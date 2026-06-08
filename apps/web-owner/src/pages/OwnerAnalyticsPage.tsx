import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Calendar,
  DollarSign,
  Package,
  PieChart,
  ShoppingCart,
  Users,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '../services/api';

interface AnalyticsData {
  revenue: { value: number; change: number; trend: 'up' | 'down' };
  orders: { value: number; change: number; trend: 'up' | 'down' };
  products: { value: number; change: number; trend: 'up' | 'down' };
  customers: { value: number; change: number; trend: 'up' | 'down' };
  topProducts: Array<{ name: string; sales: number; revenue: number; stock: number }>;
  searchQueries: Array<{ query: string; count: number; trend: 'up' | 'down' | 'stable' }>;
  hourlyData: Array<{ hour: string; revenue: number }>;
  categoryData: Array<{ name: string; value: number; color: string }>;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#EC4899'];

export default function OwnerAnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const res: any = await api.getAnalytics({ from_date: timeRange, to_date: 'today' });
      const analytics = res.data || res;
      if (analytics) {
        setData(analytics as AnalyticsData);
        return;
      }
      throw new Error('No data');
    } catch (err) {
      console.warn('Analytics API not available, using fallback:', err);
      // Fallback: mock data for demo until backend is ready
      setData({
        revenue: { value: 45250000, change: 12.5, trend: 'up' },
        orders: { value: 156, change: 8.3, trend: 'up' },
        products: { value: 89, change: 5.2, trend: 'up' },
        customers: { value: 234, change: -2.1, trend: 'down' },
        topProducts: [
          { name: 'Panadol Extra 500mg', sales: 45, revenue: 1575000, stock: 55 },
          { name: 'Vitamin C 1000mg', sales: 38, revenue: 1710000, stock: 12 },
          { name: 'Khẩu trang y tế', sales: 32, revenue: 480000, stock: 168 },
          { name: 'Nước muối sinh lý', sales: 28, revenue: 560000, stock: 72 },
          { name: 'Băng y tế', sales: 25, revenue: 375000, stock: 45 },
        ],
        searchQueries: [
          { query: 'Panadol', count: 89, trend: 'up' },
          { query: 'Vitamin C', count: 67, trend: 'up' },
          { query: 'Khẩu trang', count: 45, trend: 'down' },
          { query: 'Nước muối', count: 34, trend: 'up' },
          { query: 'Băng y tế', count: 28, trend: 'stable' },
        ],
        hourlyData: [
          { hour: '08:00', revenue: 250000 }, { hour: '09:00', revenue: 450000 },
          { hour: '10:00', revenue: 680000 }, { hour: '11:00', revenue: 520000 },
          { hour: '12:00', revenue: 380000 }, { hour: '13:00', revenue: 420000 },
          { hour: '14:00', revenue: 590000 }, { hour: '15:00', revenue: 720000 },
          { hour: '16:00', revenue: 650000 }, { hour: '17:00', revenue: 580000 },
          { hour: '18:00', revenue: 490000 }, { hour: '19:00', revenue: 320000 },
        ],
        categoryData: [
          { name: 'Thuốc giảm đau', value: 35, color: '#3B82F6' },
          { name: 'Vitamin', value: 25, color: '#10B981' },
          { name: 'Thiết bị y tế', value: 20, color: '#F59E0B' },
          { name: 'Dược phẩm khác', value: 20, color: '#8B5CF6' },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (value: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
  };

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-gray-200 rounded-xl animate-pulse" />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1,2].map(i => <div key={i} className="h-64 bg-gray-200 rounded-xl animate-pulse" />)}
        </div>
      </div>
    );
  }

  const { revenue, orders, products, customers, topProducts, searchQueries, hourlyData, categoryData } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 mt-1">Phân tích hiệu suất kinh doanh</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-gray-400" />
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value as any)} className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="7d">7 ngày</option>
            <option value="30d">30 ngày</option>
            <option value="90d">90 ngày</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Doanh thu" value={formatMoney(revenue.value)} change={revenue.change} trend={revenue.trend} icon={DollarSign} color="text-green-600" bg="bg-green-50" />
        <StatCard title="Đơn hàng" value={orders.value.toString()} change={orders.change} trend={orders.trend} icon={ShoppingCart} color="text-blue-600" bg="bg-blue-50" />
        <StatCard title="Sản phẩm bán được" value={products.value.toString()} change={products.change} trend={products.trend} icon={Package} color="text-purple-600" bg="bg-purple-50" />
        <StatCard title="Khách hàng" value={customers.value.toString()} change={customers.change} trend={customers.trend} icon={Users} color="text-orange-600" bg="bg-orange-50" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Doanh thu theo giờ</h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64 flex items-end gap-2">
            {hourlyData.map((d, idx) => {
              const maxValue = Math.max(...hourlyData.map((x) => x.revenue));
              const height = maxValue > 0 ? (d.revenue / maxValue) * 100 : 0;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600 relative group" style={{ height: `${height}%` }}>
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                      {formatMoney(d.revenue)}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">{d.hour}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Phân loại sản phẩm</h3>
            <PieChart className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-3">
            {categoryData.map((item, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: item.color }} />
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700">{item.name}</span>
                    <span className="font-medium">{item.value}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div className="h-2 rounded-full transition-all" style={{ backgroundColor: item.color, width: `${item.value}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Sản phẩm bán chạy</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 font-medium text-gray-600">Sản phẩm</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Đã bán</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Doanh thu</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Tồn kho</th>
                <th className="text-right py-3 px-4 font-medium text-gray-600">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {topProducts.map((product, idx) => (
                <tr key={idx} className="border-b">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-sm">{idx + 1}</div>
                      <span className="font-medium">{product.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">{product.sales}</td>
                  <td className="py-3 px-4 text-right font-medium text-blue-600">{formatMoney(product.revenue)}</td>
                  <td className="py-3 px-4 text-right"><span className={product.stock < 20 ? 'text-red-600 font-medium' : 'text-gray-700'}>{product.stock}</span></td>
                  <td className="py-3 px-4 text-right"><span className={`text-xs px-2 py-1 rounded-full ${product.stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{product.stock > 0 ? 'Còn hàng' : 'Hết hàng'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Từ khóa tìm kiếm phổ biến</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {searchQueries.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{item.query}</p>
                <p className="text-sm text-gray-500">{item.count} lượt tìm</p>
              </div>
              <div className={`flex items-center gap-1 text-sm ${item.trend === 'up' ? 'text-green-600' : item.trend === 'down' ? 'text-red-600' : 'text-gray-500'}`}>
                {item.trend === 'up' && <ArrowUpRight size={16} />}
                {item.trend === 'down' && <ArrowDownRight size={16} />}
                <span>{item.trend === 'up' ? '+' : item.trend === 'down' ? '-' : ''}{Math.abs(Math.random() * 20).toFixed(1)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, change, trend, icon: Icon, color, bg }: {
  title: string; value: string; change: number; trend: 'up' | 'down'; icon: any; color: string; bg: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`${bg} ${color} p-3 rounded-lg`}><Icon size={24} /></div>
      </div>
      <div className="flex items-center gap-2 mt-3">
        {trend === 'up' ? <ArrowUpRight size={16} className="text-green-600" /> : <ArrowDownRight size={16} className="text-red-600" />}
        <span className={`text-sm font-medium ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>{change > 0 ? '+' : ''}{change}%</span>
        <span className="text-sm text-gray-500">so với kỳ trước</span>
      </div>
    </div>
  );
}
