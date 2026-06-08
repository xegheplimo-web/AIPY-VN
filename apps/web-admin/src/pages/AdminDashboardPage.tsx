import { Link } from 'react-router-dom';
import { Store, Package, Users, ShoppingBag, TrendingUp, Activity, AlertTriangle, Clock } from 'lucide-react';
import { useEffect, useState } from 'react';
import apiService from '../services/api';
import { toast } from 'sonner';

interface AdminStats {
  total_users: number;
  total_stores: number;
  total_products: number;
  total_orders: number;
  total_revenue: number;
  pending_stores: number;
  pending_reports: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getDashboardStats();
      setStats({
        total_users: data.total_users ?? 0,
        total_stores: data.total_stores ?? 0,
        total_products: data.total_products ?? 0,
        total_orders: data.total_orders ?? 0,
        total_revenue: data.total_revenue ?? 0,
        pending_stores: data.pending_stores ?? 0,
        pending_reports: data.pending_reports ?? 0,
      });
    } catch (err) {
      console.error('Failed to load admin dashboard stats:', err);
      setError('Không thể tải thống kê. Vui lòng thử lại sau.');
      toast.error('Không thể tải thống kê');
      setStats({
        total_users: 0,
        total_stores: 0,
        total_products: 0,
        total_orders: 0,
        total_revenue: 0,
        pending_stores: 0,
        pending_reports: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString('vi-VN');
  };

  const statCards = stats
    ? [
        { icon: Store, label: 'Cửa hàng', value: formatNumber(stats.total_stores), color: 'bg-blue-100 text-blue-600' },
        { icon: Package, label: 'Sản phẩm', value: formatNumber(stats.total_products), color: 'bg-green-100 text-green-600' },
        { icon: Users, label: 'Người dùng', value: formatNumber(stats.total_users), color: 'bg-purple-100 text-purple-600' },
        { icon: ShoppingBag, label: 'Đơn hàng', value: formatNumber(stats.total_orders), color: 'bg-orange-100 text-orange-600' },
      ]
    : [];

  const quickActions = [
    { to: '/stores', icon: Store, title: 'Quản lý cửa hàng', desc: 'Duyệt, khóa, xem chi tiết cửa hàng', color: 'text-blue-600', badge: stats?.pending_stores ? `${stats.pending_stores} chờ duyệt` : undefined },
    { to: '/match-queue', icon: TrendingUp, title: 'Match Queue', desc: 'Đối soát dữ liệu store + seed', color: 'text-green-600' },
    { to: '/users', icon: Users, title: 'Quản lý người dùng', desc: 'Phân quyền, khóa, ban', color: 'text-purple-600' },
    { to: '/reports', icon: AlertTriangle, title: 'Báo cáo vi phạm', desc: 'Xử lý báo cáo từ người dùng', color: 'text-red-600', badge: stats?.pending_reports ? `${stats.pending_reports} chờ xử lý` : undefined },
    { to: '/categories', icon: Package, title: 'Quản lý danh mục', desc: 'Thêm, sửa, xóa danh mục sản phẩm', color: 'text-yellow-600' },
    { to: '/system', icon: Activity, title: 'Sức khỏe hệ thống', desc: 'Kiểm tra API, DB, cache', color: 'text-gray-600' },
  ];

  if (loading) {
    return (
      <div className="min-h-screen p-4">
        <div className="max-w-6xl mx-auto">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-6" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-28 bg-gray-200 rounded-xl animate-pulse" />)}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => <div key={i} className="h-32 bg-gray-200 rounded-xl animate-pulse" />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {new Date().toLocaleString('vi-VN')}
            </div>
            {stats && stats.pending_stores > 0 && (
              <Link to="/stores" className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg text-sm font-medium hover:bg-yellow-200">
                {stats.pending_stores} cửa hàng chờ duyệt
              </Link>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-700 text-sm">{error}</p>
            <button onClick={loadDashboardStats} className="mt-2 text-sm text-red-600 underline hover:text-red-800">Thử lại</button>
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {statCards.map((stat, idx) => (
            <div key={idx} className="bg-white rounded-xl p-6 shadow-sm border">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link key={action.to} to={action.to} className="p-6 bg-white rounded-xl shadow-sm border hover:border-blue-300 transition group">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <action.icon className={`w-8 h-8 ${action.color} group-hover:scale-110 transition`} />
                  <div>
                    <h3 className="font-bold">{action.title}</h3>
                    <p className="text-sm text-gray-500">{action.desc}</p>
                  </div>
                </div>
                {action.badge && <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">{action.badge}</span>}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
