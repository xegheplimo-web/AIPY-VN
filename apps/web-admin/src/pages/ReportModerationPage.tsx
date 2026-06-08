import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  FileText,
  Flag,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  ShoppingBag,
  Store,
  Trash2,
  User as UserIcon,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '../services/api';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Skeleton } from '../components/ui/skeleton';
import { Textarea } from '../components/ui/textarea';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReportType = 'store' | 'product' | 'user' | 'order';
type ReportStatus = 'pending' | 'resolved' | 'dismissed';
type StatusFilter = 'all' | ReportStatus;
type TypeFilter = 'all' | ReportType;

interface Report {
  id: string;
  type: ReportType;
  targetId: string;
  targetName: string;
  reporterId: string;
  reporterName: string;
  reason: string;
  description: string;
  status: ReportStatus;
  createdAt: Date;
  evidence?: string[];
  resolutionNotes?: string;
  resolvedAt?: Date;
  resolvedBy?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Safely extract the reports array from whatever shape the API returns. */
function extractReports(raw: any): any[] {
  if (!raw) return [];
  // { reports: [...] }
  if (Array.isArray(raw.reports)) return raw.reports;
  // { data: { reports: [...] } }
  if (raw.data && Array.isArray(raw.data.reports)) return raw.data.reports;
  // { data: [...] }
  if (Array.isArray(raw.data)) return raw.data;
  // Already an array
  if (Array.isArray(raw)) return raw;
  return [];
}

/** Normalise a single API report object into our local Report interface. */
function normaliseReport(r: any): Report {
  return {
    id: r.id ?? '',
    type: (r.type ?? r.report_type ?? 'store') as ReportType,
    targetId: r.target_id ?? r.targetId ?? r.target?.id ?? '',
    targetName: r.target_name ?? r.targetName ?? r.target?.name ?? '—',
    reporterId: r.reporter_id ?? r.reporterId ?? r.reporter?.id ?? '',
    reporterName: r.reporter_name ?? r.reporterName ?? r.reporter?.name ?? '—',
    reason: r.reason ?? r.report_reason ?? '',
    description: r.description ?? r.details ?? '',
    status: (r.status ?? 'pending') as ReportStatus,
    createdAt: new Date(r.created_at ?? r.createdAt ?? Date.now()),
    evidence: r.evidence ?? r.attachments ?? r.images ?? [],
    resolutionNotes: r.resolution_notes ?? r.resolutionNotes ?? '',
    resolvedAt: r.resolved_at ? new Date(r.resolved_at) : undefined,
    resolvedBy: r.resolved_by ?? r.resolvedBy ?? '',
  };
}

const REASON_LABELS: Record<string, string> = {
  fake_products: 'Sản phẩm giả mạo',
  wrong_price: 'Giá sai',
  harassment: 'Quấy rối',
  scam: 'Lừa đảo',
  spam: 'Spam',
  inappropriate: 'Nội dung không phù hợp',
  copyright: 'Vi phạm bản quyền',
  other: 'Khác',
};

function getReasonLabel(reason: string): string {
  return REASON_LABELS[reason] ?? reason;
}

const TYPE_CONFIG: Record<
  ReportType,
  { label: string; color: string; icon: typeof Store }
> = {
  store: { label: 'Cửa hàng', color: 'bg-purple-100 text-purple-700', icon: Store },
  product: { label: 'Sản phẩm', color: 'bg-amber-100 text-amber-700', icon: ShoppingBag },
  user: { label: 'Người dùng', color: 'bg-emerald-100 text-emerald-700', icon: UserIcon },
  order: { label: 'Đơn hàng', color: 'bg-rose-100 text-rose-700', icon: MessageSquare },
};

const STATUS_CONFIG: Record<
  ReportStatus,
  { label: string; color: string; icon: typeof Clock }
> = {
  pending: { label: 'Chờ xử lý', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  resolved: { label: 'Đã xử lý', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  dismissed: { label: 'Đã từ chối', color: 'bg-gray-100 text-gray-600', icon: XCircle },
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TypeBadge({ type }: { type: ReportType }) {
  const cfg = TYPE_CONFIG[type] ?? TYPE_CONFIG.store;
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}
    >
      <Icon size={12} />
      {cfg.label}
    </span>
  );
}

function StatusBadge({ status }: { status: ReportStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}
    >
      <Icon size={12} />
      {cfg.label}
    </span>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  iconColor,
}: {
  label: string;
  value: number;
  icon: typeof Flag;
  iconColor: string;
}) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <Icon className={`w-8 h-8 ${iconColor}`} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ReportModerationPage() {
  // Data
  const [reports, setReports] = useState<Report[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Loading / error
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail modal
  const [detailReport, setDetailReport] = useState<Report | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Resolve modal
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [resolveTarget, setResolveTarget] = useState<Report | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolving, setResolving] = useState(false);

  // Dismiss confirm modal
  const [dismissModalOpen, setDismissModalOpen] = useState(false);
  const [dismissTarget, setDismissTarget] = useState<Report | null>(null);
  const [dismissNotes, setDismissNotes] = useState('');
  const [dismissing, setDismissing] = useState(false);

  // ----- Fetch reports ----------------------------------------------------

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { limit: '100' };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (typeFilter !== 'all') params.type = typeFilter;

      const raw = await api.getReports(params);
      const list = extractReports(raw).map(normaliseReport);
      setReports(list);
      setTotalCount(raw?.total ?? list.length);
    } catch (err: any) {
      console.error('Failed to load reports:', err);
      setError(err?.message ?? 'Không thể tải danh sách báo cáo');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  // ----- Fetch single report detail --------------------------------------

  const openDetail = async (report: Report) => {
    setDetailReport(report);
    setDetailLoading(true);
    try {
      const raw = await api.getReport(report.id);
      // API may return { report: {...} } or { data: { ... } } or the object directly
      const obj = raw?.report ?? raw?.data ?? raw;
      if (obj && typeof obj === 'object') {
        setDetailReport(normaliseReport(obj));
      }
    } catch (err) {
      // Fallback: just show the data we already have
      console.warn('Could not fetch report detail, using list data', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // ----- Resolve ----------------------------------------------------------

  const openResolveModal = (report: Report) => {
    setResolveTarget(report);
    setResolutionNotes('');
    setResolveModalOpen(true);
  };

  const handleResolve = async () => {
    if (!resolveTarget) return;
    if (!resolutionNotes.trim()) {
      toast.error('Vui lòng nhập ghi chú xử lý');
      return;
    }
    setResolving(true);
    try {
      await api.resolveReport(resolveTarget.id, resolutionNotes.trim());
      toast.success('Đã xử lý báo cáo thành công');
      setResolveModalOpen(false);
      setResolveTarget(null);
      setResolutionNotes('');
      await loadReports();
    } catch (err: any) {
      toast.error(err?.message ?? 'Xử lý báo cáo thất bại');
    } finally {
      setResolving(false);
    }
  };

  // ----- Dismiss ----------------------------------------------------------

  const openDismissModal = (report: Report) => {
    setDismissTarget(report);
    setDismissNotes('');
    setDismissModalOpen(true);
  };

  const handleDismiss = async () => {
    if (!dismissTarget) return;
    setDismissing(true);
    try {
      await api.dismissReport(dismissTarget.id, dismissNotes.trim() || 'Báo cáo bị từ chối');
      toast.success('Đã từ chối báo cáo');
      setDismissModalOpen(false);
      setDismissTarget(null);
      setDismissNotes('');
      await loadReports();
    } catch (err: any) {
      toast.error(err?.message ?? 'Từ chối báo cáo thất bại');
    } finally {
      setDismissing(false);
    }
  };

  // ----- Derived data -----------------------------------------------------

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      searchQuery === '' ||
      r.targetName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.reporterName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.reason.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const pendingCount = reports.filter((r) => r.status === 'pending').length;
  const resolvedCount = reports.filter((r) => r.status === 'resolved').length;
  const dismissedCount = reports.filter((r) => r.status === 'dismissed').length;

  // ----- Render: Loading skeleton -----------------------------------------

  if (loading && reports.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-12 rounded-xl" />
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 rounded-lg" />
        ))}
      </div>
    );
  }

  // ----- Render: Error with retry -----------------------------------------

  if (error && reports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertTriangle className="w-16 h-16 text-yellow-500" />
        <h2 className="text-xl font-semibold text-gray-900">Không thể tải báo cáo</h2>
        <p className="text-gray-500 max-w-md text-center">{error}</p>
        <Button onClick={loadReports} variant="outline" className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Thử lại
        </Button>
      </div>
    );
  }

  // ----- Render: Main page ------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý báo cáo</h1>
          <p className="text-gray-500 mt-1">Xử lý các báo cáo từ người dùng</p>
        </div>
        <Button onClick={loadReports} variant="outline" size="sm" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </Button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Tổng báo cáo" value={totalCount} icon={Flag} iconColor="text-gray-400" />
        <StatCard
          label="Chờ xử lý"
          value={pendingCount}
          icon={AlertTriangle}
          iconColor="text-yellow-500"
        />
        <StatCard
          label="Đã xử lý"
          value={resolvedCount}
          icon={CheckCircle}
          iconColor="text-green-500"
        />
        <StatCard
          label="Đã từ chối"
          value={dismissedCount}
          icon={XCircle}
          iconColor="text-gray-500"
        />
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4 space-y-4">
        {/* Status tabs */}
        <div className="flex flex-wrap gap-2">
          {(
            [
              ['all', 'Tất cả'],
              ['pending', 'Chờ xử lý'],
              ['resolved', 'Đã xử lý'],
              ['dismissed', 'Đã từ chối'],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setStatusFilter(value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                statusFilter === value
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label}
              {value !== 'all' && (
                <span className="ml-1.5 text-xs opacity-75">
                  ({value === 'pending'
                    ? pendingCount
                    : value === 'resolved'
                      ? resolvedCount
                      : dismissedCount})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Search + type filter row */}
        <div className="flex gap-4 flex-col sm:flex-row">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm theo tên, lý do, mô tả..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
            />
          </div>
          <Select
            value={typeFilter}
            onValueChange={(v) => setTypeFilter(v as TypeFilter)}
          >
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Loại báo cáo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả loại</SelectItem>
              <SelectItem value="store">Cửa hàng</SelectItem>
              <SelectItem value="product">Sản phẩm</SelectItem>
              <SelectItem value="user">Người dùng</SelectItem>
              <SelectItem value="order">Đơn hàng</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Report list */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {/* Desktop table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">Loại</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">
                  Đối tượng
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">
                  Người báo cáo
                </th>
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">Lý do</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">Ngày báo</th>
                <th className="text-left py-3 px-4 font-medium text-gray-600 text-sm">
                  Trạng thái
                </th>
                <th className="text-right py-3 px-4 font-medium text-gray-600 text-sm">
                  Hành động
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-gray-500">
                    <Flag className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="font-medium">Không tìm thấy báo cáo</p>
                    <p className="text-sm mt-1">
                      {searchQuery
                        ? 'Thử thay đổi từ khóa tìm kiếm'
                        : statusFilter !== 'all'
                          ? 'Không có báo cáo nào với trạng thái này'
                          : 'Chưa có báo cáo nào'}
                    </p>
                  </td>
                </tr>
              ) : (
                filteredReports.map((report) => (
                  <tr key={report.id} className="border-b hover:bg-gray-50 transition">
                    <td className="py-4 px-4">
                      <TypeBadge type={report.type} />
                    </td>
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
                    <td className="py-4 px-4">
                      <StatusBadge status={report.status} />
                    </td>
                    <td className="py-4 px-4 text-right">
                      <div className="flex gap-1.5 justify-end">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openDetail(report)}
                          title="Xem chi tiết"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {report.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openResolveModal(report)}
                              title="Xử lý"
                              className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => openDismissModal(report)}
                              title="Từ chối"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
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

        {/* Mobile cards */}
        <div className="md:hidden divide-y">
          {filteredReports.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <Flag className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="font-medium">Không tìm thấy báo cáo</p>
              <p className="text-sm mt-1">
                {searchQuery
                  ? 'Thử thay đổi từ khóa tìm kiếm'
                  : 'Chưa có báo cáo nào phù hợp'}
              </p>
            </div>
          ) : (
            filteredReports.map((report) => (
              <div key={report.id} className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <TypeBadge type={report.type} />
                  <StatusBadge status={report.status} />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{report.targetName}</p>
                  <p className="text-sm text-gray-500">ID: {report.targetId}</p>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">
                    Người báo: <span className="text-gray-700">{report.reporterName}</span>
                  </span>
                  <span className="text-gray-500">
                    {report.createdAt.toLocaleDateString('vi-VN')}
                  </span>
                </div>
                <div className="text-sm text-gray-600">{getReasonLabel(report.reason)}</div>
                <div className="flex gap-2 pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 gap-1"
                    onClick={() => openDetail(report)}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Chi tiết
                  </Button>
                  {report.status === 'pending' && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 gap-1 text-green-600 border-green-300 hover:bg-green-50"
                        onClick={() => openResolveModal(report)}
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Xử lý
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 gap-1 text-red-600 border-red-300 hover:bg-red-50"
                        onClick={() => openDismissModal(report)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Từ chối
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ===== Detail Dialog ===== */}
      <Dialog
        open={detailReport !== null}
        onOpenChange={(open) => {
          if (!open) setDetailReport(null);
        }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Chi tiết báo cáo</DialogTitle>
            <DialogDescription>
              Xem thông tin chi tiết và bằng chứng của báo cáo
            </DialogDescription>
          </DialogHeader>

          {detailLoading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-6 w-1/2" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-6 w-2/3" />
            </div>
          ) : detailReport ? (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-5 pr-4">
                {/* Target info */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Thông tin đối tượng
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Loại:</span>
                      <TypeBadge type={detailReport.type} />
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Tên đối tượng:</span>
                      <span className="font-medium text-gray-900">
                        {detailReport.targetName}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Mã ID:</span>
                      <span className="font-mono text-gray-700">{detailReport.targetId}</span>
                    </div>
                  </div>
                </div>

                {/* Reporter info */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Người báo cáo
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Tên:</span>
                      <span className="font-medium text-gray-900">
                        {detailReport.reporterName}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Mã ID:</span>
                      <span className="font-mono text-gray-700">{detailReport.reporterId}</span>
                    </div>
                  </div>
                </div>

                {/* Reason */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Lý do báo cáo
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <Badge variant="secondary" className="mb-2">
                      {getReasonLabel(detailReport.reason)}
                    </Badge>
                    {detailReport.description && (
                      <p className="text-sm text-gray-700 mt-2">{detailReport.description}</p>
                    )}
                  </div>
                </div>

                {/* Evidence */}
                {detailReport.evidence && detailReport.evidence.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Bằng chứng ({detailReport.evidence.length})
                    </h4>
                    <div className="space-y-2">
                      {detailReport.evidence.map((ev, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg"
                        >
                          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                          <span className="text-sm text-gray-700 truncate">{ev}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Meta info */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Thông tin bổ sung
                  </h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Ngày báo cáo:</span>
                      <span className="font-medium">
                        {detailReport.createdAt.toLocaleString('vi-VN')}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Trạng thái:</span>
                      <StatusBadge status={detailReport.status} />
                    </div>
                    {detailReport.resolutionNotes && (
                      <div className="flex justify-between text-sm gap-4">
                        <span className="text-gray-500 shrink-0">Ghi chú xử lý:</span>
                        <span className="text-gray-700 text-right">
                          {detailReport.resolutionNotes}
                        </span>
                      </div>
                    )}
                    {detailReport.resolvedAt && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Ngày xử lý:</span>
                        <span className="font-medium">
                          {detailReport.resolvedAt.toLocaleString('vi-VN')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </ScrollArea>
          ) : null}

          <DialogFooter className="gap-2 sm:gap-0">
            {detailReport && detailReport.status === 'pending' && (
              <>
                <Button
                  variant="destructive"
                  onClick={() => {
                    setDetailReport(null);
                    openDismissModal(detailReport);
                  }}
                  className="gap-1"
                >
                  <Trash2 className="w-4 h-4" />
                  Từ chối
                </Button>
                <Button
                  onClick={() => {
                    setDetailReport(null);
                    openResolveModal(detailReport);
                  }}
                  className="gap-1 bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4" />
                  Xử lý
                </Button>
              </>
            )}
            <Button
              variant="outline"
              onClick={() => setDetailReport(null)}
            >
              Đóng
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== Resolve Dialog ===== */}
      <Dialog
        open={resolveModalOpen}
        onOpenChange={(open) => {
          if (!open) {
            setResolveModalOpen(false);
            setResolveTarget(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Xử lý báo cáo</DialogTitle>
            <DialogDescription>
              Bạn đang xử lý báo cáo về{' '}
              <span className="font-medium">{resolveTarget?.targetName ?? ''}</span>. Vui lòng nhập
              ghi chú xử lý.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1.5 block">
                Ghi chú xử lý <span className="text-red-500">*</span>
              </label>
              <Textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Mô tả hành động đã thực hiện, ví dụ: Đã kiểm tra và gỡ bỏ sản phẩm vi phạm..."
                rows={4}
                className="resize-none"
              />
              {!resolutionNotes.trim() && resolveTarget && (
                <p className="text-xs text-gray-400 mt-1">
                  Ghi chú xử lý là bắt buộc để hoàn tất
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setResolveModalOpen(false);
                setResolveTarget(null);
              }}
              disabled={resolving}
            >
              Hủy
            </Button>
            <Button
              onClick={handleResolve}
              disabled={resolving || !resolutionNotes.trim()}
              className="gap-1 bg-green-600 hover:bg-green-700"
            >
              {resolving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Đang xử lý...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Xác nhận xử lý
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ===== Dismiss Confirm Dialog ===== */}
      <Dialog
        open={dismissModalOpen}
        onOpenChange={(open) => {
          if (!open) {
            setDismissModalOpen(false);
            setDismissTarget(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Xác nhận từ chối báo cáo</DialogTitle>
            <DialogDescription>
              Bạn có chắc chắn muốn từ chối báo cáo về{' '}
              <span className="font-medium">{dismissTarget?.targetName ?? ''}</span>? Hành động này
              không thể hoàn tác.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">
                <p className="font-medium">Lưu ý</p>
                <p className="mt-0.5">
                  Báo cáo bị từ chối sẽ được đánh dấu là không hợp lệ. Nếu có thêm bằng chứng, người
                  dùng có thể gửi báo cáo mới.
                </p>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1.5 block">
                Lý do từ chối
              </label>
              <Textarea
                value={dismissNotes}
                onChange={(e) => setDismissNotes(e.target.value)}
                placeholder="Nhập lý do từ chối báo cáo này..."
                rows={3}
                className="resize-none"
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setDismissModalOpen(false);
                setDismissTarget(null);
              }}
              disabled={dismissing}
            >
              Hủy
            </Button>
            <Button
              variant="destructive"
              onClick={handleDismiss}
              disabled={dismissing}
              className="gap-1"
            >
              {dismissing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Đang từ chối...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4" />
                  Xác nhận từ chối
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
