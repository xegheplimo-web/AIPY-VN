"""
Order Tasks

Background tasks for order processing.
"""

import logging
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="src.tasks.orders.process_order",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_order(self, order_id: str):
    """
    Process an order in the background.
    
    Args:
        order_id: Order ID to process
    
    Returns:
        True if successful
    """
    try:
        logger.info(f"Processing order {order_id}")
        
        # TODO: Implement actual order processing logic
        # - Check inventory
        # - Reserve items
        # - Calculate shipping
        # - Update order status
        
        logger.info(f"Order {order_id} processed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process order {order_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    name="src.tasks.orders.update_order_status",
    bind=True,
    max_retries=3
)
def update_order_status(self, order_id: str, new_status: str):
    """
    Update order status and send notifications.
    
    Args:
        order_id: Order ID
        new_status: New status
    
    Returns:
        True if successful
    """
    try:
        from src.db import async_session
        from src.models.order import Order
        from sqlalchemy import select, update
        
        logger.info(f"Updating order {order_id} status to {new_status}")
        
        async with async_session() as session:
            # Update order status
            await session.execute(
                update(Order)
                .where(Order.id == order_id)
                .values(status=new_status)
            )
            await session.commit()
        
        # Send notification to user
        from src.tasks.notifications import send_order_notification
        
        # Get user's FCM token
        async with async_session() as session:
            order = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            order = order.scalar_one_or_none()
            
            if order and order.user_id:
                from src.models.user import User
                user = await session.execute(
                    select(User).where(User.id == order.user_id)
                )
                user = user.scalar_one_or_none()
                
                if user and user.fcm_token:
                    send_order_notification.delay(
                        user.fcm_token,
                        order_id,
                        new_status
                    )
        
        logger.info(f"Order {order_id} status updated to {new_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    name="src.tasks.orders.cancel_order",
    bind=True,
    max_retries=3
)
def cancel_order(self, order_id: str, reason: str = ""):
    """
    Cancel an order and restore inventory.
    
    Args:
        order_id: Order ID to cancel
        reason: Cancellation reason
    
    Returns:
        True if successful
    """
    try:
        logger.info(f"Cancelling order {order_id}. Reason: {reason}")
        
        # TODO: Implement order cancellation logic
        # - Update order status to cancelled
        # - Restore inventory
        # - Send notification to user
        # - Process refund if applicable
        
        logger.info(f"Order {order_id} cancelled successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to cancel order {order_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery_app.task(
    name="src.tasks.orders.check_pending_orders",
    bind=True
)
def check_pending_orders(self):
    """
    Check for pending orders that need processing.
    
    This task should be scheduled to run periodically.
    """
    try:
        from src.db import async_session
        from src.models.order import Order
        from sqlalchemy import select
        
        logger.info("Checking for pending orders")
        
        async with async_session() as session:
            # Get pending orders
            pending_orders = await session.execute(
                select(Order).where(Order.status == "pending")
            )
            pending_orders = pending_orders.scalars().all()
            
            logger.info(f"Found {len(pending_orders)} pending orders")
            
            # Process each pending order
            for order in pending_orders:
                process_order.delay(str(order.id))
        
        return len(pending_orders)
        
    except Exception as e:
        logger.error(f"Failed to check pending orders: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
