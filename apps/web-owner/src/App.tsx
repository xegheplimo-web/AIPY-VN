import { Route, Routes } from 'react-router-dom';
import OwnerDashboardPage from './pages/OwnerDashboardPage';
import OwnerLoginPage from './pages/OwnerLoginPage';
import OwnerOrdersPage from './pages/OwnerOrdersPage';
import ProductManagementPage from './pages/ProductManagementPage';
import StoreRegistrationPage from './pages/StoreRegistrationPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<OwnerLoginPage />} />
      <Route path="/register" element={<StoreRegistrationPage />} />
      <Route path="/dashboard" element={<OwnerDashboardPage />} />
      <Route path="/products" element={<ProductManagementPage />} />
      <Route path="/orders" element={<OwnerOrdersPage />} />
      <Route path="/" element={<OwnerDashboardPage />} />
    </Routes>
  );
}
