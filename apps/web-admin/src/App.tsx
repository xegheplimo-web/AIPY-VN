import { Routes, Route } from 'react-router-dom';
import AdminLoginPage from './pages/AdminLoginPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import StoresManagementPage from './pages/StoresManagementPage';
import MatchQueuePage from './pages/MatchQueuePage';
import UserManagementPage from './pages/UserManagementPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AdminLoginPage />} />
      <Route path="/dashboard" element={<AdminDashboardPage />} />
      <Route path="/stores" element={<StoresManagementPage />} />
      <Route path="/match-queue" element={<MatchQueuePage />} />
      <Route path="/users" element={<UserManagementPage />} />
      <Route path="/" element={<AdminDashboardPage />} />
    </Routes>
  );
}
