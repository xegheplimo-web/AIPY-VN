import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Truck, CreditCard, Check } from 'lucide-react';
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
  const [deliveryMethod, setDeliveryMethod] = useState<'pickup' | 'delivery'>('pickup');
  const [address, setAddress] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [shippingFee, setShippingFee] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('cart');
    if (saved) setCartItems(JSON.parse(saved));
  }, []);

  useEffect(() => {
    if (deliveryMethod === 'delivery' && cartItems.length > 0) {
      api.post('/shipping/calculate', {
        distance_km: 3,
        weight_grams: 500,
        order_value: subtotal,
        delivery_method: 'standard',
      }).then(res => setShippingFee(res.data.total)).catch(() => setShippingFee(25000));
    } else {
      setShippingFee(0);
    }
  }, [deliveryMethod, cartItems]);

  const subtotal = cartItems.reduce((sum, item) => sum + item.subtotal, 0);
  const total = subtotal + shippingFee;

  const handlePlaceOrder = async () => {
    setLoading(true);
    try {
      const res = await api.post('/orders', {
        items: cartItems.map(item => ({
          product_id: item.product.name,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
        store_id: 'store-1',
        delivery_method: deliveryMethod,
        delivery_address: deliveryMethod === 'delivery' ? address : null,
        subtotal,
        shipping_fee: shippingFee,
        total_amount: total,
        payment_method: paymentMethod,
      });
      localStorage.removeItem('cart');
      navigate('/orders');
    } catch (err) {
      alert('Dat hang that bai, vui long thu lai!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-4 pb-32">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold">Thanh toan</h1>
      </div>

      {/* Order Items */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
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

      {/* Delivery Method */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <Truck className="w-5 h-5" /> Phuong thuc nhan hang
        </h2>
        <div className="space-y-2">
          <label className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer ${deliveryMethod === 'pickup' ? 'border-blue-500 bg-blue-50' : ''}`}>
            <input type="radio" name="delivery" checked={deliveryMethod === 'pickup'} onChange={() => setDeliveryMethod('pickup')} />
            <div className="flex-1">
              <p className="font-medium">Nhan tai cua hang</p>
              <p className="text-sm text-gray-500">Mien phi</p>
            </div>
          </label>
          <label className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer ${deliveryMethod === 'delivery' ? 'border-blue-500 bg-blue-50' : ''}`}>
            <input type="radio" name="delivery" checked={deliveryMethod === 'delivery'} onChange={() => setDeliveryMethod('delivery')} />
            <div className="flex-1">
              <p className="font-medium">Giao hang tan noi</p>
              <p className="text-sm text-gray-500">{shippingFee > 0 ? `${shippingFee.toLocaleString('vi-VN')}đ` : 'Mien phi'}</p>
            </div>
          </label>
        </div>
        {deliveryMethod === 'delivery' && (
          <div className="mt-3">
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Nhap dia chi giao hang..."
              className="w-full p-3 border rounded-lg resize-none"
              rows={3}
            />
          </div>
        )}
      </div>

      {/* Payment */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <CreditCard className="w-5 h-5" /> Thanh toan
        </h2>
        <div className="space-y-2">
          {[
            { id: 'cod', label: 'Thanh toan khi nhan hang (COD)', icon: '💵' },
            { id: 'momo', label: 'Vi Momo', icon: '📱' },
            { id: 'zalopay', label: 'ZaloPay', icon: '💚' },
          ].map((method) => (
            <label key={method.id} className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer ${paymentMethod === method.id ? 'border-blue-500 bg-blue-50' : ''}`}>
              <input type="radio" name="payment" checked={paymentMethod === method.id} onChange={() => setPaymentMethod(method.id)} />
              <span className="text-xl">{method.icon}</span>
              <span className="flex-1 font-medium">{method.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="bg-white rounded-xl p-4 shadow-sm mb-4">
        <h2 className="font-semibold mb-3">Tong ket</h2>
        <div className="space-y-2">
          <div className="flex justify-between"><span>Tam tinh</span><span>{subtotal.toLocaleString('vi-VN')}đ</span></div>
          <div className="flex justify-between"><span>Phi giao hang</span><span>{shippingFee === 0 ? 'Mien phi' : `${shippingFee.toLocaleString('vi-VN')}đ`}</span></div>
          <hr />
          <div className="flex justify-between text-lg font-bold">
            <span>Tong cong</span>
            <span className="text-blue-600">{total.toLocaleString('vi-VN')}đ</span>
          </div>
        </div>
      </div>

      {/* Place Order Button */}
      <button
        onClick={handlePlaceOrder}
        disabled={loading || (deliveryMethod === 'delivery' && !address)}
        className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Dang xu ly...' : `Dat hang (${total.toLocaleString('vi-VN')}đ)`}
      </button>
    </div>
  );
}
