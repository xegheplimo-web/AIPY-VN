import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package, Clock, CheckCircle, Truck, Home } from 'lucide-react';
import { apiService } from '../services/api';

interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

interface Order {
  id: string;
  order_number: string;
  store_id: string;
  delivery_method: string;
  subtotal: number;
  shipping_fee: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  status: string;
  items: OrderItem[];
  created_at: string;
}

const STATUS_STEPS = ['pending', 'confirmed', 'preparing', 'ready', 'completed'];
const STATUS_LABELS: Record<string, string> = {
  pending: 'Cho xac nhan',
  confirmed: 'Da xac nhan',
  preparing: 'Dang chuan bi',
  ready: 'San sang',
  completed: 'Hoan thanh',
  cancelled: 'Da huy',
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="w-5 h-5" />,
  confirmed: <CheckCircle className="w-5 h-5" />,
  preparing: <Package className="w-5 h-5" />,
  ready: <Truck className="w-5 h-5" />,
  completed: <Home className="w-5 h-5" />,
};

export default function OrderTrackingPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const res = await apiService.get('/users/me/orders?limit=50');
      setOrders(res.data.orders || []);
    } catch (err) {
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrders = filter === 'all'
    ? orders
    : orders.filter(o => o.status === filter);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto p-4 pb-8">
      <h1 className="text-xl font-bold mb-4">Don hang cua toi</h1>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
        {['all', 'pending', 'confirmed', 'preparing', 'completed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
              filter === status ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            {status === 'all' ? 'Tat ca' : STATUS_LABELS[status]}
          </button>
        ))}
      </div>

      {/* Orders List */}
      <div className="space-y-4">
        {filteredOrders.length === 0 && (
          <div className="text-center py-12">
            <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Chua co don hang nao</p>
            <Link to="/" className="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded-lg">
              Bat dau mua sam
            </Link>
          </div>
        )}

        {filteredOrders.map((order) => (
          <div key={order.id} className="bg-white rounded-xl shadow-sm border p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-bold">{order.order_number}</p>
                <p className="text-sm text-gray-500">
                  {new Date(order.created_at).toLocaleDateString('vi-VN')}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                order.status === 'completed' ? 'bg-green-100 text-green-700' :
                order.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {STATUS_LABELS[order.status] || order.status}
              </span>
            </div>

            {/* Status Timeline */}
            <div className="flex items-center gap-1 mb-3">
              {STATUS_STEPS.map((step, idx) => {
                const currentIdx = STATUS_STEPS.indexOf(order.status);
                const isActive = idx <= currentIdx;
                return (
                  <div key={step} className="flex-1 flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-400'
                    }`}>
                      {idx + 1}
                    </div>
                    <div className={`h-1 w-full mt-1 ${
                      idx < STATUS_STEPS.length - 1 ? (isActive ? 'bg-blue-600' : 'bg-gray-200') : ''
                    }`} />
                  </div>
                );
              })}
            </div>

            {/* Items */}
            <div className="space-y-2 mb-3">
              {order.items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm">
                  <span>{item.product_name} x{item.quantity}</span>
                  <span className="font-medium">{item.subtotal.toLocaleString('vi-VN')}đ</span>
                </div>
              ))}
            </div>

            {/* Total */}
            <div className="border-t pt-2 flex justify-between">
              <span className="text-gray-500">Tong cong</span>
              <span className="font-bold text-blue-600">{order.total_amount.toLocaleString('vi-VN')}đ</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
