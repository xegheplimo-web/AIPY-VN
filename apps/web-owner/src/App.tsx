import { Route, Routes } from 'react-router-dom';
import OwnerLayout from './components/layout/OwnerLayout';
import BulkUploadPage from './pages/BulkUploadPage';
import OwnerAnalyticsPage from './pages/OwnerAnalyticsPage';
import OwnerChatPage from './pages/OwnerChatPage';
import OwnerDashboardPage from './pages/OwnerDashboardPage';
import OwnerLoginPage from './pages/OwnerLoginPage';
import OwnerOrdersPage from './pages/OwnerOrdersPage';
import ProductManagementPage from './pages/ProductManagementPage';
import PromotionsPage from './pages/PromotionsPage';
import StoreRegistrationPage from './pages/StoreRegistrationPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<OwnerLoginPage />} />
      <Route path="/register" element={<StoreRegistrationPage />} />
      <Route path="/" element={<OwnerLayout />}>
        <Route index element={<OwnerDashboardPage />} />
        <Route path="dashboard" element={<OwnerDashboardPage />} />
        <Route path="analytics" element={<OwnerAnalyticsPage />} />
        <Route path="chat" element={<OwnerChatPage />} />
        <Route path="chat/:customer_id" element={<OwnerChatPage />} />
        <Route path="products" element={<ProductManagementPage />} />
        <Route path="products/bulk-upload" element={<BulkUploadPage />} />
        <Route path="orders" element={<OwnerOrdersPage />} />
        <Route path="promotions" element={<PromotionsPage />} />
      </Route>
    </Routes>
  );
}
