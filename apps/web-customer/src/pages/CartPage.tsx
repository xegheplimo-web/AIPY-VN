import { ArrowLeft, Minus, Plus, ShoppingBag, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface CartItem {
  id: string;
  product: {
    id: string;
    name: string;
    price: number;
    stock: number;
    unit: string;
    images?: string[];
  };
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export default function CartPage() {
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    try {
      const res = await apiService.get('/cart/');
      setCartItems(res.data.items || []);
    } catch (err) {
      // Fallback: load from localStorage
      const saved = localStorage.getItem('cart');
      if (saved) setCartItems(JSON.parse(saved));
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, newQty: number) => {
    if (newQty < 1) return;
    try {
      await apiService.put(`/cart/items/${itemId}`, { quantity: newQty });
      loadCart();
    } catch (err) {
      // Update local state
      setCartItems((prev) =>
        prev.map((item) =>
          item.id === itemId
            ? { ...item, quantity: newQty, subtotal: item.unit_price * newQty }
            : item
        )
      );
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      await apiService.delete(`/cart/items/${itemId}`);
      loadCart();
    } catch (err) {
      setCartItems((prev) => prev.filter((item) => item.id !== itemId));
    }
  };

  const total = cartItems.reduce((sum, item) => sum + item.subtotal, 0);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <ShoppingBag className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">Giờ hang trong</h2>
        <p className="text-gray-500 mt-2">Hay them san pham vao gio hang nhe!</p>
        <Link
          to="/"
          className="mt-6 inline-block px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
        >
          Tiep tuc mua sam
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto p-4 pb-24">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-bold">Giờ hang ({cartItems.length})</h1>
      </div>

      <div className="space-y-4">
        {cartItems.map((item) => (
          <div key={item.id} className="flex gap-4 p-4 bg-white rounded-xl shadow-sm border">
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
              <p className="text-blue-600 font-bold mt-1">
                {item.unit_price.toLocaleString('vi-VN')}đ
              </p>
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

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4">
        <div className="max-w-lg mx-auto flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">Tong cong</p>
            <p className="text-xl font-bold text-blue-600">{total.toLocaleString('vi-VN')}đ</p>
          </div>
          <Link
            to="/checkout"
            className="px-8 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700"
          >
            Thanh toán
          </Link>
        </div>
      </div>
    </div>
  );
}
