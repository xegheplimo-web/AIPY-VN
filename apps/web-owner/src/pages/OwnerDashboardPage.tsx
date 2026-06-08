import { DollarSign, Package, ShoppingCart, Star } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import StatCard from '../components/dashboard/StatCard';
import api from '../services/api';

interface DashboardStats {
  total_products: number;
  pending_orders: number;
  monthly_revenue: number;
  average_rating: number;
  recent_orders: Array<{
    id: string;
    order_number: string;
    customer: string;
    total: number;
    status: string;
  }>;
}

export default function OwnerDashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await api.getDashboardStats();
      setStats(response);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
      toast.error('Không thể tải thống kê dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-4 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const statCards = stats
    ? [
        {
          icon: Package,
          label: 'Tong san pham',
          value: stats.total_products.toString(),
          trend: '',
        },
        {
          icon: ShoppingCart,
          label: 'Don cho xu ly',
          value: stats.pending_orders.toString(),
          trend: '',
        },
        {
          icon: DollarSign,
          label: 'Doanh thu thang',
          value: `${(stats.monthly_revenue / 1000000).toFixed(1)}M`,
          trend: '',
        },
        {
          icon: Star,
          label: 'Danh gia TB',
          value: stats.average_rating.toFixed(1),
          trend: '',
        },
      ]
    : [];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {statCards.map((stat, idx) => (
            <StatCard
              key={idx}
              icon={stat.icon}
              label={stat.label}
              value={stat.value}
              trend={stat.trend}
            />
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <Link to="/products" className="p-6 bg-blue-50 rounded-xl hover:bg-blue-100 text-center">
            <Package className="w-8 h-8 mx-auto text-blue-600 mb-2" />
            <p className="font-medium text-blue-900">Quan ly san pham</p>
          </Link>
          <Link to="/orders" className="p-6 bg-green-50 rounded-xl hover:bg-green-100 text-center">
            <ShoppingCart className="w-8 h-8 mx-auto text-green-600 mb-2" />
            <p className="font-medium text-green-900">Quan ly don hang</p>
          </Link>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold">Don hang gan day</h2>
            <Link to="/orders" className="text-blue-600 text-sm hover:underline">
              Xem tat ca
            </Link>
          </div>
          {stats && stats.recent_orders.length > 0 ? (
            <div className="divide-y">
              {stats.recent_orders.map((order) => (
                <div key={order.id} className="p-4 flex justify-between items-center">
                  <div>
                    <p className="font-medium">{order.order_number}</p>
                    <p className="text-sm text-gray-500">{order.customer}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{order.total.toLocaleString('vi-VN')}đ</p>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        order.status === 'confirmed' || order.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : order.status === 'cancelled'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {order.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <ShoppingCart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Không có đơn hàng</h3>
              <p className="text-gray-500">Chưa có đơn hàng nào gần đây</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
