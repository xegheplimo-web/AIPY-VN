import {
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Clock,
  Home,
  MapPin,
  MessageCircle,
  Package,
  Phone,
  Truck,
  User,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/api';

interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  product_image?: string;
}

interface Store {
  id: string;
  name: string;
  address: string;
  phone: string;
  latitude: number;
  longitude: number;
}

interface Shipper {
  id: string;
  name: string;
  phone: string;
  avatar?: string;
  vehicle?: string;
}

interface Order {
  id: string;
  order_number: string;
  store: Store;
  delivery_method: 'pickup' | 'delivery';
  subtotal: number;
  shipping_fee: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  status: string;
  items: OrderItem[];
  created_at: string;
  estimated_delivery?: string;
  shipper?: Shipper;
  shipping_address?: string;
  notes?: string;
}

interface StatusStep {
  key: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const STATUS_STEPS: StatusStep[] = [
  { key: 'pending', label: 'Chờ xác nhận', icon: <Clock className="w-5 h-5" />, description: 'Đơn hàng đang chờ cửa hàng xác nhận' },
  { key: 'confirmed', label: 'Đã xác nhận', icon: <CheckCircle className="w-5 h-5" />, description: 'Cửa hàng đã xác nhận đơn hàng' },
  { key: 'preparing', label: 'Đang chuẩn bị', icon: <Package className="w-5 h-5" />, description: 'Đơn hàng đang được chuẩn bị' },
  { key: 'shipping', label: 'Đang giao', icon: <Truck className="w-5 h-5" />, description: 'Shipper đang giao hàng' },
  { key: 'completed', label: 'Hoàn tất', icon: <Home className="w-5 h-5" />, description: 'Đơn hàng đã hoàn tất' },
];

const STATUS_LABELS: Record<string, string> = {
  pending: 'Chờ xác nhận',
  confirmed: 'Đã xác nhận',
  preparing: 'Đang chuẩn bị',
  ready: 'Sẵn sàng',
  shipping: 'Đang giao',
  completed: 'Hoàn tất',
  cancelled: 'Đã hủy',
};

export default function OrderTrackingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    if (id) loadOrder(id);
  }, [id]);

  const loadOrder = async (orderId: string) => {
    try {
      const data = await apiService.getOrder(orderId);
      // Handle both wrapped and unwrapped responses
      const orderData = (data as any)?.data || data;
      setOrder(orderData as Order);
    } catch (err) {
      console.error('Failed to load order:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async () => {
    if (!order?.id || !confirm('Bạn có chắc chắn muốn hủy đơn hàng này?')) return;

    setCancelling(true);
    try {
      await apiService.cancelOrder(order.id);
      if (order) loadOrder(order.id);
    } catch (err) {
      alert('Hủy đơn hàng thất bại');
    } finally {
      setCancelling(false);
    }
  };

  const handleCallStore = () => {
    if (order?.store.phone) {
      window.location.href = `tel:${order.store.phone}`;
    }
  };

  const handleChatStore = () => {
    if (order) {
      navigate(`/chat?store_id=${order.store.id}`);
    }
  };

  const handleCallShipper = () => {
    if (order?.shipper?.phone) {
      window.location.href = `tel:${order.shipper.phone}`;
    }
  };

  const getCurrentStepIndex = () => {
    if (!order) return -1;
    return STATUS_STEPS.findIndex((step) => step.key === order.status);
  };

  const canCancel = order && (order.status === 'pending' || order.status === 'confirmed');

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!order) {
    return (
      <div className="max-w-lg mx-auto p-4 text-center">
        <AlertCircle className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h2 className="text-xl font-semibold text-gray-700">Không tìm thấy đơn hàng</h2>
        <Link to="/orders" className="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded-lg">
          Xem đơn hàng của bạn
        </Link>
      </div>
    );
  }

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="max-w-lg mx-auto p-4 pb-32">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/orders" className="p-2 hover:bg-gray-100 rounded-full">
          <ChevronRight className="w-5 h-5 rotate-180" />
        </Link>
        <h1 className="text-xl font-bold">Chi tiết đơn hàng</h1>
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="font-bold text-lg">{order.order_number}</p>
            <p className="text-sm text-gray-500">{new Date(order.created_at).toLocaleString('vi-VN')}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            order.status === 'completed' ? 'bg-green-100 text-green-700' : order.status === 'cancelled' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
          }`}>
            {STATUS_LABELS[order.status] || order.status}
          </span>
        </div>

        <div className="space-y-4">
          {STATUS_STEPS.map((step, idx) => {
            const isActive = idx <= currentStepIndex;
            const isCurrent = idx === currentStepIndex;
            return (
              <div key={step.key} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-400'} ${isCurrent ? 'ring-4 ring-blue-100' : ''}`}>
                    {isActive ? step.icon : <span className="text-sm">{idx + 1}</span>}
                  </div>
                  {idx < STATUS_STEPS.length - 1 && <div className={`w-0.5 h-8 mt-2 ${isActive ? 'bg-blue-600' : 'bg-gray-200'}`} />}
                </div>
                <div className="flex-1 pb-4">
                  <p className={`font-medium ${isActive ? 'text-gray-900' : 'text-gray-400'}`}>{step.label}</p>
                  <p className={`text-sm ${isActive ? 'text-gray-600' : 'text-gray-400'}`}>{step.description}</p>
                  {isCurrent && order.estimated_delivery && <p className="text-sm text-blue-600 mt-1">Dự kiến: {order.estimated_delivery}</p>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {order.status === 'shipping' && order.shipper && (
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><Truck className="w-5 h-5 text-blue-600" /> Thông tin shipper</h3>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center"><User className="w-6 h-6 text-blue-600" /></div>
            <div className="flex-1">
              <p className="font-medium">{order.shipper.name}</p>
              <p className="text-sm text-gray-500">{order.shipper.vehicle || 'Xe máy'}</p>
            </div>
            <button onClick={handleCallShipper} className="p-3 bg-green-50 text-green-600 rounded-full hover:bg-green-100"><Phone className="w-5 h-5" /></button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2"><Package className="w-5 h-5 text-blue-600" /> Cửa hàng</h3>
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0"><Package className="w-5 h-5 text-blue-600" /></div>
          <div className="flex-1">
            <p className="font-medium">{order.store.name}</p>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-1"><MapPin size={14} /> {order.store.address}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCallStore} className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100" title="Gọi cửa hàng"><Phone className="w-4 h-4" /></button>
            <button onClick={handleChatStore} className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100" title="Chat với cửa hàng"><MessageCircle className="w-4 h-4" /></button>
          </div>
        </div>
      </div>

      {order.delivery_method === 'delivery' && order.shipping_address && (
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><MapPin className="w-5 h-5 text-blue-600" /> Địa chỉ giao hàng</h3>
          <p className="text-gray-700">{order.shipping_address}</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
        <h3 className="font-semibold mb-3">Sản phẩm ({order.items.length})</h3>
        <div className="space-y-3">
          {order.items.map((item) => (
            <div key={item.id} className="flex gap-3">
              <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                {item.product_image ? <img src={item.product_image} alt={item.product_name} className="w-full h-full object-cover rounded-lg" /> : <Package className="w-6 h-6 text-gray-400" />}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{item.product_name}</p>
                <p className="text-sm text-gray-500">x{item.quantity}</p>
              </div>
              <p className="font-medium text-blue-600">{item.subtotal.toLocaleString('vi-VN')}đ</p>
            </div>
          ))}
        </div>
      </div>

      {order.notes && (
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
          <h3 className="font-semibold mb-2">Ghi chú</h3>
          <p className="text-gray-600 text-sm">{order.notes}</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-4">
        <h3 className="font-semibold mb-3">Thông tin thanh toán</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Phương thức</span>
            <span className="font-medium">
              {order.payment_method === 'cod' ? 'Thanh toán khi nhận hàng' : order.payment_method === 'momo' ? 'Ví MoMo' : order.payment_method === 'zalopay' ? 'ZaloPay' : 'Thẻ'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Trạng thái</span>
            <span className={`font-medium ${order.payment_status === 'paid' ? 'text-green-600' : 'text-orange-600'}`}>
              {order.payment_status === 'paid' ? 'Đã thanh toán' : 'Chưa thanh toán'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 rounded-xl p-4 border border-blue-200 mb-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm"><span className="text-gray-600">Tạm tính</span><span>{order.subtotal.toLocaleString('vi-VN')}đ</span></div>
          <div className="flex justify-between text-sm"><span className="text-gray-600">Phí ship</span><span>{order.shipping_fee === 0 ? 'Miễn phí' : `${order.shipping_fee.toLocaleString('vi-VN')}đ`}</span></div>
          <div className="flex justify-between text-lg font-bold pt-2 border-t border-blue-200"><span>Tổng cộng</span><span className="text-blue-600">{order.total_amount.toLocaleString('vi-VN')}đ</span></div>
        </div>
      </div>

      <div className="space-y-3">
        {canCancel && (
          <button onClick={handleCancelOrder} disabled={cancelling} className="w-full py-3 border border-red-300 text-red-600 rounded-xl font-medium hover:bg-red-50 disabled:opacity-50">
            {cancelling ? 'Đang hủy...' : 'Hủy đơn hàng'}
          </button>
        )}
        <Link to="/" className="block w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 text-center">Tiếp tục mua sắm</Link>
      </div>
    </div>
  );
}
