import { ArrowLeft, Check, ChevronRight, CreditCard, MapPin, Package, Truck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { calculateShippingFee, formatShippingFee } from '../utils/shipping';

interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
  unit: string;
  images?: string[];
}

interface Store {
  id: string;
  name: string;
  address: string;
  distanceKm?: number;
  isSameDistrict?: boolean;
}

interface CartItem {
  id: string;
  product: Product;
  store: Store;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

interface StoreGroup {
  store: Store;
  items: CartItem[];
  deliveryMethod: 'pickup' | 'delivery';
  shippingFee: number;
  isFreeShipping: boolean;
  storeTotal: number;
}

type CheckoutStep = 'review' | 'delivery' | 'payment' | 'confirm';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentStep, setCurrentStep] = useState<CheckoutStep>('review');
  const [storeGroups, setStoreGroups] = useState<StoreGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [promoDiscount, setPromoDiscount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Form data
  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    district: '',
    ward: '',
    notes: '',
    paymentMethod: 'cod',
    agreeToTerms: false,
  });

  useEffect(() => {
    if (location.state) {
      setStoreGroups(location.state.storeGroups || []);
      setTotal(location.state.total || 0);
      setPromoDiscount(location.state.promoDiscount || 0);
    } else {
      // Fallback: load from localStorage
      const saved = localStorage.getItem('cart');
      if (saved) {
        const items = JSON.parse(saved);
        // Simple grouping for fallback
        const groups: StoreGroup[] = [];
        setStoreGroups(groups);
      }
    }
  }, [location.state]);

  const subtotal = storeGroups.reduce(
    (sum, group) => sum + group.items.reduce((s, item) => s + item.subtotal, 0),
    0
  );
  const totalShipping = storeGroups.reduce((sum, group) => sum + group.shippingFee, 0);
  const finalTotal = subtotal + totalShipping - promoDiscount;

  const handleNextStep = () => {
    const steps: CheckoutStep[] = ['review', 'delivery', 'payment', 'confirm'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  };

  const handlePrevStep = () => {
    const steps: CheckoutStep[] = ['review', 'delivery', 'payment', 'confirm'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  };

  const handlePlaceOrder = async () => {
    if (!formData.agreeToTerms) {
      alert('Vui lòng đồng ý điều khoản và điều kiện');
      return;
    }

    setLoading(true);
    try {
      // Create orders for each store
      const orderPromises = storeGroups.map(async (group) => {
        const orderData = {
          store_id: group.store.id,
          items: group.items.map((item) => ({
            product_id: item.product.id,
            quantity: item.quantity,
            unit_price: item.unit_price,
          })),
          delivery_method: group.deliveryMethod,
          shipping_address:
            group.deliveryMethod === 'delivery'
              ? `${formData.address}, ${formData.ward}, ${formData.district}, ${formData.city}`
              : undefined,
          shipping_fee: group.shippingFee,
          customer_name: formData.fullName,
          customer_phone: formData.phone,
          customer_email: formData.email,
          notes: formData.notes,
          payment_method: formData.paymentMethod,
        };

        return apiService.createOrder(orderData);
      });

      await Promise.all(orderPromises);
      localStorage.removeItem('cart');
      navigate('/orders');
    } catch (err) {
      alert('Đặt hàng thất bại, vui lòng thử lại!');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { id: 'review', label: 'Kiểm tra', icon: Package },
    { id: 'delivery', label: 'Nhận hàng', icon: Truck },
    { id: 'payment', label: 'Thanh toán', icon: CreditCard },
    { id: 'confirm', label: 'Xác nhận', icon: Check },
  ];

  return (
    <div className="max-w-2xl mx-auto p-4 pb-32">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold">Thanh toán</h1>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8 px-4">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isCompleted = steps.indexOf(currentStep) > index;
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isCompleted
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {isCompleted ? <Check size={20} /> : <Icon size={20} />}
                </div>
                <span
                  className={`text-xs mt-2 ${isActive ? 'text-blue-600 font-medium' : 'text-gray-500'}`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 ${isCompleted ? 'bg-green-600' : 'bg-gray-200'}`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Step 1: Review Products */}
      {currentStep === 'review' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold mb-4">Kiểm tra sản phẩm</h2>
          {storeGroups.map((group) => (
            <div
              key={group.store.id}
              className="bg-white rounded-xl shadow-sm border overflow-hidden"
            >
              <div className="p-4 bg-gray-50 border-b">
                <h3 className="font-semibold text-gray-900">{group.store.name}</h3>
                <p className="text-sm text-gray-500">{group.store.address}</p>
              </div>
              <div className="p-4 space-y-3">
                {group.items.map((item) => (
                  <div key={item.id} className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {item.product.images?.[0] && (
                        <img
                          src={item.product.images[0]}
                          alt={item.product.name}
                          className="w-12 h-12 object-cover rounded-lg"
                        />
                      )}
                      <div>
                        <p className="font-medium text-gray-900">{item.product.name}</p>
                        <p className="text-sm text-gray-500">
                          x{item.quantity} · {item.product.unit}
                        </p>
                      </div>
                    </div>
                    <p className="font-medium text-blue-600">
                      {item.subtotal.toLocaleString('vi-VN')}đ
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Step 2: Delivery Method */}
      {currentStep === 'delivery' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold mb-4">Chọn phương thức nhận hàng</h2>

          {storeGroups.map((group) => (
            <div key={group.store.id} className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Package className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{group.store.name}</h3>
                  <p className="text-sm text-gray-500">{group.store.address}</p>
                </div>
              </div>

              <div className="space-y-3">
                <label
                  className={`flex items-center justify-between p-4 border rounded-lg cursor-pointer transition ${
                    group.deliveryMethod === 'pickup'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name={`delivery-${group.store.id}`}
                      checked={group.deliveryMethod === 'pickup'}
                      onChange={() => {
                        const updated = storeGroups.map((g) =>
                          g.store.id === group.store.id
                            ? {
                                ...g,
                                deliveryMethod: 'pickup' as const,
                                shippingFee: 0,
                                isFreeShipping: true,
                                storeTotal: g.items.reduce((s, i) => s + i.subtotal, 0),
                              }
                            : g
                        );
                        setStoreGroups(updated);
                      }}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <p className="font-medium">Nhận tại cửa hàng</p>
                      <p className="text-sm text-gray-500">Miễn phí ship</p>
                    </div>
                  </div>
                  <span className="text-green-600 font-medium">0đ</span>
                </label>

                <label
                  className={`flex items-center justify-between p-4 border rounded-lg cursor-pointer transition ${
                    group.deliveryMethod === 'delivery'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name={`delivery-${group.store.id}`}
                      checked={group.deliveryMethod === 'delivery'}
                      onChange={() => {
                        const updated = storeGroups.map((g) =>
                          g.store.id === group.store.id
                            ? { ...g, deliveryMethod: 'delivery' as const }
                            : g
                        );
                        // Recalculate shipping
                        const recalculated = updated.map((g) => {
                          const subtotal = g.items.reduce((s, i) => s + i.subtotal, 0);
                          const weightKg = g.items.reduce((s, i) => s + i.quantity * 0.1, 0);
                          const distanceKm = g.store.distanceKm || 5;
                          const isSameDistrict = g.store.isSameDistrict !== false;
                          const shipping = calculateShippingFee({
                            distanceKm,
                            weightKg,
                            subtotal,
                            deliveryMethod: 'delivery',
                            isSameDistrict,
                          });
                          return {
                            ...g,
                            shippingFee: shipping.fee,
                            isFreeShipping: shipping.isFree,
                            storeTotal: subtotal + shipping.fee,
                          };
                        });
                        setStoreGroups(recalculated);
                      }}
                      className="w-4 h-4 text-blue-600"
                    />
                    <div>
                      <p className="font-medium">Giao tận nơi</p>
                      <p className="text-sm text-gray-500">Thời gian: 30-45 phút</p>
                    </div>
                  </div>
                  <span
                    className={`font-medium ${group.isFreeShipping ? 'text-green-600' : 'text-gray-900'}`}
                  >
                    {formatShippingFee(group.shippingFee, group.isFreeShipping)}
                  </span>
                </label>
              </div>
            </div>
          ))}

          {/* Delivery Address Form */}
          {storeGroups.some((g) => g.deliveryMethod === 'delivery') && (
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <MapPin className="w-5 h-5" /> Địa chỉ giao hàng
              </h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  placeholder="Họ tên"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="Số điện thoại"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Địa chỉ (số nhà, tên đường)"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="Thành phố"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    value={formData.district}
                    onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                    placeholder="Quận/Huyện"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <input
                  type="text"
                  value={formData.ward}
                  onChange={(e) => setFormData({ ...formData, ward: e.target.value })}
                  placeholder="Phường/Xã"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Payment Method */}
      {currentStep === 'payment' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold mb-4">Chọn phương thức thanh toán</h2>

          <div className="space-y-3">
            {[
              {
                id: 'cod',
                label: 'Thanh toán khi nhận hàng (COD)',
                icon: Package,
                desc: 'Tiền mặt khi nhận hàng',
              },
              { id: 'momo', label: 'Ví MoMo', icon: CreditCard, desc: 'Quét mã QR MoMo' },
              { id: 'zalopay', label: 'ZaloPay', icon: CreditCard, desc: 'Quét mã QR ZaloPay' },
              {
                id: 'credit_card',
                label: 'Thẻ tín dụng/Ghi nợ',
                icon: CreditCard,
                desc: 'Visa, Mastercard, JCB',
              },
            ].map((method) => (
              <label
                key={method.id}
                className={`flex items-center justify-between p-4 border rounded-lg cursor-pointer transition ${
                  formData.paymentMethod === method.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="radio"
                    name="paymentMethod"
                    checked={formData.paymentMethod === method.id}
                    onChange={(e) => setFormData({ ...formData, paymentMethod: e.target.value })}
                    className="w-4 h-4 text-blue-600"
                  />
                  <method.icon className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium">{method.label}</p>
                    <p className="text-sm text-gray-500">{method.desc}</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </label>
            ))}
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-4">
            <h3 className="font-semibold mb-3">Ghi chú (tùy chọn)</h3>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Thêm ghi chú cho đơn hàng..."
              rows={3}
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        </div>
      )}

      {/* Step 4: Confirm */}
      {currentStep === 'confirm' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold mb-4">Xác nhận đơn hàng</h2>

          {/* Order Summary */}
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <h3 className="font-semibold mb-3">Tóm tắt đơn hàng</h3>
            {storeGroups.map((group) => (
              <div
                key={group.store.id}
                className="mb-4 pb-4 border-b last:border-0 last:pb-0 last:mb-0"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Package className="w-4 h-4 text-blue-600" />
                  <span className="font-medium">{group.store.name}</span>
                </div>
                <div className="space-y-1 text-sm">
                  {group.items.map((item) => (
                    <div key={item.id} className="flex justify-between text-gray-600">
                      <span>
                        {item.product.name} x{item.quantity}
                      </span>
                      <span>{item.subtotal.toLocaleString('vi-VN')}đ</span>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-2 pt-2 border-t">
                  <span className="text-gray-600">
                    Phí ship (
                    {group.deliveryMethod === 'pickup' ? 'Nhận tại cửa hàng' : 'Giao tận nơi'})
                  </span>
                  <span className={group.isFreeShipping ? 'text-green-600' : 'text-gray-900'}>
                    {formatShippingFee(group.shippingFee, group.isFreeShipping)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Customer Info */}
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <h3 className="font-semibold mb-3">Thông tin nhận hàng</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Họ tên</span>
                <span className="font-medium">{formData.fullName || 'Chưa nhập'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Số điện thoại</span>
                <span className="font-medium">{formData.phone || 'Chưa nhập'}</span>
              </div>
              {storeGroups.some((g) => g.deliveryMethod === 'delivery') && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Địa chỉ</span>
                  <span className="font-medium text-right">
                    {formData.address && formData.ward && formData.district && formData.city
                      ? `${formData.address}, ${formData.ward}, ${formData.district}, ${formData.city}`
                      : 'Chưa nhập'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Payment Info */}
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <h3 className="font-semibold mb-3">Phương thức thanh toán</h3>
            <div className="flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-blue-600" />
              <span className="font-medium">
                {formData.paymentMethod === 'cod'
                  ? 'Thanh toán khi nhận hàng'
                  : formData.paymentMethod === 'momo'
                    ? 'Ví MoMo'
                    : formData.paymentMethod === 'zalopay'
                      ? 'ZaloPay'
                      : 'Thẻ tín dụng/Ghi nợ'}
              </span>
            </div>
          </div>

          {/* Total */}
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Tạm tính</span>
                <span>{subtotal.toLocaleString('vi-VN')}đ</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Phí ship</span>
                <span>{totalShipping.toLocaleString('vi-VN')}đ</span>
              </div>
              {promoDiscount > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Giảm giá</span>
                  <span>-{promoDiscount.toLocaleString('vi-VN')}đ</span>
                </div>
              )}
              <div className="flex justify-between text-lg font-bold pt-2 border-t border-blue-200">
                <span>Tổng cộng</span>
                <span className="text-blue-600">{finalTotal.toLocaleString('vi-VN')}đ</span>
              </div>
            </div>
          </div>

          {/* Terms */}
          <label className="flex items-start gap-3 p-4 bg-white rounded-xl shadow-sm border cursor-pointer">
            <input
              type="checkbox"
              checked={formData.agreeToTerms}
              onChange={(e) => setFormData({ ...formData, agreeToTerms: e.target.checked })}
              className="w-4 h-4 text-blue-600 mt-1"
            />
            <span className="text-sm text-gray-600">
              Tôi đồng ý với{' '}
              <a href="#" className="text-blue-600 hover:underline">
                điều khoản và điều kiện
              </a>{' '}
              của AI-SHOP.VN
            </span>
          </label>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4">
        <div className="max-w-2xl mx-auto flex gap-3">
          {currentStep !== 'review' && (
            <button
              onClick={handlePrevStep}
              className="flex-1 py-3 border border-gray-300 rounded-xl font-medium hover:bg-gray-50"
            >
              Quay lại
            </button>
          )}
          <button
            onClick={currentStep === 'confirm' ? handlePlaceOrder : handleNextStep}
            disabled={loading || (currentStep === 'confirm' && !formData.agreeToTerms)}
            className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Đang xử lý...' : currentStep === 'confirm' ? 'Đặt hàng' : 'Tiếp tục'}
          </button>
        </div>
      </div>
    </div>
  );
}
