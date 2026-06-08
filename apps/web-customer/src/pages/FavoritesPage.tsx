import { Heart, ShoppingCart, Trash2, Store } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import type { Product } from '../services/api';
import { formatMoney } from '../utils/money';

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const data = await apiService.getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (productId: string) => {
    setRemovingId(productId);
    try {
      await apiService.removeFavorite(productId);
      setFavorites(favorites.filter((f) => f.id !== productId));
    } catch (error) {
      console.error('Failed to remove favorite:', error);
    } finally {
      setRemovingId(null);
    }
  };

  const handleAddToCart = async (productId: string) => {
    try {
      await apiService.addToCart(productId, 1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  if (loading) {
    return (
      <div className="p-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4 p-4 bg-white rounded-xl shadow-sm animate-pulse">
            <div className="w-24 h-24 bg-gray-200 rounded-lg" />
            <div className="flex-1 space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (favorites.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4">
        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
          <Heart className="w-12 h-12 text-gray-300" />
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Chưa có sản phẩm yêu thích</h2>
        <p className="text-gray-500 text-center mb-6">
          Lưu lại những sản phẩm bạn thích để mua sau nhé!
        </p>
        <Link
          to="/"
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition"
        >
          Khám phá ngay
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 pb-24">
      <div className="mb-4">
        <h1 className="text-xl font-bold text-gray-900">Sản phẩm yêu thích</h1>
        <p className="text-gray-500 text-sm">{favorites.length} sản phẩm</p>
      </div>

      <div className="space-y-4">
        {favorites.map((product) => (
          <div
            key={product.id}
            className="flex gap-4 p-4 bg-white rounded-xl shadow-sm border border-gray-100"
          >
            {/* Product Image */}
            <Link to={`/product/${product.id}`} className="shrink-0">
              <div className="w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                {product.images && product.images.length > 0 ? (
                  <img
                    src={product.images[0]}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <ShoppingCart className="w-8 h-8" />
                  </div>
                )}
              </div>
            </Link>

            {/* Product Info */}
            <div className="flex-1 min-w-0">
              <Link to={`/product/${product.id}`}>
                <h3 className="font-medium text-gray-900 line-clamp-2 mb-1 hover:text-blue-600">
                  {product.name}
                </h3>
              </Link>

              {product.store && (
                <Link
                  to={`/store/${product.store.id}`}
                  className="flex items-center gap-1 text-xs text-gray-500 mb-2 hover:text-blue-600"
                >
                  <Store className="w-3 h-3" />
                  <span className="truncate">{product.store.name}</span>
                </Link>
              )}

              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg font-bold text-blue-600">
                  {formatMoney(product.price || 0)}
                </span>
                {product.stock > 0 ? (
                  <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                    Còn hàng
                  </span>
                ) : (
                  <span className="text-xs text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                    Hết hàng
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleAddToCart(product.id)}
                  disabled={product.stock === 0}
                  className="flex-1 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <ShoppingCart className="w-4 h-4" />
                  Thêm vào giỏ
                </button>
                <button
                  onClick={() => handleRemoveFavorite(product.id)}
                  disabled={removingId === product.id}
                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                  aria-label="Xóa khỏi yêu thích"
                >
                  {removingId === product.id ? (
                    <div className="w-5 h-5 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Trash2 className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
