/**
 * Stripe integration utilities
 *
 * Uses @stripe/stripe-js for client-side Stripe.js loading and
 * apiService for authenticated backend API calls.
 */

import { loadStripe, type Stripe } from '@stripe/stripe-js';
import { apiService } from '../services/api';

// ---------------------------------------------------------------------------
// Stripe.js singleton
// ---------------------------------------------------------------------------

const STRIPE_PK =
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '';

/**
 * Load Stripe.js once. Returns `null` when no publishable key is configured,
 * allowing the UI to fall back to COD-only mode.
 */
export const stripePromise: Promise<Stripe | null> = STRIPE_PK
  ? loadStripe(STRIPE_PK)
  : Promise.resolve(null);

/**
 * Check whether Stripe is configured (publishable key present).
 */
export function isStripeConfigured(): boolean {
  return Boolean(STRIPE_PK);
}

// ---------------------------------------------------------------------------
// Backend API helpers — all calls go through apiService for auth & base URL
// ---------------------------------------------------------------------------

export interface CreateIntentResponse {
  id: string;
  client_secret: string;
  amount: number;
  currency: string;
  status: string;
}

export interface ConfirmIntentResponse {
  id: string;
  status: string;
  amount: number;
  currency: string;
}

export interface IntentStatusResponse {
  id: string;
  status: string;
  amount: number;
  currency: string;
  metadata: Record<string, string>;
  created: number;
}

/**
 * Create a PaymentIntent on the backend.
 * The backend returns `{ id, client_secret, amount, currency, status }`.
 */
export async function createPaymentIntent(
  amount: number,
  currency: string = 'vnd',
  orderId?: string,
): Promise<CreateIntentResponse> {
  const data = await apiService.post<CreateIntentResponse>(
    '/api/payments/create-intent',
    {
      amount,
      currency,
      order_id: orderId,
    },
  );
  return data;
}

/**
 * Confirm a PaymentIntent on the backend (server-side confirmation).
 * Used when Stripe client-side confirmation is not available.
 */
export async function confirmPaymentIntent(
  paymentIntentId: string,
  paymentMethodId: string,
): Promise<ConfirmIntentResponse> {
  const data = await apiService.post<ConfirmIntentResponse>(
    '/api/payments/confirm-intent',
    {
      payment_intent_id: paymentIntentId,
      payment_method_id: paymentMethodId,
    },
  );
  return data;
}

/**
 * Retrieve the current status of a PaymentIntent.
 */
export async function getPaymentIntentStatus(
  paymentIntentId: string,
): Promise<IntentStatusResponse> {
  const data = await apiService.get<IntentStatusResponse>(
    `/api/payments/intent/${paymentIntentId}`,
  );
  return data;
}
