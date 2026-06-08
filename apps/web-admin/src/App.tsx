import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

const AdminLoginPage = lazy(() => import('./pages/AdminLoginPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const StoresManagementPage = lazy(() => import('./pages/StoresManagementPage'));
const StoreVerificationPage = lazy(() => import('./pages/StoreVerificationPage'));
const MatchQueuePage = lazy(() => import('./pages/MatchQueuePage'));
const UserManagementPage = lazy(() => import('./pages/UserManagementPage'));
const ReportModerationPage = lazy(() => import('./pages/ReportModerationPage'));
const CategoryManagerPage = lazy(() => import('./pages/CategoryManagerPage'));
const SystemHealthPage = lazy(() => import('./pages/SystemHealthPage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={<AdminLoginPage />} />
          <Route path="/dashboard" element={<AdminDashboardPage />} />
          <Route path="/stores" element={<StoresManagementPage />} />
          <Route path="/stores/verification" element={<StoreVerificationPage />} />
          <Route path="/match-queue" element={<MatchQueuePage />} />
          <Route path="/users" element={<UserManagementPage />} />
          <Route path="/reports" element={<ReportModerationPage />} />
          <Route path="/categories" element={<CategoryManagerPage />} />
          <Route path="/system" element={<SystemHealthPage />} />
          <Route path="/" element={<AdminDashboardPage />} />
        </Routes>
      </Suspense>
    </AuthProvider>
  );
}
