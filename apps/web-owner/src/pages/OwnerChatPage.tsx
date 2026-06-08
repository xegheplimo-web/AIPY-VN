import { CheckCircle, MessageCircle, Phone, Search, Send, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import api from '../services/api';

interface Message {
  id: string;
  role: 'owner' | 'customer';
  content: string;
  timestamp: Date;
  customerName?: string;
  customerId?: string;
}

interface Customer {
  id: string;
  name: string;
  phone: string;
  lastMessage: string;
  lastTime: Date;
  unread: number;
  avatar?: string;
}

export default function OwnerChatPage() {
  const { customer_id } = useParams<{ customer_id: string }>();
  const navigate = useNavigate();
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCustomers();
  }, []);

  useEffect(() => {
    if (customer_id) {
      const customer = customers.find((c) => c.id === customer_id);
      if (customer) {
        setSelectedCustomer(customer);
        loadMessages(customer_id);
      }
    }
  }, [customer_id, customers]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      // TODO: Backend needs to add endpoint to get customers list
      // For now, we'll derive from orders or use a placeholder
      const response = await api.getOrders({ limit: 100 });

      // Extract unique customers from orders
      const customerMap = new Map<string, Customer>();
      response.orders.forEach((order: any) => {
        const customerId = order.customer_id || order.id;
        if (!customerMap.has(customerId)) {
          customerMap.set(customerId, {
            id: customerId,
            name: order.customer_name || order.customer || 'Unknown',
            phone: order.customer_phone || '',
            lastMessage: `Đơn hàng #${order.order_number || order.id}`,
            lastTime: new Date(order.created_at || Date.now()),
            unread: 0,
          });
        }
      });

      setCustomers(Array.from(customerMap.values()));
    } catch (err) {
      console.error('Failed to load customers:', err);
      toast.error('Không thể tải danh sách khách hàng');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (customerId: string) => {
    try {
      const response = await api.getChatMessages(customerId);

      // Transform API response to match interface
      const transformed = response.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.sender_id === customerId ? 'customer' : 'owner',
        content: msg.content,
        timestamp: new Date(msg.created_at),
        customerName: selectedCustomer?.name,
        customerId: customerId,
      }));

      setMessages(transformed);
    } catch (err) {
      console.error('Failed to load messages:', err);
      toast.error('Không thể tải tin nhắn');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedCustomer) return;

    const ownerMsg: Message = {
      id: Date.now().toString(),
      role: 'owner',
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, ownerMsg]);
    setInput('');

    try {
      await api.sendChatMessage(selectedCustomer.id, input);

      // Update last message in customer list
      setCustomers((prev) =>
        prev.map((c) =>
          c.id === selectedCustomer.id ? { ...c, lastMessage: input, lastTime: new Date() } : c
        )
      );
    } catch (err) {
      console.error('Failed to send message:', err);
      toast.error('Gửi tin nhắn thất bại');
      // Remove the message if failed
      setMessages((prev) => prev.slice(0, -1));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Customer List */}
      <div className="w-80 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-gray-900 mb-4">Tin nhắn</h1>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm kiếm khách hàng..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {customers.length === 0 ? (
            <div className="p-8 text-center">
              <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Chưa có khách hàng nào</p>
            </div>
          ) : (
            customers.map((customer) => (
              <div
                key={customer.id}
                onClick={() => {
                  setSelectedCustomer(customer);
                  navigate(`/chat/${customer.id}`);
                  loadMessages(customer.id);
                }}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition ${
                  selectedCustomer?.id === customer.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                    {customer.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900 truncate">{customer.name}</p>
                      <span className="text-xs text-gray-500">
                        {customer.lastTime.toLocaleTimeString('vi-VN', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 truncate">{customer.lastMessage}</p>
                  </div>
                  {customer.unread > 0 && (
                    <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs">
                      {customer.unread}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedCustomer ? (
          <>
            {/* Header */}
            <div className="p-4 bg-white border-b flex items-center justify-between">
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
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                  {selectedCustomer.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{selectedCustomer.name}</p>
                  <p className="text-sm text-gray-500">{selectedCustomer.phone}</p>
                </div>
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-lg" title="Gọi điện">
                <Phone className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <MessageCircle className="w-16 h-16 text-gray-300 mb-4" />
                  <p>Bắt đầu cuộc trò chuyện</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'owner' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-2xl px-4 py-2 ${
                        msg.role === 'owner' ? 'bg-blue-600 text-white' : 'bg-white border'
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                      <div
                        className={`flex items-center gap-1 mt-1 text-xs ${
                          msg.role === 'owner' ? 'text-blue-100' : 'text-gray-400'
                        }`}
                      >
                        <span>
                          {msg.timestamp.toLocaleTimeString('vi-VN', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        {msg.role === 'owner' && <CheckCircle className="w-3 h-3" />}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-white border-t">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
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
