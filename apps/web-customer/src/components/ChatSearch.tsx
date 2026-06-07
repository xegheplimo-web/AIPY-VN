import { useState, useEffect, useRef } from 'react';
import { Search, Mic, Send } from 'lucide-react';

interface ChatSearchProps {
  onResultSelect?: (store: any) => void;
}

export default function ChatSearch({ onResultSelect }: ChatSearchProps) {
  const [messages, setMessages] = useState([
    { role: 'bot', content: '👋 Chào bạn! Bạn cần tìm sản phẩm gì hoặc cửa hàng nào gần đây?' }
  ]);
  const [input, setInput] = useState('');
  const [location, setLocation] = useState(null);
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

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371e3;
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(deltaPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          location,
          radius_km: 5
        })
      });
      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'bot',
        content: data.summary,
        stores: data.stores
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        content: '❌ Rất tiếc, không tìm thấy kết quả. Bạn thử tìm với từ khóa khác nhé!'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const StoreCard = ({ store }: { store: any }) => {
    const distance = location ? calculateDistance(location.lat, location.lng, store.latitude, store.longitude) : null;

    return (
      <div className="bg-white rounded-xl shadow p-4 mb-3 border border-gray-100">
        <div className="flex justify-between items-start">
          <div>
            <h4 className="font-semibold text-gray-900">{store.name}</h4>
            <p className="text-sm text-gray-500">{store.address}</p>
          </div>
          {distance && (
            <span className={`text-xs px-2 py-1 rounded-full ${
              distance < 500 ? 'bg-green-100 text-green-700' :
              distance < 2000 ? 'bg-yellow-100 text-yellow-700' :
              'bg-gray-100 text-gray-600'
            }`}>
              {(distance / 1000).toFixed(1)}km
            </span>
          )}
        </div>

        <div className="mt-3 space-y-2">
          {store.products.map((p: any) => (
            <div key={p.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <div>
                <p className="text-sm font-medium">{p.name}</p>
                <p className="text-xs text-gray-500">📍 {p.shelf_location}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-blue-600">{p.price?.toLocaleString('vi-VN')}đ</p>
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
            className="flex-1 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            📍 Chỉ đường
          </button>
          <button
            onClick={() => onResultSelect?.(store)}
            className="flex-1 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            ℹ️ Xem chi tiết
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg: any, idx: number) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-none'
                : 'bg-white shadow border border-gray-100 rounded-bl-none'
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.stores?.map((store: any) => (
                <StoreCard key={store.id} store={store} />
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
          <button className="p-3 text-gray-500 hover:text-blue-600">
            <Mic className="w-5 h-5" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Tìm sản phẩm, cửa hàng..."
            className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50"
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
