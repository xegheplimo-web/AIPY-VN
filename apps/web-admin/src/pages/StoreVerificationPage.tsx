import {
  Building2,
  CheckCircle,
  Clock,
  Eye,
  FileSpreadsheet,
  MapPin,
  Search,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '../services/api';

interface StoreVerification {
  id: string;
  name: string;
  address: string;
  phone: string;
  email: string;
  businessLicense: string;
  taxId: string;
  submittedAt: Date;
  status: 'pending' | 'approved' | 'rejected';
  documents: string[];
  ownerName: string;
  ownerPhone: string;
}

export default function StoreVerificationPage() {
  const [verifications, setVerifications] = useState<StoreVerification[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedStore, setSelectedStore] = useState<StoreVerification | null>(null);

  useEffect(() => {
    loadVerifications();
  }, [filter]);

  const loadVerifications = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 100 };
      if (filter !== 'all') {
        params.status = filter;
      }
      const response = await api.getStores(params);

      // Transform API response to match interface
      const transformed = response.stores.map((store: any) => ({
        id: store.id,
        name: store.name,
        address: store.address,
        phone: store.phone || '',
        email: store.email || '',
        businessLicense: store.business_license || '',
        taxId: store.tax_id || '',
        submittedAt: new Date(store.created_at || Date.now()),
        status: store.verification_status || 'pending',
        documents: store.documents || [],
        ownerName: store.owner_name || '',
        ownerPhone: store.owner_phone || '',
      }));

      setVerifications(transformed);
    } catch (err) {
      console.error('Failed to load verifications:', err);
      toast.error('Không thể tải danh sách cửa hàng');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await api.verifyStore(id, true);
      toast.success('Đã phê duyệt cửa hàng');
      await loadVerifications();
    } catch (err) {
      console.error('Failed to approve store:', err);
      toast.error('Phê duyệt thất bại');
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Lý do từ chối:');
    if (!reason) return;

    try {
      await api.verifyStore(id, false);
      toast.success('Đã từ chối cửa hàng');
      await loadVerifications();
    } catch (err) {
      console.error('Failed to reject store:', err);
      toast.error('Từ chối thất bại');
    }
  };

  const filteredVerifications = verifications.filter((v) => {
    const matchesFilter = filter === 'all' || v.status === filter;
    const matchesSearch =
      searchQuery === '' ||
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.address.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    const config = {
      pending: { label: 'Chờ duyệt', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
      approved: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700', icon: CheckCircle },
      rejected: { label: 'Đã từ chối', color: 'bg-red-100 text-red-700', icon: XCircle },
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
          <h1 className="text-2xl font-bold text-gray-900">Xác minh cửa hàng</h1>
          <p className="text-gray-500 mt-1">Duyệt đăng ký cửa hàng mới</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm cửa hàng..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            {['all', 'pending', 'approved', 'rejected'].map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status as any)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filter === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status === 'all'
                  ? 'Tất cả'
                  : status === 'pending'
                    ? 'Chờ duyệt'
                    : status === 'approved'
                      ? 'Đã duyệt'
                      : 'Đã từ chối'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tổng số</p>
              <p className="text-2xl font-bold text-gray-900">{verifications.length}</p>
            </div>
            <Building2 className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Chờ duyệt</p>
              <p className="text-2xl font-bold text-yellow-600">
                {verifications.filter((v) => v.status === 'pending').length}
              </p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã duyệt</p>
              <p className="text-2xl font-bold text-green-600">
                {verifications.filter((v) => v.status === 'approved').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã từ chối</p>
              <p className="text-2xl font-bold text-red-600">
                {verifications.filter((v) => v.status === 'rejected').length}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Empty State */}
      {filteredVerifications.length === 0 && (
        <div className="bg-white rounded-xl p-12 text-center border border-gray-200">
          <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Không có cửa hàng nào</h3>
          <p className="text-gray-500">
            {searchQuery
              ? 'Không tìm thấy cửa hàng phù hợp'
              : filter === 'all'
                ? 'Chưa có cửa hàng nào đăng ký'
                : `Không có cửa hàng ${filter === 'pending' ? 'chờ duyệt' : filter === 'approved' ? 'đã duyệt' : 'đã từ chối'}`}
          </p>
        </div>
      )}

      {/* Verification List */}
      {filteredVerifications.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cửa hàng
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Địa chỉ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Giấy phép
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ngày đăng ký
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Trạng thái
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredVerifications.map((v) => (
                <tr key={v.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-gray-900">{v.name}</p>
                      <p className="text-sm text-gray-500">{v.ownerName}</p>
                      <p className="text-sm text-gray-500">{v.phone}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MapPin className="w-4 h-4" />
                      {v.address}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm">
                      <p className="text-gray-900">{v.businessLicense}</p>
                      <p className="text-gray-500">MST: {v.taxId}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {v.submittedAt.toLocaleDateString('vi-VN')}
                  </td>
                  <td className="px-6 py-4">{getStatusBadge(v.status)}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelectedStore(v)}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        title="Xem chi tiết"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {v.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(v.id)}
                            className="px-3 py-1.5 text-sm font-medium text-green-600 bg-green-50 hover:bg-green-100 rounded-lg transition"
                          >
                            Duyệt
                          </button>
                          <button
                            onClick={() => handleReject(v.id)}
                            className="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition"
                          >
                            Từ chối
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      {selectedStore && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">Chi tiết cửa hàng</h2>
                <button
                  onClick={() => setSelectedStore(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <XCircle className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Tên cửa hàng</p>
                <p className="font-medium text-gray-900">{selectedStore.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Địa chỉ</p>
                <p className="text-gray-900">{selectedStore.address}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Số điện thoại</p>
                  <p className="text-gray-900">{selectedStore.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Email</p>
                  <p className="text-gray-900">{selectedStore.email}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Giấy phép kinh doanh</p>
                  <p className="text-gray-900">{selectedStore.businessLicense}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Mã số thuế</p>
                  <p className="text-gray-900">{selectedStore.taxId}</p>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Chủ sở hữu</p>
                <p className="text-gray-900">{selectedStore.ownerName}</p>
                <p className="text-gray-900">{selectedStore.ownerPhone}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Tài liệu đính kèm</p>
                <div className="flex flex-wrap gap-2">
                  {selectedStore.documents.length > 0 ? (
                    selectedStore.documents.map((doc, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-lg text-sm"
                      >
                        <FileSpreadsheet className="w-4 h-4" />
                        {doc}
                      </span>
                    ))
                  ) : (
                    <p className="text-gray-500">Không có tài liệu</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Trạng thái</p>
                {getStatusBadge(selectedStore.status)}
              </div>
            </div>
            {selectedStore.status === 'pending' && (
              <div className="p-6 border-t flex gap-3 justify-end">
                <button
                  onClick={() => {
                    handleReject(selectedStore.id);
                    setSelectedStore(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition"
                >
                  Từ chối
                </button>
                <button
                  onClick={() => {
                    handleApprove(selectedStore.id);
                    setSelectedStore(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition"
                >
                  Duyệt
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
