import { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit2, 
  Trash2, 
  Search, 
  Percent,
  Calendar,
  Tag,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';

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
      // Mock data - sẽ thay bằng API call sau
      const mockPromotions: Promotion[] = [
        {
          id: '1',
          code: 'GIAM50K',
          name: 'Giảm 50K cho đơn trên 300K',
          type: 'fixed',
          value: 50000,
          minOrder: 300000,
          maxDiscount: 50000,
          startDate: new Date('2024-01-01'),
          endDate: new Date('2024-12-31'),
          usageLimit: 1000,
          usedCount: 456,
          status: 'active',
          applicableStores: ['all'],
        },
        {
          id: '2',
          code: 'GIAM20%',
          name: 'Giảm 20% toàn bộ',
          type: 'percentage',
          value: 20,
          minOrder: 0,
          maxDiscount: 200000,
          startDate: new Date('2024-06-01'),
          endDate: new Date('2024-06-30'),
          usageLimit: 500,
          usedCount: 234,
          status: 'active',
          applicableStores: ['all'],
        },
        {
          id: '3',
          code: 'FREESHIP',
          name: 'Miễn phí ship',
          type: 'free_shipping',
          value: 0,
          minOrder: 200000,
          startDate: new Date('2024-01-01'),
          endDate: new Date('2024-12-31'),
          usageLimit: null,
          usedCount: 789,
          status: 'active',
          applicableStores: ['all'],
        },
        {
          id: '4',
          code: 'FLASHSALE',
          name: 'Flash sale 50%',
          type: 'percentage',
          value: 50,
          minOrder: 100000,
          maxDiscount: 500000,
          startDate: new Date('2024-07-01'),
          endDate: new Date('2024-07-07'),
          usageLimit: 200,
          usedCount: 0,
          status: 'scheduled',
          applicableStores: ['all'],
        },
      ];
      setPromotions(mockPromotions);
    } catch (err) {
      console.error('Failed to load promotions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      // Mock API call
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
      alert('Thêm khuyến mãi thất bại');
    }
  };

  const handleEdit = async () => {
    try {
      // Mock API call
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
      alert('Cập nhật khuyến mãi thất bại');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa khuyến mãi này?')) return;
    try {
      // Mock API call
      loadPromotions();
    } catch (err) {
      alert('Xóa khuyến mãi thất bại');
    }
  };

  const handleToggleStatus = async (id: string, currentStatus: string) => {
    try {
      setPromotions((prev) =>
        prev.map((p) =>
          p.id === id
            ? { ...p, status: currentStatus === 'active' ? 'paused' : 'active' as const }
            : p
        )
      );
    } catch (err) {
      alert('Thay đổi trạng thái thất bại');
    }
  };

  const filteredPromotions = promotions.filter((p) =>
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
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${color}`}>
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
                <td colSpan={9} className="text-center py-12 text-gray-500">
                  Không tìm thấy kết quả
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
                    <div className="text-gray-400">→ {promo.endDate.toLocaleDateString('vi-VN')}</div>
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

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Tạo khuyến mãi mới</h2>
            <div className="space-y-3">
              <input
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Mã khuyến mãi (VD: GIAM50K)"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Tên khuyến mãi"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as any })}
                className="w-full px-4 py-3 border rounded-lg"
              >
                <option value="percentage">Giảm theo %</option>
                <option value="fixed">Giảm theo số tiền</option>
                <option value="free_shipping">Miễn phí ship</option>
              </select>
              {form.type !== 'free_shipping' && (
                <>
                  <input
                    value={form.value}
                    onChange={(e) => setForm({ ...form, value: e.target.value })}
                    placeholder={form.type === 'percentage' ? 'Giảm % (VD: 20)' : 'Giảm số tiền (VD: 50000)'}
                    type="number"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                  {form.type === 'percentage' && (
                    <input
                      value={form.maxDiscount}
                      onChange={(e) => setForm({ ...form, maxDiscount: e.target.value })}
                      placeholder="Giảm tối đa (VD: 200000)"
                      type="number"
                      className="w-full px-4 py-3 border rounded-lg"
                    />
                  )}
                </>
              )}
              <input
                value={form.minOrder}
                onChange={(e) => setForm({ ...form, minOrder: e.target.value })}
                placeholder="Đơn tối thiểu (VD: 300000)"
                type="number"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Ngày bắt đầu</label>
                  <input
                    value={form.startDate}
                    onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                    type="date"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Ngày kết thúc</label>
                  <input
                    value={form.endDate}
                    onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                    type="date"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                </div>
              </div>
              <input
                value={form.usageLimit}
                onChange={(e) => setForm({ ...form, usageLimit: e.target.value })}
                placeholder="Giới hạn số lần sử dụng (để trống = vô hạn)"
                type="number"
                className="w-full px-4 py-3 border rounded-lg"
              />
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-3 border rounded-lg"
              >
                Hủy
              </button>
              <button onClick={handleAdd} className="flex-1 py-3 bg-blue-600 text-white rounded-lg">
                Tạo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingPromotion && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold mb-4">Chỉnh sửa khuyến mãi</h2>
            <div className="space-y-3">
              <input
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Mã khuyến mãi"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Tên khuyến mãi"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as any })}
                className="w-full px-4 py-3 border rounded-lg"
              >
                <option value="percentage">Giảm theo %</option>
                <option value="fixed">Giảm theo số tiền</option>
                <option value="free_shipping">Miễn phí ship</option>
              </select>
              {form.type !== 'free_shipping' && (
                <>
                  <input
                    value={form.value}
                    onChange={(e) => setForm({ ...form, value: e.target.value })}
                    placeholder="Giá trị"
                    type="number"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                  {form.type === 'percentage' && (
                    <input
                      value={form.maxDiscount}
                      onChange={(e) => setForm({ ...form, maxDiscount: e.target.value })}
                      placeholder="Giảm tối đa"
                      type="number"
                      className="w-full px-4 py-3 border rounded-lg"
                    />
                  )}
                </>
              )}
              <input
                value={form.minOrder}
                onChange={(e) => setForm({ ...form, minOrder: e.target.value })}
                placeholder="Đơn tối thiểu"
                type="number"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Ngày bắt đầu</label>
                  <input
                    value={form.startDate}
                    onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                    type="date"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-600 mb-1 block">Ngày kết thúc</label>
                  <input
                    value={form.endDate}
                    onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                    type="date"
                    className="w-full px-4 py-3 border rounded-lg"
                  />
                </div>
              </div>
              <input
                value={form.usageLimit}
                onChange={(e) => setForm({ ...form, usageLimit: e.target.value })}
                placeholder="Giới hạn số lần sử dụng"
                type="number"
                className="w-full px-4 py-3 border rounded-lg"
              />
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
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
                className="flex-1 py-3 border rounded-lg"
              >
                Hủy
              </button>
              <button onClick={handleEdit} className="flex-1 py-3 bg-blue-600 text-white rounded-lg">
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
