import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');

export async function createPaymentIntent(amount: number, currency: string = 'usd', orderId?: string) {
  try {
    const response = await fetch('/api/payments/create-intent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        amount,
        currency,
        order_id: orderId,
      }),
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || 'Failed to create payment intent');
    }

    return data;
  } catch (error) {
    console.error('Error creating payment intent:', error);
    throw error;
  }
}

export async function confirmPayment(paymentIntentId: string, paymentMethodId: string) {
  try {
    const response = await fetch('/api/payments/confirm', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        payment_intent_id: paymentIntentId,
        payment_method_id: paymentMethodId,
      }),
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || 'Failed to confirm payment');
    }

    return data;
  } catch (error) {
    console.error('Error confirming payment:', error);
    throw error;
  }
}

export async function getPaymentIntent(paymentIntentId: string) {
  try {
    const response = await fetch(`/api/payments/intent/${paymentIntentId}`);
    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || 'Failed to get payment intent');
    }

    return data.data;
  } catch (error) {
    console.error('Error getting payment intent:', error);
    throw error;
  }
}

export { stripePromise };
