import { Bell, Bot, MapPin, Mic, Search, ShoppingCart, Star } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { SearchStoreResult } from '../services/api';
import { apiService } from '../services/api';
import { formatDistance } from '../utils/distance';

export default function HomePage() {
  const navigate = useNavigate();
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [nearbyStores, setNearbyStores] = useState<SearchStoreResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Get user location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
          // Load nearby stores
          loadNearbyStores(position.coords.latitude, position.coords.longitude);
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  }, []);

  const loadNearbyStores = async (lat: number, lng: number) => {
    try {
      setLoading(true);
      const stores = await apiService.getNearbyStores(lat, lng, 5);
      setNearbyStores(stores);
    } catch (error) {
      console.error('Error loading nearby stores:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    navigate('/search', { state: { query: searchQuery, location } });
  };

  const handleQuickSearch = (query: string) => {
    setSearchQuery(query);
    navigate('/search', { state: { query, location } });
  };

  const categories = ['Thuốc', 'Mỹ phẩm', 'Thực phẩm', 'Mẹ & Bé', 'Điện tử'];
  const quickSearches = ['Panadol', 'Vitamin C', 'Khẩu trang'];

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-bold text-blue-600">AI-SHOP.VN</h1>
          <button className="p-2 hover:bg-gray-100 rounded-full">
            <Bell size={18} className="text-gray-700" />
          </button>
        </div>

        {/* Search Bar */}
        <button
          onClick={() => navigate('/search')}
          className="w-full flex items-center gap-3 bg-gray-100 rounded-xl px-4 py-3 text-left hover:bg-gray-200 transition"
        >
          <Search size={17} className="text-gray-500" />
          <span className="text-gray-500 flex-1">Tìm thuốc, sản phẩm, cửa hàng gần bạn</span>
          <Mic size={16} className="text-gray-500" />
        </button>

        {/* Location */}
        {location && (
          <div className="flex items-center gap-2 mt-3 text-sm text-gray-600">
            <MapPin size={15} className="text-blue-600" />
            <span>Quận 1, TP.HCM</span>
          </div>
        )}
      </div>

      {/* Categories */}
      <div className="px-4 py-4">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => handleQuickSearch(category)}
              className="flex-shrink-0 px-4 py-2 bg-white rounded-full border border-gray-200 text-sm font-medium hover:bg-blue-50 hover:border-blue-300 transition"
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* AI Assistant Card */}
      <div className="px-4 mb-4">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-4 text-white">
          <div className="flex items-start gap-3">
            <div className="bg-white/20 rounded-full p-2">
              <Bot size={34} />
            </div>
            <div className="flex-1">
              <p className="font-bold text-lg">Chào bạn!</p>
              <p className="text-blue-100 text-sm">Bạn cần tìm sản phẩm gì gần đây?</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Searches */}
      <div className="px-4 mb-4">
        <h3 className="font-semibold text-gray-900 mb-3">Gợi ý tìm kiếm</h3>
        <div className="flex gap-2 flex-wrap">
          {quickSearches.map((query) => (
            <button
              key={query}
              onClick={() => handleQuickSearch(query)}
              className="px-3 py-1.5 bg-white rounded-full border border-gray-200 text-sm hover:bg-blue-50 hover:border-blue-300 transition"
            >
              {query}
            </button>
          ))}
        </div>
      </div>

      {/* Nearby Stores */}
      <div className="px-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Cửa hàng nổi bật</h3>
          <button
            onClick={() => navigate('/locator')}
            className="text-blue-600 text-sm font-medium"
          >
            Xem tất cả
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Đang tải...</div>
        ) : nearbyStores.length > 0 ? (
          <div className="flex gap-3 overflow-x-auto pb-2">
            {nearbyStores.slice(0, 5).map((store) => (
              <div
                key={store.id}
                onClick={() => navigate(`/store/${store.id}`)}
                className="flex-shrink-0 w-48 bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition"
              >
                {store.cover_image_url && (
                  <img
                    src={store.cover_image_url}
                    alt={store.name}
                    className="w-full h-24 object-cover"
                  />
                )}
                <div className="p-3">
                  <h4 className="font-semibold text-sm text-gray-900 truncate">{store.name}</h4>
                  {store.distance_m && (
                    <p className="text-xs text-gray-500 mt-1">{formatDistance(store.distance_m)}</p>
                  )}
                  {store.rating && (
                    <div className="flex items-center gap-1 mt-1">
                      <Star size={12} className="text-yellow-500 fill-current" />
                      <span className="text-xs text-gray-600">{store.rating}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">Không tìm thấy cửa hàng gần bạn</div>
        )}
      </div>

      {/* Featured Products */}
      <div className="px-4 mb-4">
        <h3 className="font-semibold text-gray-900 mb-3">Sản phẩm gợi ý cho bạn</h3>
        <div className="grid grid-cols-2 gap-3">
          {nearbyStores.slice(0, 2).map((store) =>
            store.products.slice(0, 2).map((product) => (
              <div
                key={product.id}
                onClick={() => navigate(`/product/${product.id}`)}
                className="bg-white rounded-xl border border-gray-200 p-3 cursor-pointer hover:shadow-md transition"
              >
                <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center">
                  <ShoppingCart size={24} className="text-gray-400" />
                </div>
                <h4 className="font-medium text-sm text-gray-900 truncate">{product.name}</h4>
                {product.price && (
                  <p className="text-blue-600 font-semibold text-sm mt-1">
                    {new Intl.NumberFormat('vi-VN', {
                      style: 'currency',
                      currency: 'VND',
                    }).format(product.price)}
                  </p>
                )}
                {product.in_stock && (
                  <span className="text-xs text-green-600 mt-1">Còn {product.stock}</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
