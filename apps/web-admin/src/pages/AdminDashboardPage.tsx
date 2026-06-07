import { Link } from 'react-router-dom';
import { Store, Package, Users, ShoppingBag, TrendingUp } from 'lucide-react';

export default function AdminDashboardPage() {
  const stats = [
    { icon: Store, label: 'Cua hang', value: '12', color: 'bg-blue-100 text-blue-600' },
    { icon: Package, label: 'San pham', value: '245', color: 'bg-green-100 text-green-600' },
    { icon: Users, label: 'Nguoi dung', value: '1.2K', color: 'bg-purple-100 text-purple-600' },
    { icon: ShoppingBag, label: 'Don hang', value: '89', color: 'bg-orange-100 text-orange-600' },
  ];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {stats.map((stat, idx) => (
            <div key={idx} className="bg-white rounded-xl p-6 shadow-sm border">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/stores" className="p-6 bg-white rounded-xl shadow-sm border hover:border-blue-300">
            <Store className="w-8 h-8 text-blue-600 mb-3" />
            <h3 className="font-bold">Quan ly cua hang</h3>
            <p className="text-sm text-gray-500">Xem, duyet, khoa cua hang</p>
          </Link>
          <Link to="/match-queue" className="p-6 bg-white rounded-xl shadow-sm border hover:border-blue-300">
            <TrendingUp className="w-8 h-8 text-green-600 mb-3" />
            <h3 className="font-bold">Match Queue</h3>
            <p className="text-sm text-gray-500">Duyet khop store + seed data</p>
          </Link>
          <Link to="/users" className="p-6 bg-white rounded-xl shadow-sm border hover:border-blue-300">
            <Users className="w-8 h-8 text-purple-600 mb-3" />
            <h3 className="font-bold">Quan ly nguoi dung</h3>
            <p className="text-sm text-gray-500">Roles, ban, permissions</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
