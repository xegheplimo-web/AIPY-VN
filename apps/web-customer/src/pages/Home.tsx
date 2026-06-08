import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Bot,
  MapPin,
  Mic,
  Search,
  Star,
  Store,
  ChevronRight,
} from 'lucide-react';
import { apiService } from '../services/api';
import type { Store as StoreType, Product } from '../services/api';
import { formatDistance } from '../utils/distance';
import { formatMoney } from '../utils/money';
import ChatSearch from '../components/ChatSearch';

const categories = [
  { id: 'thuoc', name: 'Thuốc', icon: '💊', color: 'bg-rose-50 text-rose-600' },
  { id: 'mypham', name: 'Mỹ phẩm', icon: '💄', color: 'bg-pink-50 text-pink-600' },
  { id: 'thucpham', name: 'Thực phẩm', icon: '🍎', color: 'bg-green-50 text-green-600' },
  { id: 'mebe', name: 'Mẹ & Bé', icon: '🍼', color: 'bg-blue-50 text-blue-600' },
  { id: 'dientu', name: 'Điện tử', icon: '🔌', color: 'bg-purple-50 text-purple-600' },
  { id: 'suckhoe', name: 'Sức khỏe', icon: '❤️', color: 'bg-red-50 text-red-600' },
];

const suggestionChips = ['Panadol', 'Vitamin C', 'Khẩu trang', 'Nước rửa tay', 'Dầu gội'];

export default function Home() {
  const navigate = useNavigate();
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locationName, setLocationName] = useState('Quận 1, TP.HCM');
  const [stores, setStores] = useState<StoreType[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setLocation(loc);
          setLocationName('Vị trí hiện tại');
          loadStores(loc);
        },
        () => {
          loadStores();
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      loadStores();
    }
  }, []);

  const loadStores = async (loc?: { lat: number; lng: number }) => {
    try {
      setLoading(true);
      let storesData: StoreType[] = [];
      if (loc) {
        try {
          storesData = await apiService.getNearbyStores(loc.lat, loc.lng, 5);
        } catch {
          storesData = await apiService.getStores();
        }
      } else {
        storesData = await apiService.getStores();
      }
      setStores(storesData.slice(0, 6));

      // Load some products from first store for suggestions
      if (storesData.length > 0) {
        try {
          const productsData = await apiService.getStoreProducts(storesData[0].id);
          setProducts(productsData.slice(0, 8));
        } catch {
          setProducts([]);
        }
      }
    } catch (err) {
      console.error('Failed to load home data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate('/search', { state: { query: searchQuery, location } });
    }
  };

  const handleCategoryClick = (catId: string) => {
    navigate('/search', { state: { query: catId, location } });
  };

  const handleSuggestionClick = (suggestion: string) => {
    navigate('/search', { state: { query: suggestion, location } });
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <header className="bg-white px-4 pt-4 pb-3">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-xl font-bold text-blue-600 tracking-tight">AI-SHOP.VN</h1>
            <p className="text-xs text-gray-500">AI tìm sản phẩm gần bạn</p>
          </div>
          <button
            onClick={() => navigate('/profile')}
            className="p-2 hover:bg-gray-100 rounded-full transition"
            aria-label="Thông báo"
          >
            <Bell className="w-5 h-5 text-gray-700" />
          </button>
        </div>

        {/* Location Chip */}
        <div className="flex items-center gap-1 text-xs text-gray-600 mb-3">
          <MapPin className="w-3.5 h-3.5 text-blue-600" />
          <span className="truncate">{locationName}</span>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSearch}
            className="flex-1 flex items-center gap-2 px-4 py-2.5 bg-gray-100 rounded-xl text-left hover:bg-gray-200 transition"
          >
            <Search className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-500 flex-1">Tìm thuốc, sản phẩm, cửa hàng...</span>
            <Mic className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </header>

      {/* Chat AI Inline Toggle */}
      {showChat ? (
        <div className="fixed inset-0 z-[60] bg-white flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
            <h2 className="font-semibold flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-600" /> AI Trợ lý
            </h2>
            <button
              onClick={() => setShowChat(false)}
              className="px-3 py-1 text-sm bg-gray-100 rounded-lg"
            >
              Đóng
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatSearch />
          </div>
        </div>
      ) : (
        <>
          {/* Categories */}
          <div className="bg-white px-4 py-3 border-b border-gray-100">
            <div className="flex gap-3 overflow-x-auto scrollbar-hide">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryClick(cat.name)}
                  className={`flex flex-col items-center gap-1 min-w-[64px] p-2 rounded-xl ${cat.color} transition active:scale-95`}
                >
                  <span className="text-xl">{cat.icon}</span>
                  <span className="text-xs font-medium whitespace-nowrap">{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* AI Card */}
          <div className="px-4 py-3">
            <button
              onClick={() => setShowChat(true)}
              className="w-full flex items-center gap-3 p-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl shadow-sm hover:shadow-md transition"
            >
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="font-semibold">Chào bạn!</p>
                <p className="text-sm text-blue-100">Bạn cần tìm sản phẩm gì gần đây?</p>
              </div>
              <ChevronRight className="w-5 h-5 ml-auto opacity-70" />
            </button>
          </div>

          {/* Suggestions */}
          <div className="px-4 pb-3">
            <div className="flex flex-wrap gap-2">
              {suggestionChips.map((chip) => (
                <button
                  key={chip}
                  onClick={() => handleSuggestionClick(chip)}
                  className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* Featured Stores */}
          <section className="px-4 py-3">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-gray-900">Cửa hàng nổi bật</h2>
              <button
                onClick={() => navigate('/locator')}
                className="text-sm text-blue-600 hover:underline"
              >
                Xem tất cả
              </button>
            </div>
            {loading ? (
              <div className="flex gap-3 overflow-x-auto">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="min-w-[200px] h-28 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : stores.length === 0 ? (
              <p className="text-sm text-gray-500">Chưa có cửa hàng nào.</p>
            ) : (
              <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-2">
                {stores.map((store) => (
                  <button
                    key={store.id}
                    onClick={() => navigate(`/store/${store.id}`)}
                    className="min-w-[200px] bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition text-left"
                  >
                    {store.cover_image_url ? (
                      <div className="h-24 bg-gray-100 relative">
                        <img
                          src={store.cover_image_url}
                          alt={store.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {store.is_open_now !== undefined && (
                          <span
                            className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                              store.is_open_now
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {store.is_open_now ? 'Mở cửa' : 'Đóng'}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="h-24 bg-blue-50 flex items-center justify-center text-3xl">
                        🏪
                      </div>
                    )}
                    <div className="p-3">
                      <h3 className="font-medium text-sm text-gray-900 truncate">{store.name}</h3>
                      <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        <span className="truncate">{store.address}</span>
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {store.distance_m !== undefined && store.distance_m !== null && (
                          <span className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-full">
                            {formatDistance(store.distance_m)}
                          </span>
                        )}
                        {store.rating && (
                          <span className="text-xs text-yellow-600 bg-yellow-50 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                            <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                            {store.rating}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Suggested Products */}
          <section className="px-4 py-3">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-gray-900">Sản phẩm gợi ý</h2>
              <button
                onClick={() => navigate('/search')}
                className="text-sm text-blue-600 hover:underline"
              >
                Xem tất cả
              </button>
            </div>
            {loading ? (
              <div className="grid grid-cols-2 gap-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : products.length === 0 ? (
              <p className="text-sm text-gray-500">Chưa có sản phẩm gợi ý.</p>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {products.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => navigate(`/product/${product.id}`)}
                    className="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition text-left"
                  >
                    <div className="h-32 bg-gray-100 relative">
                      {product.images?.[0] ? (
                        <img
                          src={product.images[0]}
                          alt={product.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-300 text-4xl">
                          📦
                        </div>
                      )}
                      {product.stock > 0 && product.stock <= 5 && (
                        <span className="absolute top-2 left-2 px-2 py-0.5 bg-red-500 text-white text-[10px] font-medium rounded-full">
                          Sắp hết
                        </span>
                      )}
                    </div>
                    <div className="p-3">
                      <h3 className="font-medium text-sm text-gray-900 line-clamp-2 min-h-[2.5rem]">
                        {product.name}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">{product.category || 'Sản phẩm'}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-blue-600 font-bold text-sm">
                          {product.price ? formatMoney(product.price) : 'Liên hệ'}
                        </span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                            product.stock > 0
                              ? 'bg-green-50 text-green-700'
                              : 'bg-red-50 text-red-700'
                          }`}
                        >
                          {product.stock > 0 ? `Còn ${product.stock}` : 'Hết hàng'}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Fast Actions */}
          <section className="px-4 py-3">
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => navigate('/orders')}
                className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition text-left"
              >
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mb-2">
                  <Store className="w-5 h-5 text-purple-600" />
                </div>
                <p className="font-medium text-sm">Đơn hàng của tôi</p>
                <p className="text-xs text-gray-500 mt-0.5">Theo dõi & lịch sử</p>
              </button>
              <button
                onClick={() => navigate('/chat')}
                className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition text-left"
              >
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mb-2">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <p className="font-medium text-sm">Chat AI</p>
                <p className="text-xs text-gray-500 mt-0.5">Tìm sản phẩm thông minh</p>
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
