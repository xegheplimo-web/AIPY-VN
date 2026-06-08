import { Bot, ChevronRight, Filter, MapPin, Search, ShoppingCart } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { ChatSearchRequest, SearchStoreResult } from '../services/api';
import { apiService } from '../services/api';
import { calculateShippingFee, formatDistance } from '../utils/distance';
import { formatMoney } from '../utils/money';

export default function SearchPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { query?: string; location?: { lat: number; lng: number } };

  const [searchQuery, setSearchQuery] = useState(state?.query || '');
  const [userLocation, setUserLocation] = useState(state?.location || null);
  const [results, setResults] = useState<SearchStoreResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (searchQuery) {
      performSearch();
    }
  }, [searchQuery]);

  const performSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      const request: ChatSearchRequest = {
        query: searchQuery,
        location: userLocation || undefined,
        radius_km: 5,
        limit: 10,
      };
      const response = await apiService.chatSearch(request);
      setResults(response.stores);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (storeId: string, productId: string) => {
    try {
      await apiService.addToCart(productId, 1);
      // Show success notification
    } catch (error) {
      console.error('Add to cart error:', error);
    }
  };

  const handleOpenMap = (store: SearchStoreResult) => {
    if (store.map_url) {
      window.open(store.map_url, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
            <ChevronRight size={20} className="rotate-180" />
          </button>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && performSearch()}
            placeholder="Tìm sản phẩm, cửa hàng..."
            className="flex-1 px-4 py-2 bg-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={performSearch}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Search size={20} />
          </button>
        </div>
      </div>

      {/* AI Summary */}
      {results.length > 0 && (
        <div className="bg-blue-50 border-b border-blue-100 px-4 py-3">
          <div className="flex items-start gap-2">
            <Bot size={18} className="text-blue-600 mt-0.5" />
            <p className="text-sm text-blue-900">{results.length} cửa hàng phù hợp</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 rounded-full text-sm font-medium hover:bg-gray-200"
          >
            <Filter size={14} />
            Bộ lọc
          </button>
          <button className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm font-medium hover:bg-gray-50">
            &lt;500m
          </button>
          <button className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm font-medium hover:bg-gray-50">
            Còn hàng
          </button>
          <button className="px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm font-medium hover:bg-gray-50">
            Giá thấp → cao
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="px-4 py-4">
        {loading ? (
          <div className="text-center py-8 text-gray-500">Đang tìm kiếm...</div>
        ) : results.length === 0 ? (
          <div className="text-center py-8">
            <ShoppingCart size={44} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Không tìm thấy kết quả</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg"
            >
              Quay lại trang chủ
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((store) => (
              <StoreResultCard
                key={store.id}
                store={store}
                onAddToCart={handleAddToCart}
                onOpenMap={handleOpenMap}
                onOpenStore={() => navigate(`/store/${store.id}`)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Map Preview */}
      {results.length > 0 && (
        <div className="fixed bottom-20 left-0 right-0 bg-white border-t border-gray-100 px-4 py-3">
          <div className="flex items-center justify-between max-w-3xl mx-auto">
            <div className="flex items-center gap-2">
              <MapPin size={18} className="text-blue-600" />
              <span className="text-sm text-gray-700">Bản đồ cửa hàng gần bạn</span>
            </div>
            <button
              onClick={() => navigate('/locator')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
            >
              Xem bản đồ
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StoreResultCard({
  store,
  onAddToCart,
  onOpenMap,
  onOpenStore,
}: {
  store: SearchStoreResult;
  onAddToCart: (storeId: string, productId: string) => void;
  onOpenMap: (store: SearchStoreResult) => void;
  onOpenStore: () => void;
}) {
  const product = store.products[0];
  const shippingFee = calculateShippingFee(store.distance_m ? store.distance_m / 1000 : 0);

  return (
    <article className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Cover Image */}
      {store.cover_image_url && (
        <img src={store.cover_image_url} alt={store.name} className="w-full h-32 object-cover" />
      )}

      <div className="p-4">
        {/* Store Info */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900">{store.name}</h4>
            <div className="flex items-center gap-1 mt-1 text-sm text-gray-600">
              <MapPin size={13} />
              <span className="truncate">{store.address}</span>
            </div>
          </div>
          {store.distance_m && (
            <span className="ml-2 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
              {formatDistance(store.distance_m)}
            </span>
          )}
        </div>

        {/* Product */}
        {product && (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-3">
            <div className="w-16 h-16 bg-white rounded-lg flex items-center justify-center">
              <ShoppingCart size={24} className="text-gray-400" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-sm text-gray-900">{product.name}</p>
              <p className="text-xs text-gray-500">
                {product.category} · {product.shelf_location}
              </p>
              {product.price && (
                <p className="text-blue-600 font-semibold text-sm">{formatMoney(product.price)}</p>
              )}
            </div>
            {product.in_stock && (
              <span className="px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs font-medium">
                Còn {product.stock}
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onOpenMap(store)}
            className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
          >
            Chỉ đường
          </button>
          <button
            onClick={onOpenStore}
            className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
          >
            Vào cửa hàng
          </button>
          {product && (
            <button
              onClick={() => onAddToCart(store.id, product.id)}
              className="flex-1 px-3 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600"
            >
              Thêm
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
