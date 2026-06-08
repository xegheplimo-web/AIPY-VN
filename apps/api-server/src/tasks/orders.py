"""
Order Tasks

Background tasks for order processing.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from src.celery_app import celery_app
from src.database import async_session
from src.models.order import Order, OrderItem
from src.models.store import Product
from src.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shipping fee constants
# ---------------------------------------------------------------------------
BASE_SHIPPING_FEE = 15000  # 15,000 VND base fee
FREE_SHIPPING_THRESHOLD = 200000  # Free shipping for orders >= 200,000 VND
PER_KM_RATE = 3000  # 3,000 VND per km (simplified)


def _calculate_shipping_fee(subtotal: float, delivery_lat: float | None = None, delivery_lng: float | None = None) -> float:
    """
    Calculate shipping fee based on order subtotal and delivery distance.

    Args:
        subtotal: Order subtotal amount
        delivery_lat: Delivery latitude (optional)
        delivery_lng: Delivery longitude (optional)

    Returns:
        Shipping fee in VND
    """
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0.0

    # Simplified distance-based calculation
    # In production, this would use a real distance calculation API
    if delivery_lat is not None and delivery_lng is not None:
        # Assume store is at district center; use a simplified flat rate
        estimated_distance_km = 5.0  # Default estimated distance
        shipping_fee = BASE_SHIPPING_FEE + (estimated_distance_km * PER_KM_RATE)
    else:
        shipping_fee = BASE_SHIPPING_FEE

    return shipping_fee


async def _send_order_notification(user_id: str, order_id: str, notification_type: str, message: str):
    """
    Send an order notification to a user via the notification service.

    Args:
        user_id: The user ID to notify
        order_id: The related order ID
        notification_type: Type of notification (e.g. 'order_confirmed', 'order_cancelled')
        message: Notification message body
    """
    try:
        from src.services.notifications import NotificationType, NotificationPriority, notification_service

        title_map = {
            "order_confirmed": "Đơn hàng đã xác nhận",
            "order_cancelled": "Đơn hàng đã hủy",
            "order_auto_cancelled": "Đơn hàng tự động hủy",
        }

        await notification_service.create_notification(
            user_id=str(user_id),
            type=NotificationType.ORDER_UPDATED,
            title=title_map.get(notification_type, "Cập nhật đơn hàng"),
            message=message,
            priority=NotificationPriority.HIGH,
            data={"order_id": str(order_id), "notification_type": notification_type},
        )
        logger.info(f"Sent {notification_type} notification to user {user_id} for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to send {notification_type} notification to user {user_id}: {e}")


async def _trigger_refund(order_id: str, user_id: str, amount: float):
    """
    Trigger a refund for a paid order.

    Args:
        order_id: The order ID to refund
        user_id: The user ID who made the payment
        amount: The amount to refund
    """
    try:
        # In a production system, this would integrate with a payment provider
        # (e.g., Stripe, VNPay, MoMo) to process the refund.
        # For now, we log the refund intent and update the payment status.
        async with async_session() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            if order and order.payment_status == "paid":
                order.payment_status = "refunded"
                await session.commit()
                logger.info(f"Refund processed for order {order_id}, amount: {amount}")
            else:
                logger.warning(f"No refund needed for order {order_id} (payment_status: {order.payment_status if order else 'N/A'})")
    except Exception as e:
        logger.error(f"Failed to process refund for order {order_id}: {e}")


@celery_app.task(
    name="src.tasks.orders.process_order",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_order(self, order_id: str):
    """
    Process an order in the background.

    Steps:
    1. Verify order exists and is in 'pending' status
    2. Check product stock availability for all items
    3. Reserve stock (decrement from product.stock)
    4. Calculate shipping fee
    5. Update order status to 'confirmed'
    6. Send confirmation notification

    Args:
        order_id: Order ID to process

    Returns:
        True if successful
    """
    async def _process():
        async with async_session() as session:
            # Step 1: Verify order exists and is in 'pending' status
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                logger.error(f"Order {order_id} not found")
                raise ValueError(f"Order {order_id} not found")

            if order.status != "pending":
                logger.warning(f"Order {order_id} is not in pending status (current: {order.status})")
                raise ValueError(f"Order {order_id} is not in pending status (current: {order.status})")

            # Step 2: Check product stock availability for all items
            items_result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order_id)
            )
            order_items = items_result.scalars().all()

            if not order_items:
                logger.error(f"Order {order_id} has no items")
                raise ValueError(f"Order {order_id} has no items")

            insufficient_stock = []
            product_map = {}

            for item in order_items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if not product:
                    insufficient_stock.append(
                        f"Product {item.product_id} not found"
                    )
                    continue

                product_map[str(item.product_id)] = product

                if product.stock < item.quantity:
                    insufficient_stock.append(
                        f"Product '{product.name}' has insufficient stock "
                        f"(available: {product.stock}, requested: {item.quantity})"
                    )

            if insufficient_stock:
                error_msg = "; ".join(insufficient_stock)
                logger.error(f"Insufficient stock for order {order_id}: {error_msg}")
                # Mark order as failed due to stock issues
                order.status = "cancelled"
                order.confirmed_at = None
                await session.commit()

                # Notify user about stock issue
                await _send_order_notification(
                    user_id=str(order.user_id),
                    order_id=str(order_id),
                    notification_type="order_cancelled",
                    message=f"Đơn hàng của bạn đã bị hủy do không đủ hàng: {error_msg}",
                )

                raise ValueError(f"Insufficient stock for order {order_id}: {error_msg}")

            # Step 3: Reserve stock (decrement from product.stock)
            for item in order_items:
                product = product_map[str(item.product_id)]
                product.stock -= item.quantity
                logger.info(
                    f"Reserved {item.quantity} units of '{product.name}' for order {order_id}. "
                    f"Remaining stock: {product.stock}"
                )

            # Step 4: Calculate shipping fee
            subtotal = float(order.subtotal) if order.subtotal else 0.0
            delivery_lat = float(order.delivery_lat) if order.delivery_lat else None
            delivery_lng = float(order.delivery_lng) if order.delivery_lng else None
            shipping_fee = _calculate_shipping_fee(subtotal, delivery_lat, delivery_lng)

            # Step 5: Update order status to 'confirmed'
            order.status = "confirmed"
            order.shipping_fee = shipping_fee
            order.confirmed_at = datetime.now(timezone.utc).isoformat()

            # Recalculate total with shipping fee
            discount = float(order.discount) if order.discount else 0.0
            order.total_amount = subtotal + shipping_fee - discount

            await session.commit()

            logger.info(
                f"Order {order_id} confirmed. Shipping fee: {shipping_fee}, "
                f"Total: {order.total_amount}"
            )

            # Step 6: Send confirmation notification
            await _send_order_notification(
                user_id=str(order.user_id),
                order_id=str(order_id),
                notification_type="order_confirmed",
                message=f"Đơn hàng của bạn đã được xác nhận. Phí vận chuyển: {shipping_fee:,.0f}đ. "
                        f"Tổng cộng: {float(order.total_amount):,.0f}đ",
            )

            return True

    try:
        logger.info(f"Processing order {order_id}")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from an async context, create a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _process())
                return future.result()
        else:
            return loop.run_until_complete(_process())
    except Exception as e:
        logger.error(f"Failed to process order {order_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(name="src.tasks.orders.update_order_status", bind=True, max_retries=3)
def update_order_status(self, order_id: str, new_status: str):
    """
    Update order status and send notifications.

    Args:
        order_id: Order ID
        new_status: New status

    Returns:
        True if successful
    """
    async def _update():
        async with async_session() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError(f"Order {order_id} not found")

            old_status = order.status
            order.status = new_status

            if new_status == "confirmed":
                order.confirmed_at = datetime.now(timezone.utc).isoformat()
            elif new_status == "completed":
                order.completed_at = datetime.now(timezone.utc).isoformat()

            await session.commit()

            logger.info(f"Order {order_id} status updated from '{old_status}' to '{new_status}'")

            # Send notification
            notification_type = f"order_{new_status}"
            message = f"Trạng thái đơn hàng đã được cập nhật: {old_status} → {new_status}"
            await _send_order_notification(
                user_id=str(order.user_id),
                order_id=str(order_id),
                notification_type=notification_type,
                message=message,
            )

            return True

    try:
        logger.info(f"Updating order {order_id} status to {new_status}")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _update())
                return future.result()
        else:
            return loop.run_until_complete(_update())
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(name="src.tasks.orders.cancel_order", bind=True, max_retries=3)
def cancel_order(self, order_id: str, reason: str = ""):
    """
    Cancel an order and restore inventory.

    Steps:
    1. Verify order exists and is cancellable (pending/confirmed)
    2. Restore product stock
    3. If payment was made, trigger refund
    4. Update order status to 'cancelled'
    5. Send cancellation notification

    Args:
        order_id: Order ID to cancel
        reason: Cancellation reason

    Returns:
        True if successful
    """
    async def _cancel():
        async with async_session() as session:
            # Step 1: Verify order exists and is cancellable
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError(f"Order {order_id} not found")

            cancellable_statuses = {"pending", "confirmed"}
            if order.status not in cancellable_statuses:
                raise ValueError(
                    f"Order {order_id} cannot be cancelled (current status: {order.status}). "
                    f"Only orders with status {cancellable_statuses} can be cancelled."
                )

            # Step 2: Restore product stock for all items
            items_result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order_id)
            )
            order_items = items_result.scalars().all()

            for item in order_items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.stock += item.quantity
                    logger.info(
                        f"Restored {item.quantity} units of '{product.name}' from order {order_id}. "
                        f"New stock: {product.stock}"
                    )

            # Step 3: If payment was made, trigger refund
            payment_was_made = order.payment_status == "paid"
            if payment_was_made:
                total_amount = float(order.total_amount) if order.total_amount else 0.0
                await _trigger_refund(
                    order_id=str(order_id),
                    user_id=str(order.user_id),
                    amount=total_amount,
                )
                logger.info(f"Refund triggered for order {order_id}, amount: {total_amount}")

            # Step 4: Update order status to 'cancelled'
            order.status = "cancelled"
            if reason:
                # Store cancellation reason in a note-like field if available
                # Since there's no dedicated reason column, we log it
                logger.info(f"Order {order_id} cancellation reason: {reason}")

            await session.commit()

            logger.info(f"Order {order_id} cancelled successfully. Reason: {reason or 'N/A'}")

            # Step 5: Send cancellation notification
            refund_note = " Số tiền thanh toán sẽ được hoàn lại." if payment_was_made else ""
            await _send_order_notification(
                user_id=str(order.user_id),
                order_id=str(order_id),
                notification_type="order_cancelled",
                message=f"Đơn hàng của bạn đã được hủy.{refund_note}"
                        + (f" Lý do: {reason}" if reason else ""),
            )

            return True

    try:
        logger.info(f"Cancelling order {order_id}. Reason: {reason}")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _cancel())
                return future.result()
        else:
            return loop.run_until_complete(_cancel())
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(name="src.tasks.orders.check_pending_orders", bind=True)
def check_pending_orders(self):
    """
    Check for pending orders that have been pending for more than 30 minutes
    and auto-cancel them.

    This task should be scheduled to run periodically (e.g., every 5 minutes).

    Returns:
        Number of auto-cancelled orders
    """
    async def _check():
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        cancelled_count = 0

        async with async_session() as session:
            # Find orders that have been pending for > 30 minutes
            result = await session.execute(
                select(Order).where(Order.status == "pending")
            )
            pending_orders = result.scalars().all()

            for order in pending_orders:
                # Check if order has been pending for more than 30 minutes
                if order.created_at is None:
                    continue

                created_at = order.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                if created_at < cutoff_time:
                    logger.info(
                        f"Auto-cancelling order {order.id} "
                        f"(pending since {order.created_at}, exceeds 30-minute threshold)"
                    )

                    # Restore product stock
                    items_result = await session.execute(
                        select(OrderItem).where(OrderItem.order_id == order.id)
                    )
                    order_items = items_result.scalars().all()

                    for item in order_items:
                        product_result = await session.execute(
                            select(Product).where(Product.id == item.product_id)
                        )
                        product = product_result.scalar_one_or_none()
                        if product:
                            product.stock += item.quantity
                            logger.info(
                                f"Restored {item.quantity} units of '{product.name}' "
                                f"from auto-cancelled order {order.id}"
                            )

                    # Trigger refund if payment was made
                    if order.payment_status == "paid":
                        total_amount = float(order.total_amount) if order.total_amount else 0.0
                        await _trigger_refund(
                            order_id=str(order.id),
                            user_id=str(order.user_id),
                            amount=total_amount,
                        )

                    # Update order status
                    order.status = "cancelled"
                    cancelled_count += 1

                    # Send auto-cancellation notification
                    await _send_order_notification(
                        user_id=str(order.user_id),
                        order_id=str(order.id),
                        notification_type="order_auto_cancelled",
                        message="Đơn hàng của bạn đã tự động bị hủy do không được xác nhận trong vòng 30 phút.",
                    )

            await session.commit()

        logger.info(f"Auto-cancelled {cancelled_count} pending orders exceeding 30-minute threshold")
        return cancelled_count

    try:
        logger.info("Checking for stale pending orders...")
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _check())
                return future.result()
        else:
            return loop.run_until_complete(_check())
    except Exception as e:
        logger.error(f"Failed to check pending orders: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
