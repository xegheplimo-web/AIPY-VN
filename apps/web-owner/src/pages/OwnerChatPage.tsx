import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Send, 
  Phone, 
  MessageCircle, 
  X, 
  ChevronRight,
  CheckCircle,
  Clock,
  Search,
  Filter
} from 'lucide-react';

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
      const customer = customers.find(c => c.id === customer_id);
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
      // Mock data - sẽ thay bằng API call sau
      const mockCustomers: Customer[] = [
        {
          id: '1',
          name: 'Nguyễn Văn A',
          phone: '0901234567',
          lastMessage: 'Cửa hàng còn Panadol không?',
          lastTime: new Date(Date.now() - 5 * 60000),
          unread: 2,
        },
        {
          id: '2',
          name: 'Trần Thị B',
          phone: '0912345678',
          lastMessage: 'Đơn hàng #12345 đã giao chưa?',
          lastTime: new Date(Date.now() - 30 * 60000),
          unread: 0,
        },
        {
          id: '3',
          name: 'Lê Văn C',
          phone: '0923456789',
          lastMessage: 'Cảm ơn shop!',
          lastTime: new Date(Date.now() - 2 * 3600000),
          unread: 0,
        },
      ];
      setCustomers(mockCustomers);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (customerId: string) => {
    try {
      // Mock messages
      const mockMessages: Message[] = [
        {
          id: '1',
          role: 'customer',
          content: 'Xin chào, cửa hàng còn Panadol Extra không?',
          timestamp: new Date(Date.now() - 10 * 60000),
          customerName: 'Nguyễn Văn A',
          customerId: customerId,
        },
        {
          id: '2',
          role: 'owner',
          content: 'Chào bạn, chúng tôi còn Panadol Extra 500mg, hiện có 55 hộp. Bạn cần bao nhiêu?',
          timestamp: new Date(Date.now() - 5 * 60000),
        },
        {
          id: '3',
          role: 'customer',
          content: 'Mình lấy 2 hộp nhé',
          timestamp: new Date(Date.now() - 2 * 60000),
          customerName: 'Nguyễn Văn A',
          customerId: customerId,
        },
      ];
      setMessages(mockMessages);
    } catch (err) {
      console.error('Failed to load messages:', err);
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

    // Update last message in customer list
    setCustomers((prev) =>
      prev.map((c) =>
        c.id === selectedCustomer.id
          ? { ...c, lastMessage: input, lastTime: new Date() }
          : c
      )
    );
  };

  const handleCallCustomer = () => {
    if (selectedCustomer?.phone) {
      window.location.href = `tel:${selectedCustomer.phone}`;
    }
  };

  const handleSelectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer);
    navigate(`/chat/${customer.id}`);
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
      {/* Customer List */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-lg font-bold mb-3">Tin nhắn</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm khách hàng..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {customers.map((customer) => (
            <div
              key={customer.id}
              onClick={() => handleSelectCustomer(customer)}
              className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition ${
                selectedCustomer?.id === customer.id ? 'bg-blue-50' : ''
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <MessageCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start">
                    <p className="font-medium text-gray-900 truncate">{customer.name}</p>
                    <span className="text-xs text-gray-500">
                      {customer.lastTime.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 truncate">{customer.lastMessage}</p>
                </div>
                {customer.unread > 0 && (
                  <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                    {customer.unread}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedCustomer ? (
          <>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
              <button onClick={() => navigate('/chat')} className="p-2 hover:bg-gray-100 rounded-full">
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <div className="flex-1 flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">{selectedCustomer.name}</h2>
                  <p className="text-xs text-gray-500">{selectedCustomer.phone}</p>
                </div>
              </div>
              <button
                onClick={handleCallCustomer}
                className="p-2 bg-green-50 text-green-600 rounded-full hover:bg-green-100"
              >
                <Phone className="w-5 h-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'owner' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                      msg.role === 'owner'
                        ? 'bg-blue-600 text-white rounded-br-none'
                        : 'bg-white shadow border border-gray-100 rounded-bl-none'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p className={`text-xs mt-1 ${msg.role === 'owner' ? 'text-blue-100' : 'text-gray-400'}`}>
                      {msg.timestamp.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 px-4 py-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageCircle className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Chọn khách hàng để bắt đầu chat</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
