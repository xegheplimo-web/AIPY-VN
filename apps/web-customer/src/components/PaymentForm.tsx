import { useState } from 'react';
import { CreditCard, Lock, Check, AlertCircle } from 'lucide-react';
import { createPaymentIntent, confirmPayment, stripePromise } from '../lib/stripe';
import { apiService } from '../services/api';

interface PaymentFormProps {
  amount: number;
  currency?: string;
  orderId?: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function PaymentForm({ amount, currency = 'usd', orderId, onSuccess, onError }: PaymentFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [paymentIntentId, setPaymentIntentId] = useState('');

  const handlePayment = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Create payment intent
      const intent = await createPaymentIntent(amount, currency, orderId);
      setPaymentIntentId(intent.payment_intent_id);

      // In a real implementation, you would use Stripe Elements here
      // For now, we'll simulate the payment confirmation
      // const stripe = await stripePromise;
      // const { error, paymentIntent } = await stripe.confirmCardPayment(
      //   intent.client_secret,
      //   {
      //     payment_method: {
      //       card: cardElement,
      //     },
      //   }
      // );

      // Simulate successful payment
      setSuccess(true);
      onSuccess?.();
      
    } catch (err: any) {
      setError(err.message || 'Payment failed');
      onError?.(err.message || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
          <CreditCard className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold">Thanh toán quốc tế</h3>
          <p className="text-sm text-gray-500">Bảo mật bởi Stripe</p>
        </div>
      </div>

      {success ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h4 className="text-lg font-semibold text-green-600 mb-2">Thanh toán thành công!</h4>
          <p className="text-sm text-gray-600">Đơn hàng của bạn đã được xác nhận.</p>
        </div>
      ) : (
        <>
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">Số tiền thanh toán</span>
              <span className="text-lg font-bold text-blue-600">
                {amount.toLocaleString('vi-VN')}đ
              </span>
            </div>
            {orderId && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Mã đơn hàng</span>
                <span className="text-sm font-medium">{orderId}</span>
              </div>
            )}
          </div>

          {/* Stripe Elements would go here */}
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center gap-2 mb-3">
              <Lock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Thông tin thẻ</span>
            </div>
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Số thẻ"
                className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="MM/YY"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
                <input
                  type="text"
                  placeholder="CVC"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <button
            onClick={handlePayment}
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Đang xử lý...
              </>
            ) : (
              <>
                <Lock className="w-4 h-4" />
                Thanh toán ngay
              </>
            )}
          </button>

          <p className="text-xs text-gray-500 text-center mt-4">
            Thanh toán được bảo mật bởi Stripe. Chúng tôi không lưu trữ thông tin thẻ của bạn.
          </p>
        </>
      )}
    </div>
  );
}
