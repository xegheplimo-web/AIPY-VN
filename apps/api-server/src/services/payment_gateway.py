"""
Payment gateway service with Stripe integration.

Handles Stripe webhook events by updating order status in the database
and dispatching email / notification side-effects.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

import stripe
from sqlalchemy import select, update

from src.config import config
from src.database import async_session
from src.models.order import Order
from src.models.user import User
from src.tasks.email import send_order_confirmation

logger = logging.getLogger(__name__)


class PaymentGatewayService:
    """Service for payment gateway operations"""

    def __init__(self):
        self.stripe_api_key = config.stripe.secret_key if hasattr(config, "stripe") else None
        self.webhook_secret = config.stripe.webhook_secret if hasattr(config, "stripe") else None
        self.enabled = bool(self.stripe_api_key)

        if self.enabled:
            stripe.api_key = self.stripe_api_key
            logger.info("Stripe payment gateway initialized")
        else:
            logger.warning("Stripe payment gateway disabled (no API key)")

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "vnd",
        order_id: str = "",
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent

        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Currency code (default: VND)
            order_id: Order ID for metadata
            customer_email: Customer email
            metadata: Additional metadata

        Returns:
            Payment intent data
        """
        if not self.enabled:
            raise Exception("Payment gateway is not enabled")

        try:
            # Convert amount to smallest unit (VND uses whole numbers)
            amount_in_smallest_unit = int(amount)

            # Prepare metadata
            payment_metadata = {
                "order_id": order_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            if metadata:
                payment_metadata.update(metadata)

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_in_smallest_unit,
                currency=currency,
                metadata=payment_metadata,
                description=f"Order {order_id}",
            )

            logger.info(f"Created payment intent for order {order_id}: {intent.id}")

            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
                "metadata": intent.metadata,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: str,
    ) -> Dict[str, Any]:
        """
        Confirm a payment intent

        Args:
            payment_intent_id: Payment intent ID
            payment_method_id: Payment method ID

        Returns:
            Confirmed payment intent data
        """
        if not self.enabled:
            raise Exception("Payment gateway is not enabled")

        try:
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id,
            )

            logger.info(f"Confirmed payment intent {payment_intent_id}")

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment intent: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    async def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment intent

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent data
        """
        if not self.enabled:
            raise Exception("Payment gateway is not enabled")

        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "currency": intent.currency,
                "metadata": intent.metadata,
                "created": intent.created,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment intent: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a refund

        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund (in smallest currency unit)
            reason: Refund reason

        Returns:
            Refund data
        """
        if not self.enabled:
            raise Exception("Payment gateway is not enabled")

        try:
            # Get payment intent to find charge
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if not intent.charges:
                raise Exception("No charges found for this payment intent")

            charge_id = intent.charges.data[0].id

            # Create refund
            refund_params = {
                "charge": charge_id,
            }

            if amount:
                refund_params["amount"] = int(amount)

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Created refund for payment intent {payment_intent_id}: {refund.id}")

            return {
                "id": refund.id,
                "amount": refund.amount,
                "status": refund.status,
                "charge_id": charge_id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer

        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone
            metadata: Additional metadata

        Returns:
            Customer data
        """
        if not self.enabled:
            raise Exception("Payment gateway is not enabled")

        try:
            customer_params = {
                "email": email,
            }

            if name:
                customer_params["name"] = name

            if phone:
                customer_params["phone"] = phone

            if metadata:
                customer_params["metadata"] = metadata

            customer = stripe.Customer.create(**customer_params)

            logger.info(f"Created Stripe customer: {customer.id}")

            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "phone": customer.phone,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise Exception(f"Payment gateway error: {str(e)}")

    async def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str,
    ) -> bool:
        """
        Verify Stripe webhook signature

        Args:
            payload: Webhook payload
            sig_header: Stripe signature header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.enabled or not self.webhook_secret:
            logger.warning("Webhook signature verification disabled")
            return False

        try:
            stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return True
        except ValueError:
            logger.warning("Invalid webhook signature")
            return False
        except stripe.error.StripeError as e:
            logger.error(f"Stripe webhook error: {e}")
            return False

    # ------------------------------------------------------------------
    # Webhook event handlers
    # ------------------------------------------------------------------

    async def handle_webhook_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle Stripe webhook event

        Args:
            event_type: Event type (e.g., payment_intent.succeeded)
            event_data: Event data
        """
        logger.info(f"Handling webhook event: {event_type}")

        # Handle different event types
        if event_type == "payment_intent.succeeded":
            await self._handle_payment_succeeded(event_data)
        elif event_type == "payment_intent.payment_failed":
            await self._handle_payment_failed(event_data)
        elif event_type == "charge.refunded":
            await self._handle_refund(event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")

    async def _get_order_by_id(self, order_id: str) -> Optional[Order]:
        """
        Look up an order by its primary-key UUID.

        Args:
            order_id: Order UUID string

        Returns:
            Order instance or None
        """
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(Order).where(Order.id == uuid.UUID(order_id))
                )
                return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(f"Error looking up order {order_id}: {exc}")
            return None

    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """
        Look up a user's email by their UUID.

        Args:
            user_id: User UUID string

        Returns:
            Email address or None
        """
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(User.email).where(User.id == uuid.UUID(user_id))
                )
                row = result.scalar_one_or_none()
                return row
        except Exception as exc:
            logger.error(f"Error looking up user email for {user_id}: {exc}")
            return None

    async def _update_order_status(
        self,
        order_id: str,
        payment_status: str,
        order_status: Optional[str] = None,
    ) -> bool:
        """
        Update order payment_status (and optionally status) in the database.

        Args:
            order_id: Order UUID string
            payment_status: New payment_status value
            order_status: New status value (optional)

        Returns:
            True if the update succeeded, False otherwise
        """
        try:
            async with async_session() as session:
                values: Dict[str, Any] = {"payment_status": payment_status}
                if order_status is not None:
                    values["status"] = order_status

                stmt = (
                    update(Order)
                    .where(Order.id == uuid.UUID(order_id))
                    .values(**values)
                )
                await session.execute(stmt)
                await session.commit()
                logger.info(
                    f"Updated order {order_id}: payment_status={payment_status}"
                    + (f", status={order_status}" if order_status else "")
                )
                return True
        except Exception as exc:
            logger.error(f"Error updating order {order_id}: {exc}")
            return False

    async def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> None:
        """
        Handle payment succeeded event.

        Updates the order status to 'paid' and dispatches a confirmation
        email to the customer.
        """
        payment_intent = event_data.get("object", event_data.get("data", {}).get("object", {}))
        order_id = payment_intent.get("metadata", {}).get("order_id")
        user_id = payment_intent.get("metadata", {}).get("user_id")
        amount = payment_intent.get("amount", 0)

        logger.info(f"Payment succeeded for order {order_id}")

        if not order_id:
            logger.warning("Payment succeeded but no order_id in metadata – skipping DB update")
            return

        # Update order status in database
        updated = await self._update_order_status(
            order_id=order_id,
            payment_status="paid",
            order_status="confirmed",
        )

        if not updated:
            logger.error(f"Failed to update order {order_id} to paid status")
            return

        # Send confirmation email
        if user_id:
            user_email = await self._get_user_email(user_id)
            if user_email:
                try:
                    total = amount / 100 if amount else 0
                    send_order_confirmation.delay(user_email, str(order_id), total)
                    logger.info(f"Dispatched order confirmation email to {user_email}")
                except Exception as exc:
                    logger.error(f"Failed to dispatch confirmation email for order {order_id}: {exc}")
            else:
                logger.warning(f"Could not find email for user {user_id} – skipping confirmation email")

    async def _handle_payment_failed(self, event_data: Dict[str, Any]) -> None:
        """
        Handle payment failed event.

        Updates the order status to 'payment_failed' and notifies the user.
        """
        payment_intent = event_data.get("object", event_data.get("data", {}).get("object", {}))
        order_id = payment_intent.get("metadata", {}).get("order_id")
        user_id = payment_intent.get("metadata", {}).get("user_id")
        error_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")

        logger.warning(f"Payment failed for order {order_id}: {error_message}")

        if not order_id:
            logger.warning("Payment failed but no order_id in metadata – skipping DB update")
            return

        # Update order status in database
        updated = await self._update_order_status(
            order_id=order_id,
            payment_status="payment_failed",
            order_status="payment_failed",
        )

        if not updated:
            logger.error(f"Failed to update order {order_id} to payment_failed status")
            return

        # Notify user about failed payment
        if user_id:
            try:
                from src.services.notifications import notification_service, NotificationType, NotificationPriority
                await notification_service.create_notification(
                    user_id=user_id,
                    type=NotificationType.PAYMENT_RECEIVED,
                    title="Thanh toán thất bại",
                    message=f"Thanh toán cho đơn hàng #{order_id} đã thất bại. Lý do: {error_message}. Vui lòng thử lại.",
                    priority=NotificationPriority.HIGH,
                    data={"order_id": order_id, "error": error_message},
                )
                logger.info(f"Sent payment failure notification to user {user_id}")
            except Exception as exc:
                logger.error(f"Failed to send payment failure notification for order {order_id}: {exc}")

    async def _handle_refund(self, event_data: Dict[str, Any]) -> None:
        """
        Handle refund event.

        Updates the order status to 'refunded' and notifies the user.
        """
        charge = event_data.get("object", event_data.get("data", {}).get("object", {}))
        payment_intent_id = charge.get("payment_intent")
        refund_amount = charge.get("amount_refunded", 0)

        logger.info(f"Refund processed for charge {charge.get('id')}, payment_intent={payment_intent_id}")

        if not payment_intent_id:
            logger.warning("Refund event missing payment_intent – cannot locate order")
            return

        # Look up the order by payment intent metadata
        order_id = None
        user_id = None
        try:
            if self.enabled:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                order_id = intent.metadata.get("order_id")
                user_id = intent.metadata.get("user_id")
        except Exception as exc:
            logger.error(f"Error retrieving payment intent {payment_intent_id}: {exc}")

        if not order_id:
            logger.warning(f"Refund for payment_intent {payment_intent_id} has no order_id in metadata")
            return

        # Update order status in database
        updated = await self._update_order_status(
            order_id=order_id,
            payment_status="refunded",
            order_status="refunded",
        )

        if not updated:
            logger.error(f"Failed to update order {order_id} to refunded status")
            return

        # Notify user about refund
        if user_id:
            try:
                from src.services.notifications import notification_service, NotificationType, NotificationPriority
                total = refund_amount / 100 if refund_amount else 0
                await notification_service.create_notification(
                    user_id=user_id,
                    type=NotificationType.PAYMENT_RECEIVED,
                    title="Hoàn tiền thành công",
                    message=f"Hoàn tiền {total:,.0f} VNĐ cho đơn hàng #{order_id} đã được xử lý.",
                    priority=NotificationPriority.MEDIUM,
                    data={"order_id": order_id, "refund_amount": refund_amount},
                )
                logger.info(f"Sent refund notification to user {user_id}")
            except Exception as exc:
                logger.error(f"Failed to send refund notification for order {order_id}: {exc}")


# Global payment gateway service instance
payment_gateway_service = PaymentGatewayService()
