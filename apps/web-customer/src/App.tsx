import { Route, Routes } from 'react-router-dom';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import Home from './pages/Home';
import OrderTrackingPage from './pages/OrderTrackingPage';
import ProductDetailPage from './pages/ProductDetailPage';
import StoreDetailPage from './pages/StoreDetailPage';
import UserProfilePage from './pages/UserProfilePage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/cart" element={<CartPage />} />
      <Route path="/checkout" element={<CheckoutPage />} />
      <Route path="/store/:id" element={<StoreDetailPage />} />
      <Route path="/product/:id" element={<ProductDetailPage />} />
      <Route path="/orders" element={<OrderTrackingPage />} />
      <Route path="/profile" element={<UserProfilePage />} />
    </Routes>
  );
}
