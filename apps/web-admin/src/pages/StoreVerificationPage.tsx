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
  }, []);

  const loadVerifications = async () => {
    try {
      // Mock data - sẽ thay bằng API call sau
      const mockData: StoreVerification[] = [
        {
          id: '1',
          name: 'Nhà thuốc An Khang',
          address: '123 Nguyễn Trãi, Quận 1, TP.HCM',
          phone: '0901234567',
          email: 'anhkang@example.com',
          businessLicense: 'GP-12345',
          taxId: '123456789',
          submittedAt: new Date(Date.now() - 2 * 3600000),
          status: 'pending',
          documents: ['license.jpg', 'id_card.jpg'],
          ownerName: 'Nguyễn Văn A',
          ownerPhone: '0901234567',
        },
        {
          id: '2',
          name: 'Nhà thuốc Long Châu',
          address: '456 Lê Lợi, Quận 3, TP.HCM',
          phone: '0912345678',
          email: 'longchau@example.com',
          businessLicense: 'GP-67890',
          taxId: '987654321',
          submittedAt: new Date(Date.now() - 24 * 3600000),
          status: 'pending',
          documents: ['license.jpg'],
          ownerName: 'Trần Thị B',
          ownerPhone: '0912345678',
        },
        {
          id: '3',
          name: 'Nhà thuốc Pharmacity',
          address: '789 Hai Bà Trưng, Quận 5, TP.HCM',
          phone: '0923456789',
          email: 'pharmacity@example.com',
          businessLicense: 'GP-11111',
          taxId: '111222333',
          submittedAt: new Date(Date.now() - 48 * 3600000),
          status: 'approved',
          documents: ['license.jpg', 'id_card.jpg', 'tax_paper.jpg'],
          ownerName: 'Lê Văn C',
          ownerPhone: '0923456789',
        },
      ];
      setVerifications(mockData);
    } catch (err) {
      console.error('Failed to load verifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      // Mock API call
      setVerifications((prev) =>
        prev.map((v) => (v.id === id ? { ...v, status: 'approved' as const } : v))
      );
    } catch (err) {
      alert('Phê duyệt thất bại');
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Lý do từ chối:');
    if (!reason) return;

    try {
      // Mock API call
      setVerifications((prev) =>
        prev.map((v) => (v.id === id ? { ...v, status: 'rejected' as const } : v))
      );
    } catch (err) {
      alert('Từ chối thất bại');
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

      {/* Verification List */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left py-3 px-4 font-medium text-gray-600">Cửa hàng</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Chủ sở hữu</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Giấy phép</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Ngày đăng</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Trạng thái</th>
              <th className="text-right py-3 px-4 font-medium text-gray-600">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredVerifications.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-gray-500">
                  Không tìm thấy kết quả
                </td>
              </tr>
            ) : (
              filteredVerifications.map((verification) => (
                <tr key={verification.id} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <div>
                      <p className="font-medium text-gray-900">{verification.name}</p>
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <MapPin size={14} /> {verification.address}
                      </p>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div>
                      <p className="font-medium text-gray-900">{verification.ownerName}</p>
                      <p className="text-sm text-gray-500">{verification.ownerPhone}</p>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="space-y-1 text-sm">
                      <p>
                        <span className="text-gray-500">GP:</span> {verification.businessLicense}
                      </p>
                      <p>
                        <span className="text-gray-500">MST:</span> {verification.taxId}
                      </p>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-sm text-gray-600">
                    {verification.submittedAt.toLocaleDateString('vi-VN')}
                  </td>
                  <td className="py-4 px-4">{getStatusBadge(verification.status)}</td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setSelectedStore(verification)}
                        className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                        title="Xem chi tiết"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {verification.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(verification.id)}
                            className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                            title="Phê duyệt"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleReject(verification.id)}
                            className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                            title="Từ chối"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      {selectedStore && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b">
              <h2 className="text-xl font-bold">Chi tiết đăng ký</h2>
              <button
                onClick={() => setSelectedStore(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-96 space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Thông tin cửa hàng</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tên:</span>
                    <span className="font-medium">{selectedStore.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Địa chỉ:</span>
                    <span className="font-medium">{selectedStore.address}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Điện thoại:</span>
                    <span className="font-medium">{selectedStore.phone}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Email:</span>
                    <span className="font-medium">{selectedStore.email}</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Thông tin chủ sở hữu</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tên:</span>
                    <span className="font-medium">{selectedStore.ownerName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Điện thoại:</span>
                    <span className="font-medium">{selectedStore.ownerPhone}</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Giấy phép kinh doanh</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">GP:</span>
                    <span className="font-medium">{selectedStore.businessLicense}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">MST:</span>
                    <span className="font-medium">{selectedStore.taxId}</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Tài liệu đính kèm</h3>
                <div className="space-y-2">
                  {selectedStore.documents.map((doc, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                      <FileSpreadsheet className="w-4 h-4 text-blue-600" />
                      <span className="text-sm">{doc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="p-6 border-t flex gap-3 justify-end">
              <button
                onClick={() => setSelectedStore(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Đóng
              </button>
              {selectedStore.status === 'pending' && (
                <>
                  <button
                    onClick={() => {
                      handleReject(selectedStore.id);
                      setSelectedStore(null);
                    }}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Từ chối
                  </button>
                  <button
                    onClick={() => {
                      handleApprove(selectedStore.id);
                      setSelectedStore(null);
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Phê duyệt
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
