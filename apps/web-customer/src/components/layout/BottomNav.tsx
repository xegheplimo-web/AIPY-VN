import { Home, Search, Bot, Package, ShoppingCart } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

type NavItem = {
  path: string;
  icon: React.ReactNode;
  label: string;
};

const navItems: NavItem[] = [
  { path: '/', icon: <Home size={18} />, label: 'Trang chủ' },
  { path: '/search', icon: <Search size={18} />, label: 'Tìm kiếm' },
  { path: '/chat', icon: <Bot size={22} />, label: 'Chat AI' },
  { path: '/orders', icon: <Package size={18} />, label: 'Đơn hàng' },
  { path: '/cart', icon: <ShoppingCart size={18} />, label: 'Giỏ hàng' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  const currentPath = location.pathname;

  // Hide on checkout, product detail, store detail pages
  const hideNav = currentPath.startsWith('/checkout') || 
                  currentPath.startsWith('/product/') || 
                  currentPath.startsWith('/store/');

  if (hideNav) return null;

  return (
    <nav className="sticky bottom-0 bg-white border-t border-gray-100 shadow-[0_-2px_10px_rgba(0,0,0,0.05)] z-50">
      <div className="max-w-3xl mx-auto px-2 h-16 flex items-center justify-around">
        {navItems.map((item) => {
          const isActive = currentPath === item.path || 
                          (item.path !== '/' && currentPath.startsWith(item.path));
          
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition ${
                isActive 
                  ? 'text-blue-600' 
                  : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              {item.icon}
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
