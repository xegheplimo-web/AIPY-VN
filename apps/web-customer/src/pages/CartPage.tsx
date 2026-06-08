import { ArrowLeft, Check, MapPin, Minus, Plus, ShoppingBag, Store, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
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

export default function CartPage() {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deliveryMethods, setDeliveryMethods] = useState<Record<string, 'pickup' | 'delivery'>>({});
  const [promoCode, setPromoCode] = useState('');
  const [promoApplied, setPromoApplied] = useState(false);
  const [promoDiscount, setPromoDiscount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    try {
      const res: any = await apiService.getCart();
      const items: CartItem[] = res.items || [];
      setCartItems(items);

      const methods: Record<string, 'pickup' | 'delivery'> = {};
      items.forEach((item: CartItem) => {
        if (!methods[item.store.id]) {
          methods[item.store.id] = 'delivery';
        }
      });
      setDeliveryMethods(methods);
    } catch (err) {
      console.error('Failed to load cart from server:', err);
      // Fallback: load from localStorage
      const saved = localStorage.getItem('cart');
      if (saved) {
        try {
          const items = JSON.parse(saved);
          // Normalize local items to CartItem shape
          const normalized: CartItem[] = items.map((item: any) => ({
            id: item.id || `local-${item.product_id}-${Date.now()}`,
            product: {
              id: item.product_id || item.product?.id || '',
              name: item.product?.name || item.name || '',
              price: item.product?.price || item.price || 0,
              stock: item.product?.stock || item.stock || 999,
              unit: item.product?.unit || item.unit || 'cái',
              images: item.product?.images || item.images || [],
            },
            store: {
              id: item.store_id || item.store?.id || 'unknown',
              name: item.store_name || item.store?.name || 'Cửa hàng',
              address: item.store?.address || '',
              distanceKm: item.store?.distanceKm || 0,
              isSameDistrict: item.store?.isSameDistrict ?? true,
            },
            quantity: item.quantity || 1,
            unit_price: item.unit_price || item.price || 0,
            subtotal: (item.unit_price || item.price || 0) * (item.quantity || 1),
          }));
          setCartItems(normalized);

          const methods: Record<string, 'pickup' | 'delivery'> = {};
          normalized.forEach((item) => {
            if (!methods[item.store.id]) {
              methods[item.store.id] = 'delivery';
            }
          });
          setDeliveryMethods(methods);
        } catch (e) {
          console.error('Failed to parse local cart:', e);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, newQty: number) => {
    if (newQty < 1) return;
    try {
      await apiService.updateCartItem(itemId, newQty);
      loadCart();
    } catch (err) {
      console.error('Failed to update quantity on server:', err);
      setCartItems((prev) =>
        prev.map((item) =>
          item.id === itemId
            ? { ...item, quantity: newQty, subtotal: item.unit_price * newQty }
            : item
        )
      );
      // Sync localStorage
      const local = JSON.parse(localStorage.getItem('cart') || '[]');
      const updatedLocal = local.map((item: any) =>
        (item.id === itemId || item.product_id === itemId)
          ? { ...item, quantity: newQty, subtotal: (item.unit_price || item.price) * newQty }
          : item
      );
      localStorage.setItem('cart', JSON.stringify(updatedLocal));
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      await apiService.removeFromCart(itemId);
      loadCart();
    } catch (err) {
      console.error('Failed to remove item on server:', err);
      setCartItems((prev) => prev.filter((item) => item.id !== itemId));
      const local = JSON.parse(localStorage.getItem('cart') || '[]').filter(
        (item: any) => item.id !== itemId && item.product_id !== itemId
      );
      localStorage.setItem('cart', JSON.stringify(local));
    }
  };

  const updateDeliveryMethod = (storeId: string, method: 'pickup' | 'delivery') => {
    setDeliveryMethods((prev) => ({ ...prev, [storeId]: method }));
  };

  const applyPromoCode = () => {
    if (promoCode === 'GIAM50K') {
      setPromoApplied(true);
      setPromoDiscount(50000);
    } else if (promoCode === 'GIAM100K') {
      setPromoApplied(true);
      setPromoDiscount(100000);
    } else {
      alert('Mã giảm giá không hợp lệ');
    }
  };

  // Group items by store
  const storeGroups: StoreGroup[] = Object.values(
    cartItems.reduce(
      (groups, item) => {
        const storeId = item.store.id;
        if (!groups[storeId]) {
          groups[storeId] = {
            store: item.store,
            items: [],
            deliveryMethod: deliveryMethods[storeId] || 'delivery',
            shippingFee: 0,
            isFreeShipping: false,
            storeTotal: 0,
          };
        }
        groups[storeId].items.push(item);
        return groups;
      },
      {} as Record<string, StoreGroup>
    )
  ).map((group) => {
    const subtotal = group.items.reduce((sum, item) => sum + item.subtotal, 0);
    const weightKg = group.items.reduce((sum, item) => sum + item.quantity * 0.1, 0); // Assume 0.1kg per item
    const distanceKm = group.store.distanceKm || 5;
    const isSameDistrict = group.store.isSameDistrict !== false;

    const shipping = calculateShippingFee({
      distanceKm,
      weightKg,
      subtotal,
      deliveryMethod: deliveryMethods[group.store.id] || 'delivery',
      isSameDistrict,
    });

    return {
      ...group,
      deliveryMethod: deliveryMethods[group.store.id] || 'delivery',
      shippingFee: shipping.fee,
      isFreeShipping: shipping.isFree,
      storeTotal: subtotal + shipping.fee,
    };
  });

  const subtotal = cartItems.reduce((sum, item) => sum + item.subtotal, 0);
  const totalShipping = storeGroups.reduce((sum, group) => sum + group.shippingFee, 0);
  const total = subtotal + totalShipping - promoDiscount;

  // Check stock availability
  const outOfStockItems = cartItems.filter((item) => item.quantity > item.product.stock);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <ShoppingBag className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">Giỏ hàng trống</h2>
        <p className="text-gray-500 mt-2">Hãy thêm sản phẩm vào giỏ hàng nhé!</p>
        <Link
          to="/"
          className="mt-6 inline-block px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
        >
          Tiếp tục mua sắm
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 pb-32">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold">Giỏ hàng ({cartItems.length})</h1>
      </div>

      {/* Out of stock warning */}
      {outOfStockItems.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-3">
            <X className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Một số sản phẩm đã hết hàng</p>
              <p className="text-sm text-red-700 mt-1">
                {outOfStockItems.map((item) => item.product.name).join(', ')}
              </p>
              <p className="text-sm text-red-600 mt-2">
                Vui lòng giảm số lượng hoặc xóa sản phẩm này.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Store Groups */}
      <div className="space-y-6">
        {storeGroups.map((group) => (
          <div
            key={group.store.id}
            className="bg-white rounded-xl shadow-sm border overflow-hidden"
          >
            {/* Store Header */}
            <div className="p-4 bg-gray-50 border-b">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Store className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{group.store.name}</h3>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <MapPin size={14} /> {group.store.address}
                  </p>
                </div>
                {group.store.distanceKm && (
                  <span className="text-sm text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                    {group.store.distanceKm < 1
                      ? `${Math.round(group.store.distanceKm * 1000)}m`
                      : `${group.store.distanceKm.toFixed(1)}km`}
                  </span>
                )}
              </div>

              {/* Delivery Method Selection */}
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => updateDeliveryMethod(group.store.id, 'pickup')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition ${
                    group.deliveryMethod === 'pickup'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Check size={16} className="inline mr-1" />
                  Nhận tại cửa hàng
                </button>
                <button
                  onClick={() => updateDeliveryMethod(group.store.id, 'delivery')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition ${
                    group.deliveryMethod === 'delivery'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <MapPin size={16} className="inline mr-1" />
                  Giao tận nơi
                </button>
              </div>
            </div>

            {/* Store Items */}
            <div className="p-4 space-y-4">
              {group.items.map((item) => (
                <div key={item.id} className="flex gap-4">
                  <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    {item.product.images?.[0] ? (
                      <img
                        src={item.product.images[0]}
                        alt={item.product.name}
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <span className="text-2xl">📦</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{item.product.name}</h3>
                    <p className="text-sm text-gray-500">{item.product.unit}</p>
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-blue-600 font-bold">
                        {item.unit_price.toLocaleString('vi-VN')}đ
                      </p>
                      {item.quantity > item.product.stock && (
                        <span className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded-full">
                          Chỉ còn {item.product.stock}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-lg hover:bg-gray-200"
                        aria-label="Giảm số lượng"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                      <span className="w-8 text-center font-medium">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded-lg hover:bg-gray-200"
                        aria-label="Tăng số lượng"
                        disabled={item.quantity >= item.product.stock}
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="ml-auto p-2 text-red-500 hover:text-red-700"
                        aria-label="Xóa sản phẩm khỏi giỏ hàng"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Store Summary */}
            <div className="p-4 bg-gray-50 border-t">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Tạm tính cửa hàng</span>
                <span className="font-medium">
                  {group.items
                    .reduce((sum, item) => sum + item.subtotal, 0)
                    .toLocaleString('vi-VN')}
                  đ
                </span>
              </div>
              <div className="flex justify-between items-center text-sm mt-2">
                <span className="text-gray-600">Phí ship</span>
                <span
                  className={`font-medium ${group.isFreeShipping ? 'text-green-600' : 'text-gray-900'}`}
                >
                  {formatShippingFee(group.shippingFee, group.isFreeShipping)}
                </span>
              </div>
              <div className="flex justify-between items-center font-semibold mt-2 pt-2 border-t border-gray-200">
                <span>Tổng cửa hàng</span>
                <span className="text-blue-600">{group.storeTotal.toLocaleString('vi-VN')}đ</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Promo Code */}
      <div className="mt-6 bg-white rounded-xl shadow-sm border p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value)}
            placeholder="Nhập mã giảm giá"
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={applyPromoCode}
            disabled={promoApplied}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Áp dụng
          </button>
        </div>
        {promoApplied && (
          <div className="mt-2 text-sm text-green-600 flex items-center gap-1">
            <Check size={16} /> Đã áp dụng mã giảm giá: -{promoDiscount.toLocaleString('vi-VN')}đ
          </div>
        )}
      </div>

      {/* Total Summary */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4">
        <div className="max-w-2xl mx-auto">
          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Tạm tính</span>
              <span>{subtotal.toLocaleString('vi-VN')}đ</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Phí ship</span>
              <span>{totalShipping.toLocaleString('vi-VN')}đ</span>
            </div>
            {promoApplied && (
              <div className="flex justify-between text-sm text-green-600">
                <span>Giảm giá</span>
                <span>-{promoDiscount.toLocaleString('vi-VN')}đ</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-lg pt-2 border-t">
              <span>Tổng cộng</span>
              <span className="text-blue-600">{total.toLocaleString('vi-VN')}đ</span>
            </div>
          </div>
          <button
            onClick={() => navigate('/checkout', { state: { storeGroups, total, promoDiscount } })}
            disabled={outOfStockItems.length > 0}
            className="w-full py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Thanh toán
          </button>
        </div>
      </div>
    </div>
  );
}
