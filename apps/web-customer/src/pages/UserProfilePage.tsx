import { ChevronRight, Edit2, Heart, LogOut, MapPin, Save, ShoppingBag, User, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Form, FormCheckbox, FormField, FormSelect } from '../components/forms';
import { userProfileSchema, type UserProfileFormData } from '../lib/validations';
import { apiService } from '../services/api';
import type { User } from '../services/api';

export default function UserProfilePage() {
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setFetching(true);
      const data = await apiService.getProfile();
      setUser(data);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setFetching(false);
    }
  };

  const menuItems = [
    { icon: ShoppingBag, label: 'Đơn hàng của tôi', href: '/orders', badge: null },
    { icon: Heart, label: 'Sản phẩm yêu thích', href: '#', badge: null },
    { icon: MapPin, label: 'Địa chỉ giao hàng', href: '#', badge: null },
  ];

  const handleProfileUpdate = async (data: UserProfileFormData) => {
    setLoading(true);
    try {
      await apiService.updateProfile({
        name: data.fullName,
        phone: data.phone,
      });
      setIsEditing(false);
      await loadProfile();
    } catch (err: any) {
      alert(err.message || 'Cập nhật thất bại, vui lòng thử lại!');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiService.logout();
    window.location.href = '/';
  };

  const defaultValues: Partial<UserProfileFormData> = {
    fullName: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    language: 'vi',
    currency: 'VND',
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
  };

  if (fetching) {
    return (
      <div className="max-w-lg mx-auto p-4 pb-8">
        <div className="h-32 bg-gray-100 rounded-2xl animate-pulse mb-6" />
        <div className="h-40 bg-gray-100 rounded-xl animate-pulse mb-6" />
        <div className="h-48 bg-gray-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto p-4 pb-8">
      {/* Profile Header */}
      <div className="bg-blue-600 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-xl font-bold">{user?.name || 'Người dùng'}</h1>
              <p className="text-blue-100">{user?.email || 'Chưa cập nhật email'}</p>
            </div>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-2 bg-white/20 rounded-full hover:bg-white/30"
          >
            {isEditing ? <X className="w-5 h-5" /> : <Edit2 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Edit Profile Form */}
      {isEditing && (
        <div className="bg-white rounded-xl p-4 shadow-sm mb-6">
          <h2 className="font-semibold mb-4">Chỉnh sửa hồ sơ</h2>
          <Form
            schema={userProfileSchema}
            defaultValues={defaultValues}
            onSubmit={handleProfileUpdate}
            className="space-y-4"
          >
            <FormField name="fullName" label="Họ tên" placeholder="Nhập họ tên của bạn" required />
            <FormField name="email" label="Email" type="email" placeholder="email@example.com" required />
            <FormField name="phone" label="Số điện thoại" type="tel" placeholder="0xxxxxxxxx" required />
            <FormField name="address" label="Địa chỉ" placeholder="Nhập địa chỉ của bạn" />
            <div className="grid grid-cols-2 gap-4">
              <FormField name="city" label="Thành phố" placeholder="TP. Hồ Chí Minh" />
              <FormField name="district" label="Quận/Huyện" placeholder="Quận 1" />
            </div>
            <FormField name="ward" label="Phường/Xã" placeholder="Phường Bến Nghé" />
            <div className="grid grid-cols-2 gap-4">
              <FormSelect
                name="language"
                label="Ngôn ngữ"
                options={[
                  { value: 'vi', label: 'Tiếng Việt' },
                  { value: 'en', label: 'English' },
                ]}
              />
              <FormSelect
                name="currency"
                label="Đơn vị tiền"
                options={[
                  { value: 'VND', label: 'VND' },
                  { value: 'USD', label: 'USD' },
                ]}
              />
            </div>
            <div className="space-y-3 pt-2">
              <p className="font-medium text-sm">Thông báo</p>
              <FormCheckbox name="emailNotifications" label="Nhận thông báo qua email" />
              <FormCheckbox name="smsNotifications" label="Nhận thông báo qua SMS" />
              <FormCheckbox name="pushNotifications" label="Nhận thông báo push" />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </Form>
        </div>
      )}

      {/* Menu */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {menuItems.map((item, idx) => (
          <Link
            key={idx}
            to={item.href}
            className="flex items-center gap-4 p-4 border-b last:border-0 hover:bg-gray-50"
          >
            <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
              <item.icon className="w-5 h-5 text-blue-600" />
            </div>
            <span className="flex-1 font-medium">{item.label}</span>
            {item.badge && (
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{item.badge}</span>
            )}
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </Link>
        ))}
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full mt-6 p-4 bg-red-50 text-red-600 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-red-100"
      >
        <LogOut className="w-5 h-5" /> Đăng xuất
      </button>
    </div>
  );
}
