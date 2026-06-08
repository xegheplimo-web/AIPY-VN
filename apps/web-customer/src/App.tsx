import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import CustomerLayout from './components/layout/CustomerLayout';

const Home = lazy(() => import('./pages/Home'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const CartPage = lazy(() => import('./pages/CartPage'));
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'));
const OrderTrackingPage = lazy(() => import('./pages/OrderTrackingPage'));
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'));
const StoreDetailPage = lazy(() => import('./pages/StoreDetailPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));
const DemoPage = lazy(() => import('./pages/DemoPage'));
const DesignPage = lazy(() => import('./pages/DesignPage'));
const StoreLocatorPage = lazy(() => import('./pages/StoreLocatorPage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<CustomerLayout />}>
            <Route index element={<Home />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="cart" element={<CartPage />} />
            <Route path="checkout" element={<CheckoutPage />} />
            <Route path="store/:id" element={<StoreDetailPage />} />
            <Route path="product/:id" element={<ProductDetailPage />} />
            <Route path="orders" element={<OrderTrackingPage />} />
            <Route path="profile" element={<UserProfilePage />} />
            <Route path="demo" element={<DemoPage />} />
            <Route path="design" element={<DesignPage />} />
            <Route path="locator" element={<StoreLocatorPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster position="top-right" richColors />
      </Suspense>
    </div>
  );
}
