import {
  Calendar,
  CheckCircle,
  Clock,
  Edit2,
  Plus,
  Search,
  Tag,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '../services/api';

interface Promotion {
  id: string;
  code: string;
  name: string;
  type: 'percentage' | 'fixed' | 'free_shipping';
  value: number;
  minOrder: number;
  maxDiscount?: number;
  startDate: Date;
  endDate: Date;
  usageLimit?: number;
  usedCount: number;
  status: 'active' | 'expired' | 'scheduled' | 'paused';
  applicableStores: string[];
}

export default function PromotionsPage() {
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState<Promotion | null>(null);
  const [form, setForm] = useState({
    code: '',
    name: '',
    type: 'percentage' as 'percentage' | 'fixed' | 'free_shipping',
    value: '',
    minOrder: '',
    maxDiscount: '',
    startDate: '',
    endDate: '',
    usageLimit: '',
  });

  useEffect(() => {
    loadPromotions();
  }, []);

  const loadPromotions = async () => {
    try {
      setLoading(true);
      const response = await api.getPromotions({ limit: 100 });

      // Transform API response to match interface
      const transformed = response.promotions.map((promo: any) => ({
        id: promo.id,
        code: promo.code,
        name: promo.name,
        type: promo.type,
        value: promo.value,
        minOrder: promo.min_order || 0,
        maxDiscount: promo.max_discount,
        startDate: new Date(promo.start_date),
        endDate: new Date(promo.end_date),
        usageLimit: promo.usage_limit,
        usedCount: promo.used_count || 0,
        status: promo.status,
        applicableStores: promo.applicable_stores || ['all'],
      }));

      setPromotions(transformed);
    } catch (err) {
      console.error('Failed to load promotions:', err);
      toast.error('Không thể tải danh sách khuyến mãi');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      const data = {
        code: form.code,
        name: form.name,
        type: form.type,
        value: parseFloat(form.value),
        min_order: parseFloat(form.minOrder) || 0,
        max_discount: form.maxDiscount ? parseFloat(form.maxDiscount) : undefined,
        start_date: form.startDate,
        end_date: form.endDate,
        usage_limit: form.usageLimit ? parseInt(form.usageLimit) : undefined,
        applicable_stores: ['all'],
      };

      await api.createPromotion(data);
      toast.success('Đã tạo khuyến mãi thành công');
      setShowAddModal(false);
      setForm({
        code: '',
        name: '',
        type: 'percentage',
        value: '',
        minOrder: '',
        maxDiscount: '',
        startDate: '',
        endDate: '',
        usageLimit: '',
      });
      loadPromotions();
    } catch (err) {
      console.error('Failed to create promotion:', err);
      toast.error('Thêm khuyến mãi thất bại');
    }
  };

  const handleEdit = async () => {
    if (!editingPromotion) return;

    try {
      const data = {
        code: form.code,
        name: form.name,
        type: form.type,
        value: parseFloat(form.value),
        min_order: parseFloat(form.minOrder) || 0,
        max_discount: form.maxDiscount ? parseFloat(form.maxDiscount) : undefined,
        start_date: form.startDate,
        end_date: form.endDate,
        usage_limit: form.usageLimit ? parseInt(form.usageLimit) : undefined,
        applicable_stores: ['all'],
      };

      await api.updatePromotion(editingPromotion.id, data);
      toast.success('Đã cập nhật khuyến mãi thành công');
      setEditingPromotion(null);
      setForm({
        code: '',
        name: '',
        type: 'percentage',
        value: '',
        minOrder: '',
        maxDiscount: '',
        startDate: '',
        endDate: '',
        usageLimit: '',
      });
      loadPromotions();
    } catch (err) {
      console.error('Failed to update promotion:', err);
      toast.error('Cập nhật khuyến mãi thất bại');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa khuyến mãi này?')) return;
    try {
      await api.deletePromotion(id);
      toast.success('Đã xóa khuyến mãi thành công');
      loadPromotions();
    } catch (err) {
      console.error('Failed to delete promotion:', err);
      toast.error('Xóa khuyến mãi thất bại');
    }
  };

  const handleToggleStatus = async (id: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'active' ? 'paused' : 'active';
      await api.updatePromotion(id, { status: newStatus });
      toast.success('Đã thay đổi trạng thái khuyến mãi');
      loadPromotions();
    } catch (err) {
      console.error('Failed to toggle promotion status:', err);
      toast.error('Thay đổi trạng thái thất bại');
    }
  };

  const filteredPromotions = promotions.filter(
    (p) =>
      p.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const config = {
      active: { label: 'Đang chạy', color: 'bg-green-100 text-green-700', icon: CheckCircle },
      expired: { label: 'Đã hết hạn', color: 'bg-gray-100 text-gray-700', icon: XCircle },
      scheduled: { label: 'Đã lên lịch', color: 'bg-blue-100 text-blue-700', icon: Calendar },
      paused: { label: 'Tạm dừng', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
    };
    const { label, color, icon: Icon } = config[status as keyof typeof config];
    return (
      <span
        className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${color}`}
      >
        <Icon size={12} /> {label}
      </span>
    );
  };

  const getTypeBadge = (type: string) => {
    const config = {
      percentage: { label: '%', color: 'bg-purple-100 text-purple-700' },
      fixed: { label: '₫', color: 'bg-blue-100 text-blue-700' },
      free_shipping: { label: 'Free Ship', color: 'bg-green-100 text-green-700' },
    };
    const { label, color } = config[type as keyof typeof config];
    return <span className={`px-2 py-1 rounded text-xs font-medium ${color}`}>{label}</span>;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Khuyến mãi & Giảm giá</h1>
          <p className="text-gray-500 mt-1">Quản lý mã giảm giá và chương trình khuyến mãi</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Tạo khuyến mãi
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm khuyến mãi..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Promotion List */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left py-3 px-4 font-medium text-gray-600">Mã</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Tên</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Loại</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Giá trị</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Sử dụng</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Thời gian</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Trạng thái</th>
              <th className="text-right py-3 px-4 font-medium text-gray-600">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredPromotions.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-12 text-gray-500">
                  <Tag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p>Không tìm thấy kết quả</p>
                </td>
              </tr>
            ) : (
              filteredPromotions.map((promo) => (
                <tr key={promo.id} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <span className="font-mono font-bold text-blue-600">{promo.code}</span>
                  </td>
                  <td className="py-4 px-4">
                    <p className="font-medium text-gray-900">{promo.name}</p>
                  </td>
                  <td className="py-4 px-4">{getTypeBadge(promo.type)}</td>
                  <td className="py-4 px-4">
                    {promo.type === 'percentage' && (
                      <span className="font-medium">{promo.value}%</span>
                    )}
                    {promo.type === 'fixed' && (
                      <span className="font-medium">{promo.value.toLocaleString('vi-VN')}đ</span>
                    )}
                    {promo.type === 'free_shipping' && (
                      <span className="font-medium text-green-600">Miễn phí</span>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <div className="text-sm">
                      <span className="font-medium">{promo.usedCount}</span>
                      {promo.usageLimit && (
                        <span className="text-gray-500"> / {promo.usageLimit}</span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4 text-sm text-gray-600">
                    <div>{promo.startDate.toLocaleDateString('vi-VN')}</div>
                    <div className="text-gray-400">
                      → {promo.endDate.toLocaleDateString('vi-VN')}
                    </div>
                  </td>
                  <td className="py-4 px-4">{getStatusBadge(promo.status)}</td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => handleToggleStatus(promo.id, promo.status)}
                        className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                        title={promo.status === 'active' ? 'Tạm dừng' : 'Kích hoạt'}
                      >
                        {promo.status === 'active' ? (
                          <Clock className="w-4 h-4" />
                        ) : (
                          <CheckCircle className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setEditingPromotion(promo);
                          setForm({
                            code: promo.code,
                            name: promo.name,
                            type: promo.type,
                            value: promo.value.toString(),
                            minOrder: promo.minOrder.toString(),
                            maxDiscount: promo.maxDiscount?.toString() || '',
                            startDate: promo.startDate.toISOString().split('T')[0],
                            endDate: promo.endDate.toISOString().split('T')[0],
                            usageLimit: promo.usageLimit?.toString() || '',
                          });
                        }}
                        className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                        title="Chỉnh sửa"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(promo.id)}
                        className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                        title="Xóa"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      {(showAddModal || editingPromotion) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold text-gray-900">
                {editingPromotion ? 'Chỉnh sửa khuyến mãi' : 'Tạo khuyến mãi mới'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mã khuyến mãi
                </label>
                <input
                  type="text"
                  value={form.code}
                  onChange={(e) => setForm({ ...form, code: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="GIAM50K"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tên khuyến mãi
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Giảm 50K cho đơn trên 300K"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Loại khuyến mãi
                </label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="percentage">Phần trăm (%)</option>
                  <option value="fixed">Cố định (₫)</option>
                  <option value="free_shipping">Miễn phí ship</option>
                </select>
              </div>
              {form.type !== 'free_shipping' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Giá trị {form.type === 'percentage' ? '(%)' : '(₫)'}
                    </label>
                    <input
                      type="number"
                      value={form.value}
                      onChange={(e) => setForm({ ...form, value: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder={form.type === 'percentage' ? '20' : '50000'}
                    />
                  </div>
                  {form.type === 'percentage' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Giảm tối đa (₫)
                      </label>
                      <input
                        type="number"
                        value={form.maxDiscount}
                        onChange={(e) => setForm({ ...form, maxDiscount: e.target.value })}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="200000"
                      />
                    </div>
                  )}
                </>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Đơn tối thiểu (₫)
                </label>
                <input
                  type="number"
                  value={form.minOrder}
                  onChange={(e) => setForm({ ...form, minOrder: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="300000"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ngày bắt đầu
                  </label>
                  <input
                    type="date"
                    value={form.startDate}
                    onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ngày kết thúc
                  </label>
                  <input
                    type="date"
                    value={form.endDate}
                    onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Giới hạn số lần sử dụng
                </label>
                <input
                  type="number"
                  value={form.usageLimit}
                  onChange={(e) => setForm({ ...form, usageLimit: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1000"
                />
              </div>
            </div>
            <div className="p-6 border-t flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setEditingPromotion(null);
                  setForm({
                    code: '',
                    name: '',
                    type: 'percentage',
                    value: '',
                    minOrder: '',
                    maxDiscount: '',
                    startDate: '',
                    endDate: '',
                    usageLimit: '',
                  });
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Hủy
              </button>
              <button
                onClick={editingPromotion ? handleEdit : handleAdd}
                className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
              >
                {editingPromotion ? 'Cập nhật' : 'Tạo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
