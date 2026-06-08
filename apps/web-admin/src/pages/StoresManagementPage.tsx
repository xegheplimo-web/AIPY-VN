import { useState, useEffect, useCallback } from 'react';
import {
  Building2,
  CheckCircle,
  Clock,
  Eye,
  MapPin,
  PlayCircle,
  Search,
  Star,
  Store,
  AlertTriangle,
  Ban,
  RefreshCw,
  XCircle,
  User,
  Calendar,
  Briefcase,
} from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../components/ui/DataTable';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Skeleton } from '../components/ui/skeleton';
import api from '../services/api';

// ── Types ──────────────────────────────────────────────────────────────────

interface StoreOwner {
  id?: string;
  name?: string;
  email?: string;
  phone?: string;
}

interface StoreItem {
  id: string;
  name: string;
  address: string;
  industry?: string;
  rating?: number;
  status: 'pending' | 'active' | 'suspended' | 'rejected';
  owner?: StoreOwner;
  owner_name?: string;
  owner_phone?: string;
  created_at?: string;
  phone?: string;
  email?: string;
  description?: string;
  location_verified?: boolean;
}

type StatusFilter = 'all' | 'pending' | 'active' | 'suspended' | 'rejected';

// ── Status helpers ─────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: typeof Clock }
> = {
  pending: {
    label: 'Chờ duyệt',
    color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    icon: Clock,
  },
  active: {
    label: 'Hoạt động',
    color: 'bg-green-100 text-green-700 border-green-200',
    icon: CheckCircle,
  },
  suspended: {
    label: 'Đã đình chỉ',
    color: 'bg-red-100 text-red-700 border-red-200',
    icon: Ban,
  },
  rejected: {
    label: 'Đã từ chối',
    color: 'bg-gray-100 text-gray-600 border-gray-200',
    icon: XCircle,
  },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${config.color}`}
    >
      <Icon size={12} />
      {config.label}
    </span>
  );
}

function RatingStars({ rating }: { rating?: number }) {
  if (rating == null) return <span className="text-xs text-gray-400">—</span>;
  const clamped = Math.max(0, Math.min(5, rating));
  return (
    <span className="inline-flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          size={14}
          className={
            i < Math.round(clamped)
              ? 'fill-yellow-400 text-yellow-400'
              : 'text-gray-300'
          }
        />
      ))}
      <span className="ml-1 text-xs text-gray-500">{clamped.toFixed(1)}</span>
    </span>
  );
}

// ── Skeleton loader ────────────────────────────────────────────────────────

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-8 w-12" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function StoresManagementPage() {
  const [stores, setStores] = useState<StoreItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  // Dialogs
  const [detailStore, setDetailStore] = useState<StoreItem | null>(null);
  const [suspendDialog, setSuspendDialog] = useState<{
    open: boolean;
    store: StoreItem | null;
  }>({ open: false, store: null });
  const [suspendReason, setSuspendReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // ── Load stores ────────────────────────────────────────────────────────

  const loadStores = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: { status?: string; limit: number } = { limit: 100 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      const response = await api.getStores(params);
      // Safely handle various API response shapes
      const rawStores = response?.stores ?? [];
      const mapped: StoreItem[] = rawStores.map((s: any) => ({
        id: s.id ?? '',
        name: s.name ?? '',
        address: s.address ?? '',
        industry: s.industry ?? s.category ?? '',
        rating: s.rating ?? s.average_rating ?? undefined,
        status: s.status ?? s.verification_status ?? 'pending',
        owner: s.owner ?? undefined,
        owner_name: s.owner_name ?? s.owner?.name ?? '',
        owner_phone: s.owner_phone ?? s.owner?.phone ?? '',
        created_at: s.created_at ?? '',
        phone: s.phone ?? '',
        email: s.email ?? '',
        description: s.description ?? '',
        location_verified: s.location_verified ?? false,
      }));
      setStores(mapped);
    } catch (err: any) {
      console.error('Failed to load stores:', err);
      setError(err?.message || 'Không thể tải danh sách cửa hàng');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadStores();
  }, [loadStores]);

  // ── Filtered data ─────────────────────────────────────────────────────

  const filteredStores = stores.filter((s) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.address.toLowerCase().includes(q) ||
      (s.industry ?? '').toLowerCase().includes(q) ||
      (s.owner_name ?? '').toLowerCase().includes(q)
    );
  });

  // ── Stats ─────────────────────────────────────────────────────────────

  const stats = {
    total: stores.length,
    pending: stores.filter((s) => s.status === 'pending').length,
    active: stores.filter((s) => s.status === 'active').length,
    suspended: stores.filter((s) => s.status === 'suspended').length,
  };

  // ── Actions ───────────────────────────────────────────────────────────

  const handleVerify = async (storeId: string) => {
    try {
      setActionLoading(true);
      await api.verifyStore(storeId, true);
      await loadStores();
    } catch (err) {
      console.error('Failed to verify store:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSuspend = async () => {
    if (!suspendDialog.store) return;
    try {
      setActionLoading(true);
      await api.suspendStore(suspendDialog.store.id, suspendReason || 'Vi phạm quy định');
      setSuspendDialog({ open: false, store: null });
      setSuspendReason('');
      await loadStores();
    } catch (err) {
      console.error('Failed to suspend store:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async (storeId: string) => {
    try {
      setActionLoading(true);
      await api.activateStore(storeId);
      await loadStores();
    } catch (err) {
      console.error('Failed to activate store:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleViewDetail = async (store: StoreItem) => {
    try {
      const detail = await api.getStore(store.id);
      setDetailStore({ ...store, ...(detail ?? {}) });
    } catch {
      setDetailStore(store);
    }
  };

  // ── Table columns ─────────────────────────────────────────────────────

  const columns: ColumnDef<StoreItem>[] = [
    {
      accessorKey: 'name',
      header: 'Tên cửa hàng',
      cell: ({ row }) => {
        const s = row.original;
        return (
          <div className="flex items-center gap-3">
            <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
              <Store className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="min-w-0">
              <p className="font-medium text-gray-900 truncate max-w-[200px]">
                {s.name}
              </p>
              {s.phone && (
                <p className="text-xs text-gray-500">{s.phone}</p>
              )}
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'address',
      header: 'Địa chỉ',
      cell: ({ row }) => (
        <div className="flex items-start gap-1.5 max-w-[220px]">
          <MapPin className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
          <span className="text-sm text-gray-600 truncate">{row.original.address}</span>
        </div>
      ),
    },
    {
      accessorKey: 'industry',
      header: 'Ngành',
      cell: ({ row }) => (
        <div className="flex items-center gap-1.5">
          <Briefcase className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-sm text-gray-700">
            {row.original.industry || '—'}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'rating',
      header: 'Đánh giá',
      cell: ({ row }) => <RatingStars rating={row.original.rating} />,
    },
    {
      accessorKey: 'status',
      header: 'Trạng thái',
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
      filterFn: (row, _columnId, filterValue) => {
        if (filterValue === 'all') return true;
        return row.original.status === filterValue;
      },
    },
    {
      accessorKey: 'owner_name',
      header: 'Chủ sở hữu',
      cell: ({ row }) => {
        const s = row.original;
        const name = s.owner_name || s.owner?.name;
        return name ? (
          <div className="flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-sm text-gray-700">{name}</span>
          </div>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        );
      },
    },
    {
      accessorKey: 'created_at',
      header: 'Ngày tạo',
      cell: ({ row }) => {
        const raw = row.original.created_at;
        if (!raw) return <span className="text-xs text-gray-400">—</span>;
        return (
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-sm text-gray-600">
              {new Date(raw).toLocaleDateString('vi-VN')}
            </span>
          </div>
        );
      },
    },
    {
      id: 'actions',
      header: 'Hành động',
      cell: ({ row }) => {
        const s = row.original;
        return (
          <div className="flex items-center gap-1">
            {/* View detail */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleViewDetail(s)}
              title="Xem chi tiết"
            >
              <Eye className="w-4 h-4 text-gray-500" />
            </Button>

            {/* Verify — shown for pending / rejected */}
            {(s.status === 'pending' || s.status === 'rejected') && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleVerify(s.id)}
                disabled={actionLoading}
                title="Duyệt cửa hàng"
              >
                <CheckCircle className="w-4 h-4 text-green-600" />
              </Button>
            )}

            {/* Suspend — shown for active */}
            {s.status === 'active' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSuspendDialog({ open: true, store: s })}
                disabled={actionLoading}
                title="Đình chỉ cửa hàng"
              >
                <Ban className="w-4 h-4 text-red-500" />
              </Button>
            )}

            {/* Activate — shown for suspended */}
            {s.status === 'suspended' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleActivate(s.id)}
                disabled={actionLoading}
                title="Kích hoạt lại"
              >
                <PlayCircle className="w-4 h-4 text-green-600" />
              </Button>
            )}
          </div>
        );
      },
    },
  ];

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý cửa hàng</h1>
          <p className="text-gray-500 mt-1">
            Quản lý và phê duyệt cửa hàng trên hệ thống
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadStores} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </Button>
      </div>

      {/* Stats bar */}
      {loading && stores.length === 0 ? (
        <StatsSkeleton />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Tổng cửa hàng</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <Building2 className="w-8 h-8 text-gray-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Chờ duyệt</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Hoạt động</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Đã đình chỉ</p>
                  <p className="text-2xl font-bold text-red-600">{stats.suspended}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm kiếm theo tên, địa chỉ, ngành, chủ sở hữu..."
              className="pl-9"
            />
          </div>

          {/* Status filter pills */}
          <div className="flex gap-2 flex-wrap">
            {(
              [
                { key: 'all', label: 'Tất cả' },
                { key: 'pending', label: 'Chờ duyệt' },
                { key: 'active', label: 'Hoạt động' },
                { key: 'suspended', label: 'Đã đình chỉ' },
                { key: 'rejected', label: 'Đã từ chối' },
              ] as { key: StatusFilter; label: string }[]
            ).map(({ key, label }) => (
              <Button
                key={key}
                variant={statusFilter === key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter(key)}
              >
                {label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Error state with retry */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-red-700 font-medium mb-1">Không thể tải dữ liệu</p>
          <p className="text-sm text-red-500 mb-4">{error}</p>
          <Button variant="outline" size="sm" onClick={loadStores}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Thử lại
          </Button>
        </div>
      )}

      {/* Data table */}
      {!error && (
        <>
          {loading && stores.length === 0 ? (
            <TableSkeleton />
          ) : (
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <DataTable
                columns={columns}
                data={filteredStores}
                searchKey="name"
                searchable
              />
            </div>
          )}
        </>
      )}

      {/* ── Suspend confirmation dialog ─────────────────────────────────── */}
      <Dialog
        open={suspendDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setSuspendDialog({ open: false, store: null });
            setSuspendReason('');
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Ban className="w-5 h-5 text-red-500" />
              Đình chỉ cửa hàng
            </DialogTitle>
            <DialogDescription>
              Bạn có chắc chắn muốn đình chỉ cửa hàng{' '}
              <span className="font-semibold text-gray-900">
                {suspendDialog.store?.name}
              </span>
              ? Cửa hàng sẽ không thể hoạt động cho đến khi được kích hoạt lại.
            </DialogDescription>
          </DialogHeader>

          <div className="py-2">
            <label className="text-sm font-medium text-gray-700 mb-1.5 block">
              Lý do đình chỉ <span className="text-red-500">*</span>
            </label>
            <Textarea
              value={suspendReason}
              onChange={(e) => setSuspendReason(e.target.value)}
              placeholder="Nhập lý do đình chỉ cửa hàng..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setSuspendDialog({ open: false, store: null });
                setSuspendReason('');
              }}
              disabled={actionLoading}
            >
              Hủy
            </Button>
            <Button
              variant="destructive"
              onClick={handleSuspend}
              disabled={actionLoading || !suspendReason.trim()}
            >
              {actionLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-1.5 animate-spin" />
                  Đang xử lý...
                </>
              ) : (
                'Xác nhận đình chỉ'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Store detail dialog ─────────────────────────────────────────── */}
      <Dialog
        open={!!detailStore}
        onOpenChange={(open) => {
          if (!open) setDetailStore(null);
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Store className="w-5 h-5 text-emerald-600" />
              Chi tiết cửa hàng
            </DialogTitle>
          </DialogHeader>

          {detailStore && (
            <div className="space-y-4">
              {/* Name & Status */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {detailStore.name}
                </h3>
                <StatusBadge status={detailStore.status} />
              </div>

              {/* Info grid */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500 mb-0.5">Địa chỉ</p>
                  <p className="text-sm text-gray-900 flex items-start gap-1">
                    <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400" />
                    {detailStore.address || '—'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-0.5">Ngành</p>
                  <p className="text-sm text-gray-900 flex items-center gap-1">
                    <Briefcase className="w-3.5 h-3.5 text-gray-400" />
                    {detailStore.industry || '—'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-0.5">Đánh giá</p>
                  <RatingStars rating={detailStore.rating} />
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-0.5">Ngày tạo</p>
                  <p className="text-sm text-gray-900 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    {detailStore.created_at
                      ? new Date(detailStore.created_at).toLocaleDateString('vi-VN')
                      : '—'}
                  </p>
                </div>
              </div>

              {/* Owner */}
              <div>
                <p className="text-sm text-gray-500 mb-0.5">Chủ sở hữu</p>
                <p className="text-sm text-gray-900 flex items-center gap-1">
                  <User className="w-3.5 h-3.5 text-gray-400" />
                  {detailStore.owner_name ||
                    detailStore.owner?.name ||
                    '—'}
                </p>
                {(detailStore.owner_phone || detailStore.owner?.phone) && (
                  <p className="text-sm text-gray-600 ml-5">
                    {detailStore.owner_phone || detailStore.owner?.phone}
                  </p>
                )}
              </div>

              {/* Contact */}
              {(detailStore.phone || detailStore.email) && (
                <div className="grid grid-cols-2 gap-4">
                  {detailStore.phone && (
                    <div>
                      <p className="text-sm text-gray-500 mb-0.5">Số điện thoại</p>
                      <p className="text-sm text-gray-900">{detailStore.phone}</p>
                    </div>
                  )}
                  {detailStore.email && (
                    <div>
                      <p className="text-sm text-gray-500 mb-0.5">Email</p>
                      <p className="text-sm text-gray-900">{detailStore.email}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Description */}
              {detailStore.description && (
                <div>
                  <p className="text-sm text-gray-500 mb-0.5">Mô tả</p>
                  <p className="text-sm text-gray-700">{detailStore.description}</p>
                </div>
              )}

              {/* Quick actions in detail */}
              <div className="flex gap-2 pt-2 border-t">
                {(detailStore.status === 'pending' ||
                  detailStore.status === 'rejected') && (
                  <Button
                    size="sm"
                    onClick={() => {
                      handleVerify(detailStore.id);
                      setDetailStore(null);
                    }}
                    disabled={actionLoading}
                  >
                    <CheckCircle className="w-4 h-4 mr-1.5" />
                    Duyệt cửa hàng
                  </Button>
                )}
                {detailStore.status === 'active' && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      setDetailStore(null);
                      setSuspendDialog({ open: true, store: detailStore });
                    }}
                    disabled={actionLoading}
                  >
                    <Ban className="w-4 h-4 mr-1.5" />
                    Đình chỉ
                  </Button>
                )}
                {detailStore.status === 'suspended' && (
                  <Button
                    size="sm"
                    onClick={() => {
                      handleActivate(detailStore.id);
                      setDetailStore(null);
                    }}
                    disabled={actionLoading}
                  >
                    <PlayCircle className="w-4 h-4 mr-1.5" />
                    Kích hoạt lại
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
