import {
  CheckCircle,
  ChevronRight,
  Clock,
  Image as ImageIcon,
  MapPin,
  Package,
  Phone,
  Send,
  ShoppingCart,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiService } from '../services/api';
import type { Store } from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'store';
  content: string;
  timestamp: Date;
  type?: 'text' | 'image' | 'location' | 'product' | 'order';
  metadata?: any;
}

interface ChatStore {
  id: string;
  name: string;
  address: string;
  phone: string;
  avatar?: string;
  isOnline: boolean;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
}

export default function StoreChatPage() {
  const { store_id } = useParams<{ store_id: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [showProductPicker, setShowProductPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [store, setStore] = useState<ChatStore | null>(null);

  useEffect(() => {
    if (store_id) loadStore(store_id);
    setMessages([
      { id: '1', role: 'store', content: 'Xin chào! Tôi có thể giúp gì cho bạn?', timestamp: new Date() },
    ]);
  }, [store_id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadStore = async (storeId: string) => {
    try {
      const data: any = await apiService.getStore(storeId);
      const s = data?.data || data;
      setStore({
        id: s.id,
        name: s.name,
        address: s.address,
        phone: s.phone || '',
        avatar: s.logo_url,
        isOnline: s.is_open_now || false,
      });
    } catch (err) {
      console.error('Failed to load store:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // TODO: Send real message via WebSocket/API when backend is ready
    setTimeout(() => {
      const storeMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'store',
        content: 'Cảm ơn bạn đã nhắn tin! Chúng tôi sẽ phản hồi sớm nhất có thể.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, storeMsg]);
    }, 1000);
  };

  const handleQuickAction = (actionId: string) => {
    switch (actionId) {
      case 'check_stock':
        setInput('Bạn còn sản phẩm này không?');
        break;
      case 'send_location':
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              const locationMsg: Message = {
                id: Date.now().toString(),
                role: 'user',
                content: `Vị trí của tôi: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`,
                timestamp: new Date(),
                type: 'location',
                metadata: { lat: pos.coords.latitude, lng: pos.coords.longitude },
              };
              setMessages((prev) => [...prev, locationMsg]);
            },
            () => alert('Không thể lấy vị trí của bạn')
          );
        }
        break;
      case 'send_image':
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
              const imageMsg: Message = {
                id: Date.now().toString(),
                role: 'user',
                content: 'Đã gửi ảnh',
                timestamp: new Date(),
                type: 'image',
                metadata: { imageUrl: event.target?.result as string },
              };
              setMessages((prev) => [...prev, imageMsg]);
            };
            reader.readAsDataURL(file);
          }
        };
        fileInput.click();
        break;
      case 'call_store':
        if (store?.phone) window.location.href = `tel:${store.phone}`;
        break;
      case 'create_order':
        setShowProductPicker(true);
        break;
    }
    setShowQuickActions(false);
  };

  const quickActions: QuickAction[] = [
    { id: 'check_stock', label: 'Hỏi còn hàng', icon: <Package className="w-5 h-5" />, action: () => handleQuickAction('check_stock') },
    { id: 'send_location', label: 'Gửi vị trí', icon: <MapPin className="w-5 h-5" />, action: () => handleQuickAction('send_location') },
    { id: 'send_image', label: 'Gửi ảnh', icon: <ImageIcon className="w-5 h-5" />, action: () => handleQuickAction('send_image') },
    { id: 'call_store', label: 'Gọi cửa hàng', icon: <Phone className="w-5 h-5" />, action: () => handleQuickAction('call_store') },
    { id: 'create_order', label: 'Tạo đơn từ chat', icon: <ShoppingCart className="w-5 h-5" />, action: () => handleQuickAction('create_order') },
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <ChevronRight className="w-5 h-5 rotate-180" />
        </button>
        <div className="flex-1 flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Package className="w-5 h-5 text-blue-600" />
            </div>
            {store?.isOnline && <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />}
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">{store?.name || 'Cửa hàng'}</h2>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              {store?.isOnline ? <><CheckCircle size={12} className="text-green-500" />Đang online</> : <><Clock size={12} className="text-gray-400" />Đang offline</>}
            </p>
          </div>
        </div>
        <button onClick={() => handleQuickAction('call_store')} className="p-2 bg-green-50 text-green-600 rounded-full hover:bg-green-100">
          <Phone className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white shadow border border-gray-100 rounded-bl-none'}`}>
              {msg.type === 'image' && msg.metadata?.imageUrl && <img src={msg.metadata.imageUrl} alt="Sent image" className="w-full h-48 object-cover rounded-lg mb-2" />}
              {msg.type === 'location' && <div className="flex items-center gap-2 mb-2"><MapPin size={16} /><span className="text-sm">Đã gửi vị trí</span></div>}
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>{msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {showQuickActions && (
        <div className="absolute bottom-20 left-4 right-4 bg-white rounded-xl shadow-lg border p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold">Hành động nhanh</h3>
            <button onClick={() => setShowQuickActions(false)} className="p-1 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action) => (
              <button key={action.id} onClick={action.action} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                {action.icon}
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {showProductPicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[80vh] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold">Chọn sản phẩm</h3>
              <button onClick={() => setShowProductPicker(false)} className="p-1 hover:bg-gray-100 rounded"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-4 overflow-y-auto max-h-96">
              <p className="text-gray-500 text-center py-8">Chức năng đang phát triển</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <button onClick={() => setShowQuickActions(!showQuickActions)} className="p-3 bg-gray-100 rounded-full hover:bg-gray-200">
            <Package className="w-5 h-5 text-gray-600" />
          </button>
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSend()} placeholder="Nhập tin nhắn..." className="flex-1 px-4 py-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button onClick={handleSend} disabled={!input.trim()} className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
