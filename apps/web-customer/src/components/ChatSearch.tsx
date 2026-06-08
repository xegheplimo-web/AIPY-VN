import { Send, MapPin, ShoppingCart, Store, Navigation } from 'lucide-react';
import { memo, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import type { SearchStoreResult, SearchProductResult } from '../services/api';

interface ChatSearchProps {
  onResultSelect?: (store: SearchStoreResult) => void;
}

interface Message {
  role: 'user' | 'bot';
  content: string;
  stores?: SearchStoreResult[];
}

export default function ChatSearch({ onResultSelect }: ChatSearchProps) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', content: '👋 Chào bạn! Bạn cần tìm sản phẩm gì hoặc cửa hàng nào gần đây?' },
  ]);
  const [input, setInput] = useState('');
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        (err) => console.warn('Không lấy được GPS:', err),
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await apiService.chatSearch({
        query: input,
        location: location || undefined,
        radius_km: 5,
        limit: 10,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: data.summary || `Tìm thấy ${data.total_found} cửa hàng phù hợp`,
          stores: data.stores || [],
        },
      ]);
    } catch (err) {
      console.error('Chat search error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: '❌ Rất tiếc, không tìm thấy kết quả. Bạn thử tìm với từ khóa khác nhé!',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-white shadow border border-gray-100 rounded-bl-none'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.stores?.map((store) => (
                <StoreCard key={store.id} store={store} location={location} onResultSelect={onResultSelect} />
              ))}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl rounded-bl-none px-4 py-3 shadow">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Tìm sản phẩm, cửa hàng..."
            className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Tìm kiếm sản phẩm hoặc cửa hàng"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50"
            aria-label="Gửi tin nhắn tìm kiếm"
            aria-busy={loading}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        {location && (
          <p className="text-xs text-gray-400 mt-2 text-center">
            📍 Đang tìm trong bán kính 5km quanh bạn
          </p>
        )}
      </div>
    </div>
  );
}

const StoreCard = memo(function StoreCard({
  store,
  location,
  onResultSelect,
}: {
  store: SearchStoreResult;
  location: { lat: number; lng: number } | null;
  onResultSelect?: (store: SearchStoreResult) => void;
}) {
  const navigate = useNavigate();

  const distance = location
    ? calculateDistance(location.lat, location.lng, store.latitude, store.longitude)
    : store.distance_m ?? null;

  const distanceText =
    distance !== null
      ? distance < 1000
        ? `${Math.round(distance)}m`
        : `${(distance / 1000).toFixed(1)}km`
      : '';

  return (
    <div className="bg-white rounded-xl shadow p-4 mb-3 border border-gray-100 mt-3">
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          {store.logo_url ? (
            <img src={store.logo_url} alt="" className="w-8 h-8 rounded-full object-cover" />
          ) : (
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <Store className="w-4 h-4 text-blue-600" />
            </div>
          )}
          <div>
            <h4 className="font-semibold text-gray-900 text-sm">{store.name}</h4>
            <p className="text-xs text-gray-500">{store.address}</p>
          </div>
        </div>
        {distanceText && (
          <span
            className={`text-xs px-2 py-1 rounded-full ${
              (distance ?? 99999) < 500
                ? 'bg-green-100 text-green-700'
                : (distance ?? 99999) < 2000
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-600'
            }`}
          >
            {distanceText}
          </span>
        )}
      </div>

      <div className="mt-3 space-y-2">
        {store.products.map((p: SearchProductResult) => (
          <div key={p.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
            <div>
              <p className="text-sm font-medium">{p.name}</p>
              <p className="text-xs text-gray-500">📍 {p.shelf_location}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-blue-600">
                {p.price?.toLocaleString('vi-VN')}đ
              </p>
              <p className={`text-xs ${p.in_stock ? 'text-green-600' : 'text-red-500'}`}>
                {p.in_stock ? `Còn ${p.stock}` : 'Hết hàng'}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-2">
        <button
          onClick={() => window.open(store.map_url, '_blank')}
          className="flex-1 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-1"
          aria-label="Chỉ đường đến cửa hàng"
        >
          <Navigation className="w-3 h-3" /> Chỉ đường
        </button>
        <button
          onClick={() => onResultSelect?.(store)}
          className="flex-1 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center justify-center gap-1"
          aria-label="Xem chi tiết cửa hàng"
        >
          <MapPin className="w-3 h-3" /> Chi tiết
        </button>
        <button
          onClick={() => navigate(`/store/${store.id}`)}
          className="flex-1 py-2 text-sm bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 flex items-center justify-center gap-1"
          aria-label="Vào cửa hàng"
        >
          <ShoppingCart className="w-3 h-3" /> Vào shop
        </button>
      </div>
    </div>
  );
});

function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371e3;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(deltaPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
