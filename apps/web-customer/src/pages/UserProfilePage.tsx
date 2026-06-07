import { Link } from 'react-router-dom';
import { User, ShoppingBag, Heart, MapPin, LogOut, ChevronRight } from 'lucide-react';

export default function UserProfilePage() {
  const menuItems = [
    { icon: ShoppingBag, label: 'Don hang cua toi', href: '/orders', badge: null },
    { icon: Heart, label: 'San pham yeu thich', href: '#', badge: null },
    { icon: MapPin, label: 'Dia chi giao hang', href: '#', badge: null },
  ];

  return (
    <div className="max-w-lg mx-auto p-4 pb-8">
      {/* Profile Header */}
      <div className="bg-blue-600 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
            <User className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-xl font-bold">Nguoi dung</h1>
            <p className="text-blue-100">user@example.com</p>
          </div>
        </div>
      </div>

      {/* Menu */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {menuItems.map((item, idx) => (
          <Link
            key={idx}
            to={item.href}
            className="flex items-center gap-4 p-4 border-b last:border-0 hover:bg-gray-50"
          >
            <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
              <item.icon className="w-5 h-5 text-blue-600" />
            </div>
            <span className="flex-1 font-medium">{item.label}</span>
            {item.badge && (
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </Link>
        ))}
      </div>

      {/* Logout */}
      <button className="w-full mt-6 p-4 bg-red-50 text-red-600 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-red-100">
        <LogOut className="w-5 h-5" /> Dang xuat
      </button>
    </div>
  );
}
