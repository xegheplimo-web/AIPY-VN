import { Link } from 'react-router-dom';
import { Package, ShoppingCart, DollarSign, Star, TrendingUp } from 'lucide-react';

export default function OwnerDashboardPage() {
  const stats = [
    { icon: Package, label: 'Tong san pham', value: '45', trend: '+3' },
    { icon: ShoppingCart, label: 'Don cho xu ly', value: '12', trend: '+2' },
    { icon: DollarSign, label: 'Doanh thu thang', value: '15.2M', trend: '+15%' },
    { icon: Star, label: 'Danh gia TB', value: '4.8', trend: '+0.2' },
  ];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {stats.map((stat, idx) => (
            <div key={idx} className="bg-white rounded-xl p-4 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <stat.icon className="w-5 h-5 text-blue-600" />
                <span className="text-xs text-green-600 font-medium">{stat.trend}</span>
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
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
            <Link to="/orders" className="text-blue-600 text-sm hover:underline">Xem tat ca</Link>
          </div>
          <div className="divide-y">
            {[
              { id: 'ORD-2024-00001', customer: 'Nguyen Van A', total: '350,000', status: 'pending' },
              { id: 'ORD-2024-00002', customer: 'Tran Thi B', total: '125,000', status: 'confirmed' },
            ].map((order) => (
              <div key={order.id} className="p-4 flex justify-between items-center">
                <div>
                  <p className="font-medium">{order.id}</p>
                  <p className="text-sm text-gray-500">{order.customer}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{order.total}đ</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    order.status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
