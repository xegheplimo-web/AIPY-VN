"""
Stripe Payment Service

Provides payment processing functionality using Stripe.
"""

import logging
from typing import Any

try:
    from stripe import StripeClient

    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

from src.config import config

logger = logging.getLogger(__name__)


class StripeService:
    """Service for Stripe payment processing."""

    def __init__(self):
        """Initialize Stripe service."""
        self.client = None
        self._initialize_stripe()

    def _initialize_stripe(self):
        """Initialize Stripe client."""
        if not STRIPE_AVAILABLE:
            logger.warning("stripe not installed, payment processing disabled")
            return

        try:
            if not config.stripe.is_configured():
                logger.warning("Stripe not configured, payment processing disabled")
                return

            self.client = StripeClient(api_key=config.stripe.secret_key)
            logger.info("Stripe initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")
            self.client = None

    def is_ready(self) -> bool:
        """Check if the service is ready."""
        return self.client is not None

    async def create_payment_intent(
        self,
        amount: int,
        currency: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a payment intent.

        Args:
            amount: Amount in cents (smallest currency unit)
            currency: Currency code (default: from config)
            metadata: Optional metadata for the payment

        Returns:
            Payment intent data or None if failed
        """
        if not self.is_ready():
            logger.warning("Stripe not ready, cannot create payment intent")
            return None

        try:
            payment_intent = self.client.payment_intents.create(
                amount=amount,
                currency=currency or config.stripe.currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )

            logger.info(f"Payment intent created: {payment_intent.id}")
            return {
                "id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status,
            }

        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None

    async def confirm_payment(
        self, payment_intent_id: str, payment_method_id: str
    ) -> dict[str, Any] | None:
        """
        Confirm a payment.

        Args:
            payment_intent_id: Payment intent ID
            payment_method_id: Payment method ID

        Returns:
            Payment intent data or None if failed
        """
        if not self.is_ready():
            logger.warning("Stripe not ready, cannot confirm payment")
            return None

        try:
            payment_intent = self.client.payment_intents.confirm(
                payment_intent_id, payment_method=payment_method_id
            )

            logger.info(f"Payment confirmed: {payment_intent.id}")
            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
            }

        except Exception as e:
            logger.error(f"Failed to confirm payment: {e}")
            return None

    async def create_customer(
        self,
        email: str,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a Stripe customer.

        Args:
            email: Customer email
            name: Customer name
            metadata: Optional metadata

        Returns:
            Customer data or None if failed
        """
        if not self.is_ready():
            logger.warning("Stripe not ready, cannot create customer")
            return None

        try:
            customer = self.client.customers.create(
                email=email, name=name, metadata=metadata or {}
            )

            logger.info(f"Customer created: {customer.id}")
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name,
            }

        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return None

    async def get_payment_intent(
        self, payment_intent_id: str
    ) -> dict[str, Any] | None:
        """
        Get payment intent details.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Payment intent data or None if failed
        """
        if not self.is_ready():
            logger.warning("Stripe not ready, cannot get payment intent")
            return None

        try:
            payment_intent = self.client.payment_intents.retrieve(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "metadata": payment_intent.metadata,
            }

        except Exception as e:
            logger.error(f"Failed to get payment intent: {e}")
            return None

    async def refund_payment(
        self, payment_intent_id: str, amount: int | None = None
    ) -> dict[str, Any] | None:
        """
        Refund a payment.

        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund in cents (None for full refund)

        Returns:
        Refund data or None if failed
        """
        if not self.is_ready():
            logger.warning("Stripe not ready, cannot refund payment")
            return None

        try:
            refund = self.client.refunds.create(
                payment_intent=payment_intent_id, amount=amount
            )

            logger.info(f"Refund created: {refund.id}")
            return {
                "id": refund.id,
                "amount": refund.amount,
                "status": refund.status,
            }

        except Exception as e:
            logger.error(f"Failed to refund payment: {e}")
            return None


# Global service instance
stripe_service = StripeService()


def get_stripe_service() -> StripeService:
    """Get the global Stripe service instance."""
    return stripe_service
