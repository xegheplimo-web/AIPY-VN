import {
  AlertTriangle,
  CheckCircle,
  Eye,
  FileSpreadsheet,
  Flag,
  MessageSquare,
  Search,
  ShoppingBag,
  Store,
  User as UserIcon,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface Report {
  id: string;
  type: 'store' | 'product' | 'user' | 'order';
  targetId: string;
  targetName: string;
  reporterId: string;
  reporterName: string;
  reason: string;
  description: string;
  status: 'pending' | 'reviewed' | 'resolved' | 'dismissed';
  createdAt: Date;
  evidence?: string[];
}

export default function ReportModerationPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'reviewed' | 'resolved' | 'dismissed'>(
    'all'
  );
  const [typeFilter, setTypeFilter] = useState<'all' | 'store' | 'product' | 'user' | 'order'>(
    'all'
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      // Mock data - sẽ thay bằng API call sau
      const mockReports: Report[] = [
        {
          id: '1',
          type: 'store',
          targetId: 'store-1',
          targetName: 'Nhà thuốc An Khang',
          reporterId: 'user-1',
          reporterName: 'Nguyễn Văn A',
          reason: 'fake_products',
          description: 'Cửa hàng bán sản phẩm giả mạo, không đúng mô tả',
          status: 'pending',
          createdAt: new Date(Date.now() - 2 * 3600000),
          evidence: ['screenshot1.jpg', 'screenshot2.jpg'],
        },
        {
          id: '2',
          type: 'product',
          targetId: 'product-1',
          targetName: 'Panadol Extra 500mg',
          reporterId: 'user-2',
          reporterName: 'Trần Thị B',
          reason: 'wrong_price',
          description: 'Giá trên web khác giá thực tế tại cửa hàng',
          status: 'pending',
          createdAt: new Date(Date.now() - 5 * 3600000),
        },
        {
          id: '3',
          type: 'user',
          targetId: 'user-3',
          targetName: 'Lê Văn C',
          reporterId: 'user-4',
          reporterName: 'Phạm Thị D',
          reason: 'harassment',
          description: 'Người dùng này có hành vi quấy rối trong chat',
          status: 'reviewed',
          createdAt: new Date(Date.now() - 24 * 3600000),
        },
        {
          id: '4',
          type: 'order',
          targetId: 'order-1',
          targetName: 'Đơn hàng #12345',
          reporterId: 'user-5',
          reporterName: 'Hoàng Văn E',
          reason: 'scam',
          description: 'Cửa hàng không giao hàng nhưng vẫn thu tiền',
          status: 'pending',
          createdAt: new Date(Date.now() - 48 * 3600000),
          evidence: ['payment_proof.jpg'],
        },
      ];
      setReports(mockReports);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (reportId: string) => {
    try {
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status: 'resolved' as const } : r))
      );
    } catch (err) {
      alert('Xử lý thất bại');
    }
  };

  const handleDismiss = async (reportId: string) => {
    const reason = prompt('Lý do từ chối:');
    if (!reason) return;

    try {
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status: 'dismissed' as const } : r))
      );
    } catch (err) {
      alert('Từ chối thất bại');
    }
  };

  const filteredReports = reports.filter((r) => {
    const matchesFilter = filter === 'all' || r.status === filter;
    const matchesType = typeFilter === 'all' || r.type === typeFilter;
    const matchesSearch =
      searchQuery === '' ||
      r.targetName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.reporterName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesType && matchesSearch;
  });

  const getTypeBadge = (type: string) => {
    const config = {
      store: { label: 'Cửa hàng', color: 'bg-purple-100 text-purple-700', icon: Store },
      product: { label: 'Sản phẩm', color: 'bg-blue-100 text-blue-700', icon: ShoppingBag },
      user: { label: 'Người dùng', color: 'bg-green-100 text-green-700', icon: UserIcon },
      order: { label: 'Đơn hàng', color: 'bg-orange-100 text-orange-700', icon: MessageSquare },
    };
    const { label, color, icon: Icon } = config[type as keyof typeof config];
    return (
      <span
        className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${color}`}
      >
        <Icon size={12} /> {label}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const config = {
      pending: { label: 'Chờ xử lý', color: 'bg-yellow-100 text-yellow-700' },
      reviewed: { label: 'Đang xem', color: 'bg-blue-100 text-blue-700' },
      resolved: { label: 'Đã xử lý', color: 'bg-green-100 text-green-700' },
      dismissed: { label: 'Đã từ chối', color: 'bg-gray-100 text-gray-700' },
    };
    const { label, color } = config[status as keyof typeof config];
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${color}`}>{label}</span>;
  };

  const getReasonLabel = (reason: string) => {
    const labels: Record<string, string> = {
      fake_products: 'Sản phẩm giả mạo',
      wrong_price: 'Giá sai',
      harassment: 'Quấy rối',
      scam: 'Lừa đảo',
      spam: 'Spam',
      inappropriate: 'Nội dung không phù hợp',
    };
    return labels[reason] || reason;
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
          <h1 className="text-2xl font-bold text-gray-900">Moderation Reports</h1>
          <p className="text-gray-500 mt-1">Xử lý báo cáo từ người dùng</p>
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
              placeholder="Tìm kiếm báo cáo..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="pending">Chờ xử lý</option>
              <option value="reviewed">Đang xem</option>
              <option value="resolved">Đã xử lý</option>
              <option value="dismissed">Đã từ chối</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả loại</option>
              <option value="store">Cửa hàng</option>
              <option value="product">Sản phẩm</option>
              <option value="user">Người dùng</option>
              <option value="order">Đơn hàng</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tổng số</p>
              <p className="text-2xl font-bold text-gray-900">{reports.length}</p>
            </div>
            <Flag className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Chờ xử lý</p>
              <p className="text-2xl font-bold text-yellow-600">
                {reports.filter((r) => r.status === 'pending').length}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã xử lý</p>
              <p className="text-2xl font-bold text-green-600">
                {reports.filter((r) => r.status === 'resolved').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã từ chối</p>
              <p className="text-2xl font-bold text-gray-600">
                {reports.filter((r) => r.status === 'dismissed').length}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-gray-500" />
          </div>
        </div>
      </div>

      {/* Report List */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left py-3 px-4 font-medium text-gray-600">Loại</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Đối tượng</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Người báo cáo</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Lý do</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Ngày báo</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Trạng thái</th>
              <th className="text-right py-3 px-4 font-medium text-gray-600">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredReports.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-12 text-gray-500">
                  Không tìm thấy kết quả
                </td>
              </tr>
            ) : (
              filteredReports.map((report) => (
                <tr key={report.id} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4">{getTypeBadge(report.type)}</td>
                  <td className="py-4 px-4">
                    <p className="font-medium text-gray-900">{report.targetName}</p>
                    <p className="text-sm text-gray-500">ID: {report.targetId}</p>
                  </td>
                  <td className="py-4 px-4">
                    <p className="font-medium text-gray-900">{report.reporterName}</p>
                    <p className="text-sm text-gray-500">ID: {report.reporterId}</p>
                  </td>
                  <td className="py-4 px-4">
                    <p className="text-sm text-gray-900">{getReasonLabel(report.reason)}</p>
                  </td>
                  <td className="py-4 px-4 text-sm text-gray-600">
                    {report.createdAt.toLocaleDateString('vi-VN')}
                  </td>
                  <td className="py-4 px-4">{getStatusBadge(report.status)}</td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setSelectedReport(report)}
                        className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                        title="Xem chi tiết"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {report.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleResolve(report.id)}
                            className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                            title="Xử lý"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDismiss(report.id)}
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
      {selectedReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b">
              <h2 className="text-xl font-bold">Chi tiết báo cáo</h2>
              <button
                onClick={() => setSelectedReport(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-96 space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">Thông tin đối tượng</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Loại:</span>
                      <span>{getTypeBadge(selectedReport.type)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Tên:</span>
                      <span className="font-medium">{selectedReport.targetName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">ID:</span>
                      <span className="font-medium">{selectedReport.targetId}</span>
                    </div>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">Thông tin người báo cáo</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Tên:</span>
                      <span className="font-medium">{selectedReport.reporterName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">ID:</span>
                      <span className="font-medium">{selectedReport.reporterId}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Lý do báo cáo</h3>
                <p className="text-sm text-gray-900">{getReasonLabel(selectedReport.reason)}</p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Mô tả chi tiết</h3>
                <p className="text-sm text-gray-700">{selectedReport.description}</p>
              </div>
              {selectedReport.evidence && selectedReport.evidence.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Bằng chứng</h3>
                  <div className="space-y-2">
                    {selectedReport.evidence.map((evidence, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                        <FileSpreadsheet className="w-4 h-4 text-blue-600" />
                        <span className="text-sm">{evidence}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <h3 className="font-semibold mb-2">Thông tin bổ sung</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Ngày báo cáo:</span>
                    <span className="font-medium">
                      {selectedReport.createdAt.toLocaleString('vi-VN')}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Trạng thái:</span>
                    <span>{getStatusBadge(selectedReport.status)}</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-6 border-t flex gap-3 justify-end">
              <button
                onClick={() => setSelectedReport(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Đóng
              </button>
              {selectedReport.status === 'pending' && (
                <>
                  <button
                    onClick={() => {
                      handleDismiss(selectedReport.id);
                      setSelectedReport(null);
                    }}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Từ chối
                  </button>
                  <button
                    onClick={() => {
                      handleResolve(selectedReport.id);
                      setSelectedReport(null);
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Xử lý
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
