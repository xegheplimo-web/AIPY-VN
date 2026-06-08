import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  Calendar,
  DollarSign,
  Package,
  RefreshCw,
  ShoppingCart,
  Users,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { toast } from 'sonner';
import api from '../services/api';

// ---------------------------------------------------------------------------
// Types – flexible to handle whatever the API returns
// ---------------------------------------------------------------------------

interface StatValue {
  value: number;
  change?: number;
  trend?: 'up' | 'down';
}

interface TopProduct {
  name: string;
  sales: number;
  revenue: number;
  stock: number;
}

interface RevenuePoint {
  date: string;
  revenue: number;
}

interface StatusPoint {
  status: string;
  count: number;
}

interface CategoryPoint {
  name: string;
  value: number;
}

interface AnalyticsData {
  revenue?: StatValue;
  orders?: StatValue;
  products?: StatValue;
  customers?: StatValue;
  total_revenue?: number;
  total_orders?: number;
  total_products?: number;
  total_customers?: number;
  low_stock_count?: number;
  avg_order_value?: number;
  topProducts?: TopProduct[];
  revenueOverTime?: RevenuePoint[];
  ordersByStatus?: StatusPoint[];
  categoryData?: CategoryPoint[];
}

type TimeRange = '7d' | '30d' | '90d';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const COLORS = ['#2563eb', '#16a34a', '#eab308', '#9333ea', '#ef4444', '#ec4899', '#06b6d4', '#f97316'];

function formatMoney(value: number): string {
  if (value == null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number): string {
  if (value == null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('vi-VN').format(value);
}

function toDateRange(range: TimeRange): { from_date: string; to_date: string } {
  const now = new Date();
  const from = new Date();
  switch (range) {
    case '7d':
      from.setDate(now.getDate() - 7);
      break;
    case '30d':
      from.setDate(now.getDate() - 30);
      break;
    case '90d':
      from.setDate(now.getDate() - 90);
      break;
  }
  return {
    from_date: from.toISOString().split('T')[0],
    to_date: now.toISOString().split('T')[0],
  };
}

const statusLabelMap: Record<string, string> = {
  pending: 'Chờ xử lý',
  confirmed: 'Đã xác nhận',
  preparing: 'Đang chuẩn bị',
  delivering: 'Đang giao',
  delivered: 'Đã giao',
  completed: 'Hoàn thành',
  cancelled: 'Đã hủy',
  refunded: 'Đã hoàn',
};

// ---------------------------------------------------------------------------
// Skeleton components
// ---------------------------------------------------------------------------

function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-20 bg-gray-200 rounded mb-2" />
          <div className="h-8 w-28 bg-gray-200 rounded" />
        </div>
        <div className="w-12 h-12 bg-gray-200 rounded-lg" />
      </div>
      <div className="h-4 w-32 bg-gray-200 rounded mt-3" />
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 animate-pulse">
      <div className="h-5 w-40 bg-gray-200 rounded mb-6" />
      <div className="h-64 bg-gray-100 rounded" />
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded mb-6" />
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center gap-4 py-3 border-b last:border-b-0">
          <div className="w-8 h-8 bg-gray-200 rounded-full" />
          <div className="flex-1 h-4 bg-gray-200 rounded" />
          <div className="w-16 h-4 bg-gray-200 rounded" />
          <div className="w-20 h-4 bg-gray-200 rounded" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat Card
// ---------------------------------------------------------------------------

function StatCard({
  title,
  value,
  change,
  trend,
  icon: Icon,
  color,
  bg,
}: {
  title: string;
  value: string;
  change?: number;
  trend?: 'up' | 'down';
  icon: any;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`${bg} ${color} p-3 rounded-lg`}>
          <Icon size={24} />
        </div>
      </div>
      {change != null && trend != null && (
        <div className="flex items-center gap-2 mt-3">
          {trend === 'up' ? (
            <ArrowUpRight size={16} className="text-green-600" />
          ) : (
            <ArrowDownRight size={16} className="text-red-600" />
          )}
          <span className={`text-sm font-medium ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {change > 0 ? '+' : ''}
            {change}%
          </span>
          <span className="text-sm text-gray-500">so với kỳ trước</span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom tooltip for recharts
// ---------------------------------------------------------------------------

function MoneyTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="text-gray-600 mb-1">{label}</p>
      {payload.map((entry: any, idx: number) => (
        <p key={idx} className="font-medium" style={{ color: entry.color }}>
          {entry.name}: {formatMoney(entry.value)}
        </p>
      ))}
    </div>
  );
}

function CountTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="text-gray-600 mb-1">{label}</p>
      {payload.map((entry: any, idx: number) => (
        <p key={idx} className="font-medium" style={{ color: entry.color }}>
          {entry.name}: {formatNumber(entry.value)}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function OwnerAnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = toDateRange(timeRange);
      const res: any = await api.getAnalytics(params);
      const analytics = res?.data ?? res ?? {};

      // Validate that we got *something* useful
      if (typeof analytics === 'object' && analytics !== null) {
        setData(analytics as AnalyticsData);
      } else {
        throw new Error('Dữ liệu trả về không hợp lệ');
      }
    } catch (err: any) {
      console.error('Analytics API error:', err);
      setError(err.message || 'Không thể tải dữ liệu phân tích');
      toast.error('Không thể tải dữ liệu phân tích');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  // -----------------------------------------------------------------------
  // Derived / safe values – show N/A for anything missing
  // -----------------------------------------------------------------------

  const totalRevenue =
    data?.revenue?.value ?? data?.total_revenue ?? undefined;
  const totalOrders =
    data?.orders?.value ?? data?.total_orders ?? undefined;
  const totalCustomers =
    data?.customers?.value ?? data?.total_customers ?? undefined;
  const avgOrderValue =
    data?.avg_order_value ??
    (totalRevenue != null && totalOrders != null && totalOrders > 0
      ? totalRevenue / totalOrders
      : undefined);
  const revenueChange = data?.revenue?.change;
  const revenueTrend = data?.revenue?.trend;
  const ordersChange = data?.orders?.change;
  const ordersTrend = data?.orders?.trend;

  const revenueOverTime: RevenuePoint[] = data?.revenueOverTime ?? [];
  const ordersByStatus: StatusPoint[] = data?.ordersByStatus ?? [];
  const topProducts: TopProduct[] = data?.topProducts ?? [];
  const categoryData: CategoryPoint[] = data?.categoryData ?? [];

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Thống kê</h1>
          <p className="text-gray-500 mt-1">Phân tích hiệu suất kinh doanh</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-gray-400" />
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRange)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
          >
            <option value="7d">7 ngày</option>
            <option value="30d">30 ngày</option>
            <option value="90d">90 ngày</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-700 font-medium mb-1">Không thể tải dữ liệu</p>
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={loadAnalytics}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Thử lại
          </button>
        </div>
      )}

      {/* Stat Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Tổng doanh thu"
            value={totalRevenue != null ? formatMoney(totalRevenue) : 'N/A'}
            change={revenueChange}
            trend={revenueTrend}
            icon={DollarSign}
            color="text-green-600"
            bg="bg-green-50"
          />
          <StatCard
            title="Tổng đơn hàng"
            value={totalOrders != null ? formatNumber(totalOrders) : 'N/A'}
            change={ordersChange}
            trend={ordersTrend}
            icon={ShoppingCart}
            color="text-blue-600"
            bg="bg-blue-50"
          />
          <StatCard
            title="Giá trị trung bình"
            value={avgOrderValue != null ? formatMoney(avgOrderValue) : 'N/A'}
            icon={Package}
            color="text-purple-600"
            bg="bg-purple-50"
          />
          <StatCard
            title="Khách hàng"
            value={totalCustomers != null ? formatNumber(totalCustomers) : 'N/A'}
            change={data?.customers?.change}
            trend={data?.customers?.trend}
            icon={Users}
            color="text-orange-600"
            bg="bg-orange-50"
          />
        </div>
      )}

      {/* Charts row 1 */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Revenue over time */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Doanh thu theo thời gian</h3>
            {revenueOverTime.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={revenueOverTime}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                    tickFormatter={(v: number) =>
                      v >= 1_000_000
                        ? `${(v / 1_000_000).toFixed(1)}M`
                        : v >= 1_000
                          ? `${(v / 1_000).toFixed(0)}K`
                          : String(v)
                    }
                  />
                  <Tooltip content={<MoneyTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Doanh thu"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-gray-400">
                <p>Chưa có dữ liệu doanh thu</p>
              </div>
            )}
          </div>

          {/* Orders by status */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Đơn hàng theo trạng thái</h3>
            {ordersByStatus.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={ordersByStatus}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="status"
                    tick={{ fontSize: 11 }}
                    stroke="#9ca3af"
                    tickFormatter={(v: string) => statusLabelMap[v] ?? v}
                  />
                  <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                  <Tooltip
                    content={<CountTooltip />}
                    labelFormatter={(l: any) => statusLabelMap[l] ?? l}
                  />
                  <Bar dataKey="count" name="Số đơn" radius={[6, 6, 0, 0]}>
                    {ordersByStatus.map((_, idx) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-gray-400">
                <p>Chưa có dữ liệu đơn hàng</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Charts row 2 */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top products */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Sản phẩm bán chạy</h3>
            {topProducts.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={topProducts} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 11 }}
                    stroke="#9ca3af"
                    width={120}
                  />
                  <Tooltip content={<CountTooltip />} />
                  <Bar dataKey="sales" name="Đã bán" fill="#2563eb" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-gray-400">
                <p>Chưa có dữ liệu sản phẩm</p>
              </div>
            )}
          </div>

          {/* Category breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Phân loại sản phẩm</h3>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }: any) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={{ stroke: '#9ca3af' }}
                  >
                    {categoryData.map((_, idx) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: any) => [formatNumber(Number(value)), 'Số lượng']}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value: string) => <span className="text-sm text-gray-700">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-gray-400">
                <p>Chưa có dữ liệu phân loại</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top products table */}
      {loading ? (
        <TableSkeleton />
      ) : topProducts.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Chi tiết sản phẩm bán chạy</h3>
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
                  <tr key={idx} className="border-b last:border-b-0 hover:bg-gray-50 transition">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-sm">
                          {idx + 1}
                        </div>
                        <span className="font-medium">{product.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">{formatNumber(product.sales)}</td>
                    <td className="py-3 px-4 text-right font-medium text-blue-600">
                      {formatMoney(product.revenue)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={
                          product.stock < 20 ? 'text-red-600 font-medium' : 'text-gray-700'
                        }
                      >
                        {formatNumber(product.stock)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          product.stock > 0
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {product.stock > 0 ? 'Còn hàng' : 'Hết hàng'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Low stock warning */}
      {!loading && data?.low_stock_count != null && data.low_stock_count > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium text-yellow-800">
              {data.low_stock_count} sản phẩm sắp hết hàng
            </p>
            <p className="text-sm text-yellow-700 mt-0.5">
              Kiểm tra và nhập thêm hàng để tránh mất đơn
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
