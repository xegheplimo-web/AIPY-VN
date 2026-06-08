import { type ColumnDef } from '@tanstack/react-table';
import { Check, Truck, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { DataTable } from '../components/ui/DataTable';
import api from '../services/api';

interface Order {
  id: string;
  order_number: string;
  customer: string;
  total: string;
  status: string;
  date: string;
  items: string[];
}

const STATUS_TABS = ['all', 'pending', 'confirmed', 'preparing', 'ready', 'completed'];
const STATUS_LABELS: Record<string, string> = {
  all: 'Tất cả',
  pending: 'Chờ xác nhận',
  confirmed: 'Đã xác nhận',
  preparing: 'Đang chuẩn bị',
  ready: 'Sẵn sàng',
  completed: 'Hoàn thành',
};

export default function OwnerOrdersPage() {
  const [activeTab, setActiveTab] = useState('all');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, [activeTab]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (activeTab !== 'all') {
        params.status = activeTab;
      }
      const response = await api.getOrders(params);

      const transformed = (response.orders || []).map((order: any) => ({
        id: order.id,
        order_number: order.order_number || `ORD-${order.id}`,
        customer: order.customer_name || order.customer || 'Không rõ',
        total: order.total?.toLocaleString('vi-VN') || '0',
        status: order.status || 'pending',
        date: new Date(order.created_at || Date.now()).toLocaleDateString('vi-VN'),
        items: order.items?.map((item: any) => item.name || item.product_name) || [],
      }));

      setOrders(transformed);
    } catch (err) {
      console.error('Failed to load orders:', err);
      toast.error('Không thể tải danh sách đơn hàng');
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await api.updateOrderStatus(id, newStatus);
      toast.success('Đã cập nhật trạng thái đơn hàng');
      await loadOrders();
    } catch (err) {
      console.error('Failed to update order status:', err);
      toast.error('Cập nhật trạng thái thất bại');
    }
  };

  const filtered = activeTab === 'all' ? orders : orders.filter((o) => o.status === activeTab);

  const columns: ColumnDef<Order>[] = [
    {
      accessorKey: 'order_number',
      header: 'Mã đơn hàng',
      cell: ({ row }) => <div className="font-medium">{row.getValue('order_number')}</div>,
    },
    {
      accessorKey: 'customer',
      header: 'Khách hàng',
    },
    {
      accessorKey: 'date',
      header: 'Ngày đặt',
    },
    {
      accessorKey: 'items',
      header: 'Sản phẩm',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600 max-w-xs truncate">
          {row.getValue('items').join(', ')}
        </div>
      ),
    },
    {
      accessorKey: 'total',
      header: 'Tổng tiền',
      cell: ({ row }) => <div className="font-bold text-blue-600">{row.getValue('total')}đ</div>,
    },
    {
      accessorKey: 'status',
      header: 'Trạng thái',
      cell: ({ row }) => (
        <span
          className={`text-xs px-2 py-1 rounded-full ${
            row.getValue('status') === 'completed'
              ? 'bg-green-100 text-green-700'
              : row.getValue('status') === 'pending'
                ? 'bg-yellow-100 text-yellow-700'
                : row.getValue('status') === 'cancelled'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-blue-100 text-blue-700'
          }`}
        >
          {STATUS_LABELS[row.getValue('status')] || row.getValue('status')}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Hành động',
      cell: ({ row }) => {
        const status = row.getValue('status');
        return (
          <div className="flex gap-2">
            {status === 'pending' && (
              <>
                <button
                  onClick={() => updateStatus(row.original.id, 'confirmed')}
                  className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg flex items-center gap-1"
                >
                  <Check className="w-4 h-4" /> Chấp nhận
                </button>
                <button
                  onClick={() => updateStatus(row.original.id, 'cancelled')}
                  className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg flex items-center gap-1"
                >
                  <X className="w-4 h-4" /> Từ chối
                </button>
              </>
            )}
            {status === 'confirmed' && (
              <button
                onClick={() => updateStatus(row.original.id, 'preparing')}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg flex items-center gap-1"
              >
                <Truck className="w-4 h-4" /> Bắt đầu chuẩn bị
              </button>
            )}
            {status === 'preparing' && (
              <button
                onClick={() => updateStatus(row.original.id, 'ready')}
                className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg"
              >
                Sẵn sàng giao
              </button>
            )}
          </div>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen p-4 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Quản lý đơn hàng</h1>

        <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                activeTab === tab ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
              }`}
            >
              {STATUS_LABELS[tab]}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center border border-gray-200">
            <Truck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Không có đơn hàng</h3>
            <p className="text-gray-500">
              {activeTab === 'all'
                ? 'Chưa có đơn hàng nào'
                : `Không có đơn hàng ${STATUS_LABELS[activeTab]}`}
            </p>
          </div>
        ) : (
          <DataTable columns={columns} data={filtered} searchKey="order_number" />
        )}
      </div>
    </div>
  );
}
