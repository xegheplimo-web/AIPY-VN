import { ArrowLeft, CreditCard, MapPin, Truck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, FormCheckbox, FormField, FormSelect } from '../components/forms';
import { checkoutSchema, type CheckoutFormData } from '../lib/validations';
import { apiService } from '../services/api';

interface CartItem {
  product: { id: string; name: string; price: number; unit: string; store_id?: string };
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export default function CheckoutPage() {
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [shippingFee, setShippingFee] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [orderId, setOrderId] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('cart');
    if (saved) setCartItems(JSON.parse(saved));
  }, []);

  const subtotal = cartItems.reduce((sum, item) => sum + item.subtotal, 0);
  const total = subtotal + shippingFee;

  const handlePlaceOrder = async (data: CheckoutFormData) => {
    // If credit card payment, show payment form first
    if (data.paymentMethod === 'credit_card') {
      setShowPaymentForm(true);
      return;
    }

    setLoading(true);
    try {
      const res = await apiService.createOrder({
        store_id: cartItems[0]?.product?.store_id || 'default-store',
        items: cartItems.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
        delivery_method: data.deliveryMethod === 'delivery' ? 'delivery' : 'pickup',
        shipping_address: data.deliveryMethod === 'delivery' ? data.address : undefined,
      });
      localStorage.removeItem('cart');
      navigate('/orders');
    } catch (err) {
      alert('Đặt hàng thất bại, vui lòng thử lại!');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = () => {
    setShowPaymentForm(false);
    // Create order after successful payment
    localStorage.removeItem('cart');
    navigate('/orders');
  };

  if (showPaymentForm) {
    return (
      <div className="max-w-lg mx-auto p-4">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => setShowPaymentForm(false)}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold">Thanh toán</h1>
        </div>
        <PaymentForm
          amount={total}
          orderId={orderId}
          onSuccess={handlePaymentSuccess}
          onError={(error) => alert(error)}
        />
      </div>
    );
  }

  const defaultValues: Partial<CheckoutFormData> = {
    deliveryMethod: 'standard',
    paymentMethod: 'cod',
    agreeToTerms: false,
  };

  return (
    <div className="max-w-lg mx-auto p-4 pb-32">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold">Thanh toán</h1>
      </div>

      <Form
        schema={checkoutSchema}
        defaultValues={defaultValues}
        onSubmit={handlePlaceOrder}
        className="space-y-4"
      >
        {/* Order Items */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3">Sản phẩm ({cartItems.length})</h2>
          {cartItems.map((item, idx) => (
            <div key={idx} className="flex justify-between py-2 border-b last:border-0">
              <div>
                <p className="font-medium">{item.product.name}</p>
                <p className="text-sm text-gray-500">x{item.quantity}</p>
              </div>
              <p className="font-medium">{item.subtotal.toLocaleString('vi-VN')}đ</p>
            </div>
          ))}
        </div>

        {/* Shipping Information */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <MapPin className="w-5 h-5" /> Thông tin giao hàng
          </h2>
          <div className="space-y-4">
            <FormField name="fullName" label="Họ tên" placeholder="Nhập họ tên của bạn" required />
            <FormField
              name="phone"
              label="Số điện thoại"
              type="tel"
              placeholder="0xxxxxxxxx"
              required
            />
            <FormField name="email" label="Email" type="email" placeholder="email@example.com" />
            <FormField
              name="address"
              label="Địa chỉ"
              placeholder="Nhập địa chỉ giao hàng"
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <FormField name="city" label="Thành phố" placeholder="TP Hồ Chí Minh" required />
              <FormField name="district" label="Quận/Huyện" placeholder="Quận 1" required />
            </div>
            <FormField name="ward" label="Phường/Xã" placeholder="Phường Bến Nghé" required />
          </div>
        </div>

        {/* Delivery Method */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <Truck className="w-5 h-5" /> Phương thức giao hàng
          </h2>
          <FormSelect
            name="deliveryMethod"
            label="Chọn phương thức giao hàng"
            options={[
              { value: 'pickup', label: 'Nhận tại cửa hàng' },
              { value: 'delivery', label: 'Giao tận nơi' },
            ]}
            required
          />
        </div>

        {/* Payment Method */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <CreditCard className="w-5 h-5" /> Phương thức thanh toán
          </h2>
          <FormSelect
            name="paymentMethod"
            label="Chọn phương thức thanh toán"
            options={[
              { value: 'cod', label: 'Thanh toán khi nhận hàng (COD)' },
              { value: 'momo', label: 'Ví Momo' },
              { value: 'zalopay', label: 'ZaloPay' },
              { value: 'credit_card', label: 'Thẻ tín dụng/Ghi nợ' },
            ]}
            required
          />
        </div>

        {/* Notes */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <FormField
            name="notes"
            label="Ghi chú (tùy chọn)"
            placeholder="Thêm ghi chú cho đơn hàng..."
          />
        </div>

        {/* Terms */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <FormCheckbox
            name="agreeToTerms"
            label="Tôi đồng ý với điều khoản và điều kiện của AI-SHOP.VN"
            required
          />
        </div>

        {/* Summary */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3">Tổng kết</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Tạm tính</span>
              <span>{subtotal.toLocaleString('vi-VN')}đ</span>
            </div>
            <div className="flex justify-between">
              <span>Phí giao hàng</span>
              <span>
                {shippingFee === 0 ? 'Miễn phí' : `${shippingFee.toLocaleString('vi-VN')}đ`}
              </span>
            </div>
            <hr />
            <div className="flex justify-between text-lg font-bold">
              <span>Tổng cộng</span>
              <span className="text-blue-600">{total.toLocaleString('vi-VN')}đ</span>
            </div>
          </div>
        </div>

        {/* Place Order Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? 'Đang xử lý...' : 'Đặt hàng'}
        </button>
      </Form>
    </div>
  );
}

// Temporary placeholder for PaymentForm component
function PaymentForm({ amount, orderId, onSuccess, onError }: any) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <p className="text-center text-gray-500">Form thanh toán sẽ được thêm sau</p>
      <button
        onClick={onSuccess}
        className="w-full mt-4 py-3 bg-green-600 text-white rounded-lg font-semibold"
      >
        Mô phỏng thanh toán thành công
      </button>
    </div>
  );
}
