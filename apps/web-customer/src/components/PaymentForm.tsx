import { useState, useEffect, useCallback } from 'react';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import type { StripeElementChangeEvent } from '@stripe/stripe-js';
import {
  CreditCard,
  Lock,
  Check,
  AlertCircle,
  Truck,
  Wallet,
  Loader2,
  Banknote,
  ShieldCheck,
  Info,
} from 'lucide-react';
import {
  stripePromise,
  isStripeConfigured,
  createPaymentIntent,
  type CreateIntentResponse,
} from '../lib/stripe';
import { apiService } from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type PaymentMethodType = 'card' | 'momo' | 'zalopay' | 'cod';

interface PaymentMethodOption {
  id: PaymentMethodType;
  label: string;
  description: string;
  icon: React.ReactNode;
  available: boolean;
}

interface PaymentFormProps {
  amount: number;
  currency?: string;
  orderId?: string;
  onSuccess?: (paymentMethod: PaymentMethodType, intentId?: string) => void;
  onError?: (error: string) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#1f2937',
      '::placeholder': { color: '#9ca3af' },
      fontFamily:
        '"Inter", "Helvetica Neue", "Arial", sans-serif',
    },
    invalid: {
      color: '#ef4444',
      iconColor: '#ef4444',
    },
  },
  hidePostalCode: true,
};

// ---------------------------------------------------------------------------
// Inner form that uses Stripe hooks (must be inside <Elements>)
// ---------------------------------------------------------------------------

function CardPaymentForm({
  amount,
  orderId,
  clientSecret,
  paymentIntentId,
  onSuccess,
  onError,
  onBack,
}: {
  amount: number;
  orderId?: string;
  clientSecret: string;
  paymentIntentId: string;
  onSuccess: (intentId: string) => void;
  onError: (error: string) => void;
  onBack: () => void;
}) {
  const stripe = useStripe();
  const elements = useElements();

  const [processing, setProcessing] = useState(false);
  const [cardComplete, setCardComplete] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);
  const [succeeded, setSucceeded] = useState(false);

  const handleCardChange = (e: StripeElementChangeEvent) => {
    setCardComplete(e.complete);
    setCardError(e.error ? e.error.message : null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || !clientSecret) return;

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) return;

    setProcessing(true);
    setCardError(null);

    try {
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: { card: cardElement },
      });

      if (result.error) {
        // Stripe declined / validation error
        const msg =
          result.error.message || 'Thanh toán không thành công. Vui lòng thử lại.';
        setCardError(msg);
        onError(msg);
      } else if (result.paymentIntent?.status === 'succeeded') {
        setSucceeded(true);
        onSuccess(result.paymentIntent.id);
      } else {
        // Requires further action (e.g. 3DS)
        // For now poll the intent status
        const status = await apiService.get<{
          id: string;
          status: string;
        }>(`/api/payments/intent/${paymentIntentId}`);

        if (status.status === 'succeeded') {
          setSucceeded(true);
          onSuccess(status.id);
        } else if (status.status === 'requires_action') {
          setCardError(
            'Xác thực bổ sung cần thiết. Vui lòng hoàn tất xác thực 3D Secure.',
          );
          onError('3D Secure authentication required');
        } else {
          setCardError(
            `Trạng thái thanh toán: ${status.status}. Vui lòng thử lại.`,
          );
          onError(`Payment status: ${status.status}`);
        }
      }
    } catch (err: any) {
      const msg = err?.message || 'Lỗi không xác định khi xử lý thanh toán.';
      setCardError(msg);
      onError(msg);
    } finally {
      setProcessing(false);
    }
  };

  // ---- Success screen ----
  if (succeeded) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-emerald-600" />
        </div>
        <h4 className="text-lg font-semibold text-emerald-600 mb-2">
          Thanh toán thành công!
        </h4>
        <p className="text-sm text-gray-600">
          Đơn hàng của bạn đã được xác nhận.
        </p>
      </div>
    );
  }

  // ---- Card form ----
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Amount summary */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Số tiền thanh toán</span>
          <span className="text-lg font-bold text-emerald-600">
            {amount.toLocaleString('vi-VN')}₫
          </span>
        </div>
        {orderId && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Mã đơn hàng</span>
            <span className="text-sm font-medium">{orderId}</span>
          </div>
        )}
      </div>

      {/* Card input */}
      <div className="p-4 border rounded-lg bg-white">
        <div className="flex items-center gap-2 mb-3">
          <Lock className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">Thông tin thẻ</span>
        </div>
        <div className="p-3 border rounded-md bg-gray-50">
          <CardElement options={CARD_ELEMENT_OPTIONS} onChange={handleCardChange} />
        </div>
        {cardError && (
          <div className="mt-2 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-500">{cardError}</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          disabled={processing}
          className="flex-1 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          Quay lại
        </button>
        <button
          type="submit"
          disabled={processing || !stripe || !cardComplete}
          className="flex-[2] py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
        >
          {processing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Đang xử lý...
            </>
          ) : (
            <>
              <Lock className="w-4 h-4" />
              Thanh toán {amount.toLocaleString('vi-VN')}₫
            </>
          )}
        </button>
      </div>

      <div className="flex items-center justify-center gap-1 text-xs text-gray-400">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>Bảo mật bởi Stripe — chúng tôi không lưu thông tin thẻ</span>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main PaymentForm component
// ---------------------------------------------------------------------------

export function PaymentForm({
  amount,
  currency = 'vnd',
  orderId,
  onSuccess,
  onError,
}: PaymentFormProps) {
  const stripeAvailable = isStripeConfigured();

  const [selectedMethod, setSelectedMethod] = useState<PaymentMethodType>(
    stripeAvailable ? 'card' : 'cod',
  );
  const [intentData, setIntentData] = useState<CreateIntentResponse | null>(null);
  const [creatingIntent, setCreatingIntent] = useState(false);
  const [error, setError] = useState('');
  const [codSuccess, setCodSuccess] = useState(false);
  const [codProcessing, setCodProcessing] = useState(false);

  // Available payment methods
  const paymentMethods: PaymentMethodOption[] = [
    {
      id: 'card',
      label: 'Thẻ quốc tế',
      description: 'Visa, Mastercard, JCB — bảo mật bởi Stripe',
      icon: <CreditCard className="w-5 h-5" />,
      available: stripeAvailable,
    },
    {
      id: 'momo',
      label: 'MoMo',
      description: 'Ví điện tử MoMo',
      icon: <Wallet className="w-5 h-5" />,
      available: false,
    },
    {
      id: 'zalopay',
      label: 'ZaloPay',
      description: 'Ví điện tử ZaloPay',
      icon: <Wallet className="w-5 h-5" />,
      available: false,
    },
    {
      id: 'cod',
      label: 'Thanh toán khi nhận hàng',
      description: 'Trả tiền mặt khi giao hàng thành công',
      icon: <Banknote className="w-5 h-5" />,
      available: true,
    },
  ];

  // ---- Create PaymentIntent when Card is selected ----
  const createIntent = useCallback(async () => {
    if (intentData) return; // already created
    setCreatingIntent(true);
    setError('');
    try {
      const data = await createPaymentIntent(amount, currency, orderId);
      if (!data.client_secret) {
        throw new Error('Không nhận được client_secret từ máy chủ.');
      }
      setIntentData(data);
    } catch (err: any) {
      const msg =
        err?.message || 'Không thể tạo phiên thanh toán. Vui lòng thử lại.';
      setError(msg);
      onError?.(msg);
    } finally {
      setCreatingIntent(false);
    }
  }, [amount, currency, orderId, intentData, onError]);

  // When user selects Card, create intent
  useEffect(() => {
    if (selectedMethod === 'card' && !intentData && !creatingIntent) {
      createIntent();
    }
  }, [selectedMethod, intentData, creatingIntent, createIntent]);

  // ---- COD handler ----
  const handleCOD = async () => {
    setCodProcessing(true);
    setError('');
    try {
      // For COD, no Stripe intent is needed. Just confirm the order.
      // We simulate a small delay for UX and call onSuccess.
      await new Promise((r) => setTimeout(r, 800));
      setCodSuccess(true);
      onSuccess?.('cod');
    } catch (err: any) {
      const msg = err?.message || 'Đặt hàng không thành công. Vui lòng thử lại.';
      setError(msg);
      onError?.(msg);
    } finally {
      setCodProcessing(false);
    }
  };

  // ---- Card payment success ----
  const handleCardSuccess = (intentId: string) => {
    onSuccess?.('card', intentId);
  };

  // ---- Reset back to method selector from card view ----
  const handleCardBack = () => {
    setSelectedMethod(stripeAvailable ? 'card' : 'cod');
  };

  // ---- COD success screen ----
  if (codSuccess) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-emerald-600" />
          </div>
          <h4 className="text-lg font-semibold text-emerald-600 mb-2">
            Đặt hàng thành công!
          </h4>
          <p className="text-sm text-gray-600">
            Bạn sẽ thanh toán bằng tiền mặt khi nhận hàng.
          </p>
        </div>
      </div>
    );
  }

  // ---- Card payment with Stripe Elements ----
  if (selectedMethod === 'card' && stripeAvailable && intentData) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Thanh toán bằng thẻ</h3>
            <p className="text-xs text-gray-500">Bảo mật bởi Stripe</p>
          </div>
        </div>

        <Elements stripe={stripePromise} options={{ clientSecret: intentData.client_secret }}>
          <CardPaymentForm
            amount={amount}
            orderId={orderId}
            clientSecret={intentData.client_secret}
            paymentIntentId={intentData.id}
            onSuccess={handleCardSuccess}
            onError={(msg) => {
              setError(msg);
              onError?.(msg);
            }}
            onBack={handleCardBack}
          />
        </Elements>
      </div>
    );
  }

  // ---- Loading while creating intent ----
  if (selectedMethod === 'card' && creatingIntent) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border">
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
          <p className="text-sm text-gray-600">Đang chuẩn bị phiên thanh toán...</p>
        </div>
      </div>
    );
  }

  // ---- Default: Payment method selector ----
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
          <CreditCard className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">Phương thức thanh toán</h3>
          <p className="text-xs text-gray-500">Chọn hình thức thanh toán</p>
        </div>
      </div>

      {/* Amount summary */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-gray-600">Số tiền thanh toán</span>
          <span className="text-lg font-bold text-emerald-600">
            {amount.toLocaleString('vi-VN')}₫
          </span>
        </div>
        {orderId && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Mã đơn hàng</span>
            <span className="text-sm font-medium">{orderId}</span>
          </div>
        )}
      </div>

      {/* Stripe not configured notice */}
      {!stripeAvailable && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
          <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">
              Thanh toán bằng thẻ chưa khả dụng
            </p>
            <p className="text-xs text-amber-700 mt-0.5">
              Hệ thống thanh toán trực tuyến chưa được cấu hình. Vui lòng chọn
              hình thức khác hoặc liên hệ hỗ trợ.
            </p>
          </div>
        </div>
      )}

      {/* Payment method list */}
      <div className="space-y-3 mb-6">
        {paymentMethods.map((method) => {
          const isSelected = selectedMethod === method.id;
          const isDisabled = !method.available;

          return (
            <button
              key={method.id}
              onClick={() => {
                if (!isDisabled) setSelectedMethod(method.id);
              }}
              disabled={isDisabled}
              className={`
                w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all text-left
                ${isSelected
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
                ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {/* Radio indicator */}
              <div
                className={`
                  w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0
                  ${isSelected
                    ? 'border-emerald-500 bg-emerald-500'
                    : 'border-gray-300'
                  }
                `}
              >
                {isSelected && <div className="w-2 h-2 bg-white rounded-full" />}
              </div>

              {/* Icon */}
              <div
                className={`
                  w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                  ${isSelected ? 'bg-emerald-100 text-emerald-600' : 'bg-gray-100 text-gray-500'}
                `}
              >
                {method.icon}
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {method.label}
                  </span>
                  {method.id === 'card' && !isDisabled && (
                    <span className="inline-flex items-center gap-0.5 text-[10px] font-medium text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">
                      <ShieldCheck className="w-3 h-3" />
                      Stripe
                    </span>
                  )}
                  {isDisabled && method.id !== 'card' && (
                    <span className="text-[10px] font-medium text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded">
                      Sắp ra mắt
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{method.description}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Submit button */}
      <button
        onClick={() => {
          if (selectedMethod === 'cod') {
            handleCOD();
          } else if (selectedMethod === 'card') {
            // Intent creation is handled by useEffect; this button won't show
            // while intent is being created because we render a loading state.
            createIntent();
          }
        }}
        disabled={
          codProcessing ||
          (selectedMethod === 'card' && creatingIntent) ||
          !paymentMethods.find((m) => m.id === selectedMethod)?.available
        }
        className="w-full py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
      >
        {codProcessing || creatingIntent ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Đang xử lý...
          </>
        ) : selectedMethod === 'cod' ? (
          <>
            <Truck className="w-4 h-4" />
            Đặt hàng — Thanh toán khi nhận hàng
          </>
        ) : (
          <>
            <Lock className="w-4 h-4" />
            Tiếp tục thanh toán
          </>
        )}
      </button>

      <p className="text-xs text-gray-400 text-center mt-4">
        Giao dịch được bảo mật. Thông tin thanh toán của bạn luôn an toàn.
      </p>
    </div>
  );
}

export default PaymentForm;
