import {
  ChevronRight,
  Edit2,
  Heart,
  LogOut,
  MapPin,
  Save,
  ShoppingBag,
  User,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Form, FormCheckbox, FormField, FormSelect } from '../components/forms';
import { userProfileSchema, type UserProfileFormData } from '../lib/validations';

export default function UserProfilePage() {
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  const menuItems = [
    { icon: ShoppingBag, label: 'Don hang cua toi', href: '/orders', badge: null },
    { icon: Heart, label: 'San pham yeu thich', href: '#', badge: null },
    { icon: MapPin, label: 'Dia chi giao hang', href: '#', badge: null },
  ];

  const handleProfileUpdate = async (data: UserProfileFormData) => {
    setLoading(true);
    try {
      // TODO: Call API to update profile
      console.log('Updating profile:', data);
      // await api.put('/users/profile', data);
      setIsEditing(false);
    } catch (err) {
      alert('Cap nhat that bai, vui long thu lai!');
    } finally {
      setLoading(false);
    }
  };

  const defaultValues: Partial<UserProfileFormData> = {
    fullName: 'Nguoi dung',
    email: 'user@example.com',
    phone: '0123456789',
    language: 'vi',
    currency: 'VND',
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
  };

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
              <h1 className="text-xl font-bold">Nguoi dung</h1>
              <p className="text-blue-100">user@example.com</p>
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
          <h2 className="font-semibold mb-4">Chinh sua ho so</h2>
          <Form
            schema={userProfileSchema}
            defaultValues={defaultValues}
            onSubmit={handleProfileUpdate}
            className="space-y-4"
          >
            <FormField name="fullName" label="Ho ten" placeholder="Nhap ho ten cua ban" required />
            <FormField
              name="email"
              label="Email"
              type="email"
              placeholder="email@example.com"
              required
            />
            <FormField
              name="phone"
              label="So dien thoai"
              type="tel"
              placeholder="0xxxxxxxxx"
              required
            />
            <FormField name="address" label="Dia chi" placeholder="Nhap dia chi cua ban" />
            <div className="grid grid-cols-2 gap-4">
              <FormField name="city" label="Thanh pho" placeholder="TP Ho Chi Minh" />
              <FormField name="district" label="Quan/Huyen" placeholder="Quan 1" />
            </div>
            <FormField name="ward" label="Phuong/Xa" placeholder="Phuong Ben Nghe" />
            <div className="grid grid-cols-2 gap-4">
              <FormSelect
                name="language"
                label="Ngon ngu"
                options={[
                  { value: 'vi', label: 'Tieng Viet' },
                  { value: 'en', label: 'English' },
                ]}
              />
              <FormSelect
                name="currency"
                label="Don vi tien"
                options={[
                  { value: 'VND', label: 'VND' },
                  { value: 'USD', label: 'USD' },
                ]}
              />
            </div>
            <div className="space-y-3 pt-2">
              <p className="font-medium text-sm">Thong bao</p>
              <FormCheckbox name="emailNotifications" label="Nhan thong bao qua email" />
              <FormCheckbox name="smsNotifications" label="Nhan thong bao qua SMS" />
              <FormCheckbox name="pushNotifications" label="Nhan thong bao push" />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Dang luu...' : 'Luu thay doi'}
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
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {item.badge}
              </span>
            )}
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </Link>
        ))}
      </div>

      {/* Logout */}
      <button className="w-full mt-6 p-4 bg-red-50 text-red-600 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-red-100">
        <LogOut className="w-5 h-5" /> Dang xuat
      </button>
    </div>
  );
}
