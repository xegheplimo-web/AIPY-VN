import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Bell, ShoppingCart, User, MapPin } from 'lucide-react';
import BottomNav from './BottomNav';

interface CustomerLayoutProps {
  children?: React.ReactNode;
}

export default function CustomerLayout({ children }: CustomerLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();

  const currentPath = location.pathname;
  const isHome = currentPath === '/';

  // Page titles
  const pageTitles: Record<string, string> = {
    '/': 'AI-SHOP.VN',
    '/cart': 'Giỏ hàng',
    '/checkout': 'Thanh toán',
    '/orders': 'Đơn hàng của tôi',
    '/profile': 'Tài khoản',
    '/search': 'Tìm kiếm',
  };

  const title = pageTitles[currentPath] || 'AI-SHOP.VN';

  // Show header on all pages except product detail and store detail
  const showHeader = !currentPath.startsWith('/store/') && !currentPath.startsWith('/product/');

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {showHeader && (
        <header className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
          <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {!isHome && (
                <button
                  onClick={() => navigate(-1)}
                  className="p-2 -ml-2 hover:bg-gray-100 rounded-full transition"
                  aria-label="Quay lại"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-700" />
                </button>
              )}
              <h1 className="text-lg font-bold text-blue-600">{title}</h1>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/cart')}
                className="p-2 hover:bg-gray-100 rounded-full transition relative"
                aria-label="Giỏ hàng"
              >
                <ShoppingCart className="w-5 h-5 text-gray-700" />
              </button>
              <button
                onClick={() => navigate('/profile')}
                className="p-2 hover:bg-gray-100 rounded-full transition"
                aria-label="Tài khoản"
              >
                <User className="w-5 h-5 text-gray-700" />
              </button>
              <button
                className="p-2 hover:bg-gray-100 rounded-full transition"
                aria-label="Thông báo"
              >
                <Bell className="w-5 h-5 text-gray-700" />
              </button>
            </div>
          </div>
        </header>
      )}

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          <Outlet />
        </div>
      </main>

      <BottomNav />
    </div>
  );
}
