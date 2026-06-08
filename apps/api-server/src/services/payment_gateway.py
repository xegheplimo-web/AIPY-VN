"""
Payment gateway service with Stripe integration
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import stripe
from src.config import config

logger = logging.getLogger(__name__)


class PaymentGatewayService:
    """Service for payment gateway operations"""
    
    def __init__(self):
        self.stripe_api_key = config.stripe_api_key if hasattr(config, 'stripe_api_key') else None
        self.webhook_secret = config.stripe_webhook_secret if hasattr(config, 'stripe_webhook_secret') else None
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
        order_id: str,
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
    
    async def _handle_payment_succeeded(self, event_data: Dict[str, Any]) -> None:
        """Handle payment succeeded event"""
        payment_intent = event_data.get("data", {}).get("object", {})
        order_id = payment_intent.get("metadata", {}).get("order_id")
        
        logger.info(f"Payment succeeded for order {order_id}")
        
        # TODO: Update order status in database
        # TODO: Send confirmation email
        # TODO: Trigger fulfillment process
    
    async def _handle_payment_failed(self, event_data: Dict[str, Any]) -> None:
        """Handle payment failed event"""
        payment_intent = event_data.get("data", {}).get("object", {})
        order_id = payment_intent.get("metadata", {}).get("order_id")
        
        logger.warning(f"Payment failed for order {order_id}")
        
        # TODO: Update order status in database
        # TODO: Send payment failed notification
    
    async def _handle_refund(self, event_data: Dict[str, Any]) -> None:
        """Handle refund event"""
        charge = event_data.get("data", {}).get("object", {})
        
        logger.info(f"Refund processed for charge {charge.get('id')}")
        
        # TODO: Update order status in database
        # TODO: Send refund notification


# Global payment gateway service instance
payment_gateway_service = PaymentGatewayService()
