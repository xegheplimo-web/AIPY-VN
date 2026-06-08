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
  Wifi,
  WifiOff,
  X,
  Loader2,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiService } from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  id: string;
  sender_id: string | null;
  store_id: string | null;
  content: string;
  message_type: string;
  is_read: boolean;
  created_at: string;
}

interface DisplayMessage {
  id: string;
  role: 'user' | 'store';
  content: string;
  timestamp: Date;
  type?: 'text' | 'image' | 'location' | 'product' | 'order';
  metadata?: Record<string, unknown>;
}

interface ChatStore {
  id: string;
  name: string;
  address: string;
  phone: string;
  avatar?: string;
  isOnline: boolean;
  ownerId?: string;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Derive the WebSocket base URL from the API base URL (http→ws, https→wss). */
function getWsBaseUrl(): string {
  const apiBase: string =
    (import.meta as any).env?.VITE_API_URL || 'http://localhost:9000';
  return apiBase.replace(/^http/, 'ws');
}

/** Format a Date for display (Vietnamese locale, HH:mm). */
function formatTime(date: Date): string {
  return date.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function StoreChatPage() {
  const { store_id } = useParams<{ store_id: string }>();
  const navigate = useNavigate();

  // ---- state ----
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [showProductPicker, setShowProductPicker] = useState(false);
  const [store, setStore] = useState<ChatStore | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>('disconnected');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- refs ----
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const userIdRef = useRef<string | null>(null);
  const mountedRef = useRef(true);

  // ========================================================================
  // Auto-scroll
  // ========================================================================

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // ========================================================================
  // Load store info
  // ========================================================================

  const loadStore = useCallback(async (storeId: string) => {
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
        ownerId: s.owner_id || s.user_id || undefined,
      });
    } catch (err) {
      console.error('Không thể tải thông tin cửa hàng:', err);
      setError('Không thể tải thông tin cửa hàng');
    }
  }, []);

  // ========================================================================
  // Load current user id (for distinguishing sent vs received)
  // ========================================================================

  const loadCurrentUserId = useCallback(async () => {
    try {
      const profile: any = await apiService.getProfile();
      userIdRef.current = profile?.id || profile?.data?.id || null;
    } catch {
      // Not critical – messages will still work, just may default role
    }
  }, []);

  // ========================================================================
  // Load chat history via REST
  // ========================================================================

  const loadChatHistory = useCallback(
    async (storeId: string) => {
      try {
        const res: any = await apiService.get(
          `/api/stores/${storeId}/messages?limit=50`
        );
        const raw: ChatMessage[] = res?.messages || res?.data?.messages || [];
        if (raw.length > 0) {
          const mapped: DisplayMessage[] = raw.map((m) => ({
            id: m.id,
            role:
              m.sender_id && m.sender_id === userIdRef.current
                ? 'user'
                : 'store',
            content: m.content,
            timestamp: new Date(m.created_at),
            type: (m.message_type as DisplayMessage['type']) || 'text',
          }));
          setMessages(mapped);
        }
      } catch (err) {
        console.error('Không thể tải lịch sử chat:', err);
        // Non-fatal – user can still send messages
      }
    },
    []
  );

  // ========================================================================
  // WebSocket connection
  // ========================================================================

  const connectWebSocket = useCallback(
    (storeId: string) => {
      // Clean up any existing connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      const token = apiService.getToken();
      if (!token) {
        setError('Vui lòng đăng nhập để chat với cửa hàng');
        setLoading(false);
        return;
      }

      const wsBase = getWsBaseUrl();
      const wsUrl = `${wsBase}/ws/chat/${storeId}?token=${encodeURIComponent(token)}`;

      setConnectionStatus('connecting');
      setError(null);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setConnectionStatus('connected');
        setError(null);

        // Keep-alive ping every 30s
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30_000);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'new_message': {
              const msg = data.message;
              if (!msg) break;
              const isIncoming =
                msg.sender_id && msg.sender_id !== userIdRef.current;
              const display: DisplayMessage = {
                id: msg.id || Date.now().toString(),
                role: isIncoming ? 'store' : 'user',
                content: msg.content || '',
                timestamp: msg.created_at
                  ? new Date(msg.created_at)
                  : new Date(),
                type: 'text',
              };
              setMessages((prev) => {
                // Deduplicate
                if (prev.some((m) => m.id === display.id)) return prev;
                return [...prev, display];
              });
              setIsTyping(false);
              break;
            }
            case 'typing': {
              if (data.user_id && data.user_id !== userIdRef.current) {
                setIsTyping(true);
                if (typingTimeoutRef.current)
                  clearTimeout(typingTimeoutRef.current);
                typingTimeoutRef.current = setTimeout(
                  () => setIsTyping(false),
                  3_000
                );
              }
              break;
            }
            case 'room_joined':
              // Acknowledged – no action needed
              break;
            case 'pong':
              break;
            case 'error':
              console.warn('WebSocket error from server:', data.message);
              break;
            default:
              // Unknown type – try to handle as a plain chat message
              if (data.content) {
                const fallback: DisplayMessage = {
                  id: data.id || Date.now().toString(),
                  role:
                    data.sender_id && data.sender_id === userIdRef.current
                      ? 'user'
                      : 'store',
                  content: data.content,
                  timestamp: data.created_at
                    ? new Date(data.created_at)
                    : new Date(),
                  type: 'text',
                };
                setMessages((prev) => {
                  if (prev.some((m) => m.id === fallback.id)) return prev;
                  return [...prev, fallback];
                });
              }
          }
        } catch (parseErr) {
          console.error('Không thể phân tích tin nhắn WebSocket:', parseErr);
        }
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        setConnectionStatus('disconnected');

        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Auto-reconnect after delay unless it was an intentional close
        if (event.code !== 1000) {
          if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = setTimeout(() => {
            if (mountedRef.current && store_id) {
              connectWebSocket(store_id);
            }
          }, 3_000);
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        setError('Không thể kết nối đến máy chủ chat');
        setConnectionStatus('disconnected');
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  // ========================================================================
  // Send message via WebSocket
  // ========================================================================

  const handleSend = useCallback(() => {
    if (!input.trim()) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Không có kết nối. Đang thử kết nối lại...');
      return;
    }

    const content = input.trim();
    const receiverId = store?.ownerId || store_id || '';

    // Optimistically add to local list
    const optimisticMsg: DisplayMessage = {
      id: `pending-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
      type: 'text',
    };
    setMessages((prev) => [...prev, optimisticMsg]);
    setInput('');

    // Send over WebSocket
    wsRef.current.send(
      JSON.stringify({
        type: 'message',
        content,
        receiver_id: receiverId,
      })
    );
  }, [input, store?.ownerId, store_id]);

  // ========================================================================
  // Quick actions
  // ========================================================================

  const handleQuickAction = useCallback(
    (actionId: string) => {
      switch (actionId) {
        case 'check_stock':
          setInput('Bạn còn sản phẩm này không?');
          break;
        case 'send_location':
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              (pos) => {
                const locationMsg: DisplayMessage = {
                  id: Date.now().toString(),
                  role: 'user',
                  content: `Vị trí của tôi: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)}`,
                  timestamp: new Date(),
                  type: 'location',
                  metadata: {
                    lat: pos.coords.latitude,
                    lng: pos.coords.longitude,
                  },
                };
                setMessages((prev) => [...prev, locationMsg]);

                // Also send via WS if connected
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                  wsRef.current.send(
                    JSON.stringify({
                      type: 'message',
                      content: locationMsg.content,
                      receiver_id: store?.ownerId || store_id || '',
                    })
                  );
                }
              },
              () => alert('Không thể lấy vị trí của bạn')
            );
          }
          break;
        case 'send_image': {
          const fileInput = document.createElement('input');
          fileInput.type = 'file';
          fileInput.accept = 'image/*';
          fileInput.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
              const reader = new FileReader();
              reader.onload = (event) => {
                const imageMsg: DisplayMessage = {
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
        }
        case 'call_store':
          if (store?.phone) window.location.href = `tel:${store.phone}`;
          break;
        case 'create_order':
          setShowProductPicker(true);
          break;
      }
      setShowQuickActions(false);
    },
    [store?.ownerId, store?.phone, store_id]
  );

  const quickActions: QuickAction[] = [
    {
      id: 'check_stock',
      label: 'Hỏi còn hàng',
      icon: <Package className="w-5 h-5" />,
      action: () => handleQuickAction('check_stock'),
    },
    {
      id: 'send_location',
      label: 'Gửi vị trí',
      icon: <MapPin className="w-5 h-5" />,
      action: () => handleQuickAction('send_location'),
    },
    {
      id: 'send_image',
      label: 'Gửi ảnh',
      icon: <ImageIcon className="w-5 h-5" />,
      action: () => handleQuickAction('send_image'),
    },
    {
      id: 'call_store',
      label: 'Gọi cửa hàng',
      icon: <Phone className="w-5 h-5" />,
      action: () => handleQuickAction('call_store'),
    },
    {
      id: 'create_order',
      label: 'Tạo đơn từ chat',
      icon: <ShoppingCart className="w-5 h-5" />,
      action: () => handleQuickAction('create_order'),
    },
  ];

  // ========================================================================
  // Effects – lifecycle
  // ========================================================================

  useEffect(() => {
    mountedRef.current = true;
    if (!store_id) return;

    const init = async () => {
      setLoading(true);
      await loadCurrentUserId();
      await Promise.all([loadStore(store_id), loadChatHistory(store_id)]);
      setLoading(false);
      connectWebSocket(store_id);
    };

    init();

    return () => {
      mountedRef.current = false;
      // Clean up WebSocket
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store_id]);

  // ========================================================================
  // Loading state
  // ========================================================================

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-600" />
        <span className="ml-3 text-gray-500">Đang tải...</span>
      </div>
    );
  }

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* ---- Header ---- */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 rounded-full"
          aria-label="Quay lại"
        >
          <ChevronRight className="w-5 h-5 rotate-180" />
        </button>

        <div className="flex-1 flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <Package className="w-5 h-5 text-emerald-600" />
            </div>
            {store?.isOnline && (
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
            )}
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">
              {store?.name || 'Cửa hàng'}
            </h2>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              {store?.isOnline ? (
                <>
                  <CheckCircle size={12} className="text-green-500" />
                  Đang online
                </>
              ) : (
                <>
                  <Clock size={12} className="text-gray-400" />
                  Đang offline
                </>
              )}
            </p>
          </div>
        </div>

        {/* Connection status indicator */}
        <div className="flex items-center gap-1.5 mr-1">
          {connectionStatus === 'connected' ? (
            <Wifi className="w-4 h-4 text-green-500" />
          ) : connectionStatus === 'connecting' ? (
            <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-400" />
          )}
          <span
            className={`text-xs font-medium ${
              connectionStatus === 'connected'
                ? 'text-green-600'
                : connectionStatus === 'connecting'
                  ? 'text-amber-600'
                  : 'text-red-500'
            }`}
          >
            {connectionStatus === 'connected'
              ? 'Đã kết nối'
              : connectionStatus === 'connecting'
                ? 'Đang kết nối...'
                : 'Mất kết nối'}
          </span>
        </div>

        <button
          onClick={() => handleQuickAction('call_store')}
          className="p-2 bg-green-50 text-green-600 rounded-full hover:bg-green-100"
          aria-label="Gọi cửa hàng"
        >
          <Phone className="w-5 h-5" />
        </button>
      </div>

      {/* ---- Error banner ---- */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center justify-between shrink-0">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ---- Messages ---- */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-12">
            <Package className="w-12 h-12 mx-auto mb-3 opacity-40" />
            <p>Chưa có tin nhắn nào</p>
            <p className="text-sm mt-1">Hãy gửi tin nhắn đầu tiên!</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white rounded-br-none'
                  : 'bg-white shadow border border-gray-100 rounded-bl-none'
              }`}
            >
              {msg.type === 'image' && (() => {
                const url = msg.metadata?.imageUrl;
                return typeof url === 'string' && url ? (
                  <img
                    src={url}
                    alt="Ảnh đã gửi"
                    className="w-full h-48 object-cover rounded-lg mb-2"
                  />
                ) : null;
              })()}
              {msg.type === 'location' && (
                <div className="flex items-center gap-2 mb-2">
                  <MapPin size={16} />
                  <span className="text-sm">Đã gửi vị trí</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p
                className={`text-xs mt-1 ${
                  msg.role === 'user' ? 'text-emerald-100' : 'text-gray-400'
                }`}
              >
                {formatTime(msg.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white shadow border border-gray-100 rounded-2xl rounded-bl-none px-4 py-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                <span className="text-xs text-gray-400 ml-1">Đang nhập...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ---- Quick actions panel ---- */}
      {showQuickActions && (
        <div className="absolute bottom-20 left-4 right-4 bg-white rounded-xl shadow-lg border p-4 z-10">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold">Hành động nhanh</h3>
            <button
              onClick={() => setShowQuickActions(false)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action) => (
              <button
                key={action.id}
                onClick={action.action}
                className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                {action.icon}
                <span className="text-sm font-medium">{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ---- Product picker modal ---- */}
      {showProductPicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[80vh] overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="font-semibold">Chọn sản phẩm</h3>
              <button
                onClick={() => setShowProductPicker(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-96">
              <p className="text-gray-500 text-center py-8">
                Chức năng đang phát triển
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ---- Input bar ---- */}
      <div className="bg-white border-t border-gray-200 p-4 shrink-0">
        <div className="flex gap-2">
          <button
            onClick={() => setShowQuickActions(!showQuickActions)}
            className="p-3 bg-gray-100 rounded-full hover:bg-gray-200"
            aria-label="Hành động nhanh"
          >
            <Package className="w-5 h-5 text-gray-600" />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Nhập tin nhắn..."
            className="flex-1 px-4 py-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={connectionStatus !== 'connected'}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || connectionStatus !== 'connected'}
            className="p-3 bg-emerald-600 text-white rounded-full hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Gửi tin nhắn"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
