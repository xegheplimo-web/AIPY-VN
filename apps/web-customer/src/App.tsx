import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/clerk-react';
import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';

const Home = lazy(() => import('./pages/Home'));
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

function Header() {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-blue-600">VietStore</h1>
          </div>
          <div className="flex items-center space-x-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700">
                  Sign In
                </button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Sign Up
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/store/:id" element={<StoreDetailPage />} />
          <Route path="/product/:id" element={<ProductDetailPage />} />
          <Route path="/orders" element={<OrderTrackingPage />} />
          <Route path="/profile" element={<UserProfilePage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/design" element={<DesignPage />} />
          <Route path="/locator" element={<StoreLocatorPage />} />
        </Routes>
        <Toaster position="top-right" richColors />
      </Suspense>
    </div>
  );
}
