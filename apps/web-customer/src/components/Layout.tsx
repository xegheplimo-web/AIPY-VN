import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Home, Search, ShoppingCart, ClipboardList, User } from 'lucide-react';
import Header from './Header';

const navItems = [
  { path: '/', label: 'Trang chủ', icon: Home },
  { path: '/search', label: 'Tìm kiếm', icon: Search },
  { path: '/cart', label: 'Giỏ hàng', icon: ShoppingCart },
  { path: '/orders', label: 'Đơn hàng', icon: ClipboardList },
  { path: '/profile', label: 'Tài khoản', icon: User },
];

const pageTitles: Record<string, string> = {
  '/': 'VietStore',
  '/cart': 'Giỏ hàng',
  '/checkout': 'Thanh toán',
  '/orders': 'Đơn hàng của tôi',
  '/profile': 'Tài khoản',
};

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const currentPath = location.pathname;
  const title = pageTitles[currentPath];

  const showHeader = !currentPath.startsWith('/store/') && !currentPath.startsWith('/product/');
  const showNav = !currentPath.startsWith('/checkout') && !currentPath.startsWith('/product/') && !currentPath.startsWith('/store/');

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {showHeader && <Header title={title} showBack={currentPath !== '/'} />}

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          <Outlet />
        </div>
      </main>

      {showNav && (
        <nav className="sticky bottom-0 bg-white border-t border-gray-100 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
          <div className="max-w-3xl mx-auto px-2 h-16 flex items-center justify-around">
            {navItems.map((item) => {
              const isActive = currentPath === item.path || (item.path !== '/' && currentPath.startsWith(item.path));
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition ${
                    isActive ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
