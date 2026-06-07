import { ArrowLeft, CreditCard, MapPin, Truck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, FormCheckbox, FormField, FormSelect } from '../components/forms';
import { checkoutSchema, type CheckoutFormData } from '../lib/validations';
import api from '../services/api';

interface CartItem {
  product: { name: string; price: number; unit: string };
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
      const res = await api.post('/orders', {
        items: cartItems.map((item) => ({
          product_id: item.product.name,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
        store_id: 'store-1',
        delivery_method: data.deliveryMethod,
        delivery_address: data.deliveryMethod === 'delivery' ? data.address : null,
        subtotal,
        shipping_fee: shippingFee,
        total_amount: total,
        payment_method: data.paymentMethod,
        notes: data.notes,
      });
      localStorage.removeItem('cart');
      navigate('/orders');
    } catch (err) {
      alert('Dat hang that bai, vui long thu lai!');
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
          <h1 className="text-xl font-bold">Thanh toan</h1>
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
        <h1 className="text-xl font-bold">Thanh toan</h1>
      </div>

      <Form
        schema={checkoutSchema}
        defaultValues={defaultValues}
        onSubmit={handlePlaceOrder}
        className="space-y-4"
      >
        {/* Order Items */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3">San pham ({cartItems.length})</h2>
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
            <MapPin className="w-5 h-5" /> Thong tin giao hang
          </h2>
          <div className="space-y-4">
            <FormField name="fullName" label="Ho ten" placeholder="Nhap ho ten cua ban" required />
            <FormField
              name="phone"
              label="So dien thoai"
              type="tel"
              placeholder="0xxxxxxxxx"
              required
            />
            <FormField name="email" label="Email" type="email" placeholder="email@example.com" />
            <FormField
              name="address"
              label="Dia chi"
              placeholder="Nhap dia chi giao hang"
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <FormField name="city" label="Thanh pho" placeholder="TP Ho Chi Minh" required />
              <FormField name="district" label="Quan/Huyen" placeholder="Quan 1" required />
            </div>
            <FormField name="ward" label="Phuong/Xa" placeholder="Phuong Ben Nghe" required />
          </div>
        </div>

        {/* Delivery Method */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <Truck className="w-5 h-5" /> Phuong thuc giao hang
          </h2>
          <FormSelect
            name="deliveryMethod"
            label="Chon phuong thuc giao hang"
            options={[
              { value: 'standard', label: 'Giao hang tieu chuan (2-3 ngay)' },
              { value: 'express', label: 'Giao hang nhanh (1-2 ngay)' },
              { value: 'same-day', label: 'Giao hang trong ngay' },
            ]}
            required
          />
        </div>

        {/* Payment Method */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <CreditCard className="w-5 h-5" /> Phuong thuc thanh toan
          </h2>
          <FormSelect
            name="paymentMethod"
            label="Chon phuong thuc thanh toan"
            options={[
              { value: 'cod', label: 'Thanh toan khi nhan hang (COD)' },
              { value: 'momo', label: 'Vi Momo' },
              { value: 'zalopay', label: 'ZaloPay' },
              { value: 'credit_card', label: 'The tin dung/Ghi nhan' },
            ]}
            required
          />
        </div>

        {/* Notes */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <FormField
            name="notes"
            label="Ghi chu (tuy chon)"
            placeholder="Them ghi chu cho don hang..."
          />
        </div>

        {/* Terms */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <FormCheckbox
            name="agreeToTerms"
            label="Toi dong y voi dieu khoan va dieu kien cua VietStore"
            required
          />
        </div>

        {/* Summary */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <h2 className="font-semibold mb-3">Tong ket</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Tam tinh</span>
              <span>{subtotal.toLocaleString('vi-VN')}đ</span>
            </div>
            <div className="flex justify-between">
              <span>Phi giao hang</span>
              <span>
                {shippingFee === 0 ? 'Mien phi' : `${shippingFee.toLocaleString('vi-VN')}đ`}
              </span>
            </div>
            <hr />
            <div className="flex justify-between text-lg font-bold">
              <span>Tong cong</span>
              <span className="text-blue-600">{total.toLocaleString('vi-VN')}đ</span>
            </div>
          </div>
        </div>

        {/* Place Order Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? 'Dang xu ly...' : `Dat hang (${total.toLocaleString('vi-VN')}đ)`}
        </button>
      </Form>
    </div>
  );
}
