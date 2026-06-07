import { useState, useEffect } from 'react';
import { Bell, BellOff, Check, X } from 'lucide-react';
import { requestNotificationPermission, onMessageListener } from '../lib/firebase';
import api from '../services/api';

interface NotificationToast {
  id: string;
  title: string;
  body: string;
  data?: any;
}

export function NotificationManager() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [enabled, setEnabled] = useState(false);
  const [toasts, setToasts] = useState<NotificationToast[]>([]);

  useEffect(() => {
    // Check current permission
    setPermission(Notification.permission);
  }, []);

  const enableNotifications = async () => {
    try {
      const token = await requestNotificationPermission();
      
      if (token) {
        // Register token with backend
        await api.post('/notifications/register', {
          token,
          platform: 'web',
        });
        
        setEnabled(true);
        setPermission('granted');
      }
    } catch (error) {
      console.error('Failed to enable notifications:', error);
    }
  };

  const disableNotifications = () => {
    setEnabled(false);
    // Note: We can't actually revoke permission via API
    // This just disables the feature in the UI
  };

  // Listen for incoming messages
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = onMessageListener((payload) => {
      const notification: NotificationToast = {
        id: Date.now().toString(),
        title: payload.notification?.title || 'Thông báo',
        body: payload.notification?.body || '',
        data: payload.data,
      };
      
      setToasts((prev) => [...prev, notification]);
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== notification.id));
      }, 5000);
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [enabled]);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <>
      {/* Notification Toggle Button */}
      <button
        onClick={enabled ? disableNotifications : enableNotifications}
        className="p-2 rounded-full hover:bg-gray-100 transition-colors"
        title={enabled ? 'Tắt thông báo' : 'Bật thông báo'}
      >
        {enabled ? (
          <Bell className="w-5 h-5 text-blue-600" />
        ) : (
          <BellOff className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {/* Notification Toasts */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 max-w-sm animate-slide-in"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-semibold text-sm">{toast.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{toast.body}</p>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
