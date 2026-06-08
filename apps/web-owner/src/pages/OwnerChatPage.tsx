import {
  AlertCircle,
  CheckCircle,
  Loader2,
  MessageCircle,
  Phone,
  RefreshCw,
  Search,
  Send,
  Wifi,
  WifiOff,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import api from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: string;
  role: 'owner' | 'customer';
  content: string;
  timestamp: Date;
}

interface Customer {
  id: string;
  name: string;
  phone: string;
  lastMessage: string;
  lastTime: Date;
  unread: number;
}

type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function wsBaseUrl(): string {
  const apiBase = (import.meta as any).env?.VITE_API_URL || 'http://localhost:9000';
  return apiBase.replace(/^http/, 'ws');
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(date: Date): string {
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OwnerChatPage() {
  const { customer_id } = useParams<{ customer_id: string }>();
  const navigate = useNavigate();

  // Data state
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  // UI state
  const [customersLoading, setCustomersLoading] = useState(true);
  const [customersError, setCustomersError] = useState<string | null>(null);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // WebSocket state
  const [wsStatus, setWsStatus] = useState<WsStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const customerIdRef = useRef<string | null>(null);

  // Keep ref in sync so WebSocket callbacks always see the latest value
  useEffect(() => {
    customerIdRef.current = selectedCustomer?.id ?? null;
  }, [selectedCustomer]);

  // -----------------------------------------------------------------------
  // 1. Load customers from orders
  // -----------------------------------------------------------------------

  const loadCustomers = useCallback(async () => {
    try {
      setCustomersLoading(true);
      setCustomersError(null);

      const response = await api.getOrders({ limit: 200 } as any);
      const orders = response.orders || [];

      const customerMap = new Map<string, Customer>();
      orders.forEach((order: any) => {
        const cid = order.customer_id || order.user_id || order.id;
        if (!customerMap.has(cid)) {
          customerMap.set(cid, {
            id: cid,
            name: order.customer_name || order.customer || order.user_name || 'Khách hàng',
            phone: order.customer_phone || order.phone || '',
            lastMessage: `Đơn hàng #${order.order_number || order.id?.toString().slice(0, 8)}`,
            lastTime: new Date(order.created_at || Date.now()),
            unread: 0,
          });
        } else {
          // Update if this order is newer
          const existing = customerMap.get(cid)!;
          const orderTime = new Date(order.created_at || Date.now());
          if (orderTime > existing.lastTime) {
            existing.lastMessage = `Đơn hàng #${order.order_number || order.id?.toString().slice(0, 8)}`;
            existing.lastTime = orderTime;
          }
        }
      });

      const list = Array.from(customerMap.values()).sort(
        (a, b) => b.lastTime.getTime() - a.lastTime.getTime()
      );
      setCustomers(list);
    } catch (err: any) {
      console.error('Failed to load customers:', err);
      setCustomersError(err.message || 'Không thể tải danh sách khách hàng');
      toast.error('Không thể tải danh sách khách hàng');
    } finally {
      setCustomersLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCustomers();
  }, [loadCustomers]);

  // -----------------------------------------------------------------------
  // 2. Select customer from URL param
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (customer_id && customers.length > 0) {
      const found = customers.find((c) => c.id === customer_id);
      if (found) {
        setSelectedCustomer(found);
      }
    }
  }, [customer_id, customers]);

  // -----------------------------------------------------------------------
  // 3. Load chat history via REST
  // -----------------------------------------------------------------------

  const loadMessages = useCallback(async (customerId: string) => {
    try {
      setMessagesLoading(true);
      setMessagesError(null);
      const storeId = localStorage.getItem('store_id') || localStorage.getItem('owner_store_id') || '';
      const response: any = await api.get<any>(`/api/stores/${storeId}/messages`);
      const raw = response?.messages || response?.data?.messages || [];

      const transformed: Message[] = raw.map((msg: any) => ({
        id: msg.id,
        role: msg.sender_id === customerId ? 'customer' : 'owner',
        content: msg.content,
        timestamp: new Date(msg.created_at || Date.now()),
      }));

      setMessages(transformed);
    } catch (err: any) {
      console.error('Failed to load messages:', err);
      setMessagesError(err.message || 'Không thể tải tin nhắn');
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCustomer) {
      loadMessages(selectedCustomer.id);
    } else {
      setMessages([]);
    }
  }, [selectedCustomer, loadMessages]);

  // -----------------------------------------------------------------------
  // 4. WebSocket connection
  // -----------------------------------------------------------------------

  const connectWs = useCallback(
    (roomId: string) => {
      // Close previous connection
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          /* ignore */
        }
        wsRef.current = null;
      }

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      const token = api.getToken();
      if (!token) {
        setWsStatus('error');
        return;
      }

      const url = `${wsBaseUrl()}/ws/chat/${roomId}?token=${encodeURIComponent(token)}`;
      setWsStatus('connecting');

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'new_message' && data.message) {
            const msg = data.message;
            const currentCid = customerIdRef.current;
            const isIncoming = msg.sender_id !== currentCid && msg.sender_id !== 'owner';
            const role: 'owner' | 'customer' = isIncoming ? 'customer' : 'owner';

            setMessages((prev) => {
              if (prev.some((m) => m.id === msg.id)) return prev;
              return [
                ...prev,
                {
                  id: msg.id,
                  role,
                  content: msg.content,
                  timestamp: new Date(msg.created_at || Date.now()),
                },
              ];
            });

            // Update customer lastMessage
            if (isIncoming) {
              setCustomers((prev) =>
                prev.map((c) =>
                  c.id === msg.sender_id
                    ? { ...c, lastMessage: msg.content, lastTime: new Date(msg.created_at || Date.now()), unread: c.unread + 1 }
                    : c
                )
              );
            }
          }
        } catch (e) {
          console.warn('Failed to parse WS message:', e);
        }
      };

      ws.onerror = () => {
        setWsStatus('error');
      };

      ws.onclose = () => {
        setWsStatus('disconnected');
        // Auto-reconnect after 3s if customer still selected
        if (customerIdRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            if (customerIdRef.current) {
              connectWs(customerIdRef.current);
            }
          }, 3000);
        }
      };
    },
    []
  );

  // Connect when customer changes
  useEffect(() => {
    if (selectedCustomer) {
      connectWs(selectedCustomer.id);
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setWsStatus('disconnected');
    }

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [selectedCustomer, connectWs]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // -----------------------------------------------------------------------
  // 5. Send message via WebSocket
  // -----------------------------------------------------------------------

  const handleSend = () => {
    if (!input.trim() || !selectedCustomer) return;

    const content = input.trim();

    // Optimistic add
    const optimisticMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'owner',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);
    setInput('');

    // Send via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content,
          receiver_id: selectedCustomer.id,
        })
      );

      // Update customer lastMessage
      setCustomers((prev) =>
        prev.map((c) =>
          c.id === selectedCustomer.id
            ? { ...c, lastMessage: content, lastTime: new Date() }
            : c
        )
      );
    } else {
      // Fallback: send via REST
      api
        .sendChatMessage(selectedCustomer.id, content)
        .then(() => {
          setCustomers((prev) =>
            prev.map((c) =>
              c.id === selectedCustomer.id
                ? { ...c, lastMessage: content, lastTime: new Date() }
                : c
            )
          );
        })
        .catch((err) => {
          console.error('Failed to send message via REST:', err);
          toast.error('Gửi tin nhắn thất bại');
          // Remove optimistic message
          setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
        });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // -----------------------------------------------------------------------
  // 6. Auto-scroll
  // -----------------------------------------------------------------------

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // -----------------------------------------------------------------------
  // Render helpers
  // -----------------------------------------------------------------------

  const filteredCustomers = customers.filter(
    (c) =>
      !searchQuery ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.phone.includes(searchQuery)
  );

  const wsStatusBadge = () => {
    switch (wsStatus) {
      case 'connected':
        return (
          <span className="inline-flex items-center gap-1 text-xs text-green-600">
            <Wifi className="w-3 h-3" /> Đã kết nối
          </span>
        );
      case 'connecting':
        return (
          <span className="inline-flex items-center gap-1 text-xs text-yellow-600">
            <Loader2 className="w-3 h-3 animate-spin" /> Đang kết nối...
          </span>
        );
      case 'disconnected':
        return (
          <span className="inline-flex items-center gap-1 text-xs text-gray-400">
            <WifiOff className="w-3 h-3" /> Ngắt kết nối
          </span>
        );
      case 'error':
        return (
          <span className="inline-flex items-center gap-1 text-xs text-red-500">
            <AlertCircle className="w-3 h-3" /> Lỗi kết nối
          </span>
        );
    }
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  if (customersLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Đang tải danh sách khách hàng...</span>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* ---------------------------------------------------------------- */}
      {/* Sidebar – Customer list                                         */}
      {/* ---------------------------------------------------------------- */}
      <div className="w-80 bg-white border-r flex flex-col shrink-0">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-gray-900">Tin nhắn</h1>
            <button
              onClick={loadCustomers}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition"
              title="Tải lại"
            >
              <RefreshCw className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm khách hàng..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
        </div>

        {/* Error */}
        {customersError && (
          <div className="p-3 bg-red-50 border-b text-sm text-red-600 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <div className="flex-1">
              <p>{customersError}</p>
              <button
                onClick={loadCustomers}
                className="text-red-700 underline text-xs mt-1 hover:no-underline"
              >
                Thử lại
              </button>
            </div>
          </div>
        )}

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {filteredCustomers.length === 0 ? (
            <div className="p-8 text-center">
              <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {customers.length === 0
                  ? 'Chưa có khách hàng nào'
                  : 'Không tìm thấy khách hàng'}
              </p>
            </div>
          ) : (
            filteredCustomers.map((customer) => (
              <div
                key={customer.id}
                onClick={() => {
                  setSelectedCustomer(customer);
                  navigate(`/chat/${customer.id}`);
                }}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition ${
                  selectedCustomer?.id === customer.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold shrink-0">
                    {customer.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900 truncate">{customer.name}</p>
                      <span className="text-xs text-gray-500 shrink-0 ml-2">
                        {formatTime(customer.lastTime)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 truncate">{customer.lastMessage}</p>
                  </div>
                  {customer.unread > 0 && (
                    <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs shrink-0">
                      {customer.unread}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ---------------------------------------------------------------- */}
      {/* Main chat area                                                   */}
      {/* ---------------------------------------------------------------- */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedCustomer ? (
          <>
            {/* Header */}
            <div className="p-4 bg-white border-b flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    setSelectedCustomer(null);
                    navigate('/chat');
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg lg:hidden"
                >
                  <X className="w-5 h-5" />
                </button>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold shrink-0">
                  {selectedCustomer.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{selectedCustomer.name}</p>
                  <p className="text-sm text-gray-500">{selectedCustomer.phone}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {wsStatusBadge()}
                <button
                  className="p-2 hover:bg-gray-100 rounded-lg"
                  title="Gọi điện"
                  onClick={() => {
                    if (selectedCustomer.phone) {
                      window.location.href = `tel:${selectedCustomer.phone}`;
                    }
                  }}
                >
                  <Phone className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messagesLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                  <span className="ml-2 text-gray-500">Đang tải tin nhắn...</span>
                </div>
              ) : messagesError ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <AlertCircle className="w-12 h-12 text-red-300 mb-3" />
                  <p className="text-red-600 mb-2">{messagesError}</p>
                  <button
                    onClick={() => loadMessages(selectedCustomer.id)}
                    className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Thử lại
                  </button>
                </div>
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <MessageCircle className="w-16 h-16 text-gray-300 mb-4" />
                  <p>Bắt đầu cuộc trò chuyện</p>
                </div>
              ) : (
                messages.map((msg, idx) => {
                  const isOwner = msg.role === 'owner';
                  const showDate =
                    idx === 0 ||
                    formatDate(messages[idx - 1].timestamp) !== formatDate(msg.timestamp);

                  return (
                    <div key={msg.id}>
                      {showDate && (
                        <div className="flex items-center justify-center my-2">
                          <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
                            {formatDate(msg.timestamp)}
                          </span>
                        </div>
                      )}
                      <div className={`flex ${isOwner ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[70%] rounded-2xl px-4 py-2.5 ${
                            isOwner
                              ? 'bg-blue-600 text-white rounded-br-none'
                              : 'bg-white border border-gray-200 rounded-bl-none'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                          <div
                            className={`flex items-center gap-1 mt-1 text-xs ${
                              isOwner ? 'text-blue-100' : 'text-gray-400'
                            }`}
                          >
                            <span>{formatTime(msg.timestamp)}</span>
                            {isOwner && <CheckCircle className="w-3 h-3" />}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-white border-t shrink-0">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Nhập tin nhắn..."
                  disabled={wsStatus === 'error'}
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || wsStatus === 'error'}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageCircle className="w-24 h-24 text-gray-300 mx-auto mb-4" />
              <h2 className="text-xl font-medium text-gray-900 mb-2">Chọn một cuộc trò chuyện</h2>
              <p className="text-gray-500">Chọn khách hàng từ danh sách để bắt đầu chat</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
