import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';

const AdminLoginPage = lazy(() => import('./pages/AdminLoginPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const StoresManagementPage = lazy(() => import('./pages/StoresManagementPage'));
const MatchQueuePage = lazy(() => import('./pages/MatchQueuePage'));
const UserManagementPage = lazy(() => import('./pages/UserManagementPage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/login" element={<AdminLoginPage />} />
        <Route path="/dashboard" element={<AdminDashboardPage />} />
        <Route path="/stores" element={<StoresManagementPage />} />
        <Route path="/match-queue" element={<MatchQueuePage />} />
        <Route path="/users" element={<UserManagementPage />} />
        <Route path="/" element={<AdminDashboardPage />} />
      </Routes>
    </Suspense>
  );
}
