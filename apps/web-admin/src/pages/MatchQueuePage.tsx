import {
  AlertTriangle,
  ArrowLeftRight,
  CheckCircle,
  Clock,
  Database,
  Loader2,
  MapPin,
  Merge,
  Phone,
  RefreshCw,
  Search,
  Store,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import api from '../services/api';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from '../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Skeleton } from '../components/ui/skeleton';

// ─── Types ───────────────────────────────────────────────────────────────────

interface SeedStore {
  id: string;
  name: string;
  address: string;
  phone: string;
  latitude: number;
  longitude: number;
  industry: string;
  source: string;
}

interface RegisteredStore {
  id: string;
  name: string;
  address: string;
  phone: string;
  email: string;
  latitude: number;
  longitude: number;
  industry: string;
  ownerName: string;
  submittedAt: string;
}

interface MatchItem {
  id: string;
  seed: SeedStore;
  registered: RegisteredStore;
  similarity: number;
  status: 'pending' | 'approved' | 'rejected' | 'merged';
  matchedAt: string;
}

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected';
type ConfirmAction = { matchId: string; action: 'approve' | 'reject' } | null;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function safeString(val: unknown, fallback = ''): string {
  return typeof val === 'string' ? val : fallback;
}

function safeNumber(val: unknown, fallback = 0): number {
  return typeof val === 'number' && !isNaN(val) ? val : fallback;
}

function parseSeed(raw: Record<string, unknown>): SeedStore {
  return {
    id: safeString(raw.id),
    name: safeString(raw.name),
    address: safeString(raw.address),
    phone: safeString(raw.phone),
    latitude: safeNumber(raw.latitude),
    longitude: safeNumber(raw.longitude),
    industry: safeString(raw.industry),
    source: safeString(raw.source),
  };
}

function parseRegistered(raw: Record<string, unknown>): RegisteredStore {
  return {
    id: safeString(raw.id),
    name: safeString(raw.name),
    address: safeString(raw.address),
    phone: safeString(raw.phone),
    email: safeString(raw.email),
    latitude: safeNumber(raw.latitude),
    longitude: safeNumber(raw.longitude),
    industry: safeString(raw.industry),
    ownerName: safeString(raw.owner_name ?? raw.ownerName),
    submittedAt: safeString(raw.submitted_at ?? raw.submittedAt),
  };
}

function parseMatch(raw: Record<string, unknown>): MatchItem {
  const seedRaw = (raw.seed ?? raw.seed_store ?? {}) as Record<string, unknown>;
  const regRaw = (raw.registered ?? raw.registered_store ?? raw.store ?? {}) as Record<string, unknown>;
  const statusVal = safeString(raw.status, 'pending').toLowerCase();
  const validStatuses = ['pending', 'approved', 'rejected', 'merged'] as const;

  return {
    id: safeString(raw.id),
    seed: parseSeed(seedRaw),
    registered: parseRegistered(regRaw),
    similarity: safeNumber(raw.similarity ?? raw.confidence ?? raw.score),
    status: validStatuses.includes(statusVal as (typeof validStatuses)[number])
      ? (statusVal as (typeof validStatuses)[number])
      : 'pending',
    matchedAt: safeString(raw.matched_at ?? raw.created_at ?? raw.matchedAt ?? raw.createdAt),
  };
}

function formatDate(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function similarityColor(similarity: number) {
  if (similarity >= 90) return { bg: 'bg-emerald-100 text-emerald-700', ring: 'ring-emerald-300' };
  if (similarity >= 80) return { bg: 'bg-amber-100 text-amber-700', ring: 'ring-amber-300' };
  return { bg: 'bg-red-100 text-red-700', ring: 'ring-red-300' };
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function MatchQueuePage() {
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [processing, setProcessing] = useState<string | null>(null); // matchId being processed

  // ── Data loading ─────────────────────────────────────────────────────────

  const loadMatches = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getMatchQueue({ limit: 200 });

      // Safely extract matches array from various possible response shapes
      const rawList = Array.isArray(response)
        ? response
        : Array.isArray((response as Record<string, unknown>)?.matches)
          ? (response as Record<string, unknown>).matches
          : Array.isArray((response as Record<string, unknown>)?.data)
            ? (response as Record<string, unknown>).data
            : [];

      const parsed = rawList.map((item: unknown) =>
        parseMatch(item as Record<string, unknown>)
      );

      setMatches(parsed);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Không thể tải danh sách ghép nối';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  // ── Action handlers ──────────────────────────────────────────────────────

  const handleConfirmAction = async () => {
    if (!confirmAction) return;
    const { matchId, action } = confirmAction;

    try {
      setProcessing(matchId);
      await api.processMatch(matchId, action);

      // Optimistically update status
      setMatches((prev) =>
        prev.map((m) =>
          m.id === matchId ? { ...m, status: action === 'approve' ? 'approved' : 'rejected' } : m
        )
      );

      toast.success(action === 'approve' ? 'Đã phê duyệt ghép nối' : 'Đã từ chối ghép nối');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Thao tác thất bại';
      toast.error(message);
      // Refresh from server on failure
      await loadMatches();
    } finally {
      setProcessing(null);
      setConfirmAction(null);
    }
  };

  // ── Derived data ─────────────────────────────────────────────────────────

  const filteredMatches = matches.filter((m) => {
    const matchesStatus = statusFilter === 'all' || m.status === statusFilter;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      m.seed.name.toLowerCase().includes(q) ||
      m.seed.address.toLowerCase().includes(q) ||
      m.registered.name.toLowerCase().includes(q) ||
      m.registered.address.toLowerCase().includes(q) ||
      m.registered.ownerName.toLowerCase().includes(q);
    return matchesStatus && matchesSearch;
  });

  const stats = {
    total: matches.length,
    pending: matches.filter((m) => m.status === 'pending').length,
    approved: matches.filter((m) => m.status === 'approved').length,
    rejected: matches.filter((m) => m.status === 'rejected').length,
  };

  // ── Status badge ─────────────────────────────────────────────────────────

  const renderStatusBadge = (status: MatchItem['status']) => {
    const cfg: Record<MatchItem['status'], { label: string; cls: string }> = {
      pending: { label: 'Chờ xử lý', cls: 'bg-amber-100 text-amber-700' },
      approved: { label: 'Đã duyệt', cls: 'bg-emerald-100 text-emerald-700' },
      rejected: { label: 'Đã từ chối', cls: 'bg-red-100 text-red-700' },
      merged: { label: 'Đã gộp', cls: 'bg-sky-100 text-sky-700' },
    };
    const { label, cls } = cfg[status];
    return <Badge className={`${cls} border-0 font-medium`}>{label}</Badge>;
  };

  // ── Render: Loading skeleton ─────────────────────────────────────────────

  if (loading && matches.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-56 rounded-xl" />
        ))}
      </div>
    );
  }

  // ── Render: Error state ──────────────────────────────────────────────────

  if (error && matches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <AlertTriangle className="w-16 h-16 text-red-400" />
        <h2 className="text-xl font-semibold text-gray-900">Không thể tải dữ liệu</h2>
        <p className="text-gray-500 max-w-md text-center">{error}</p>
        <Button onClick={loadMatches} className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Thử lại
        </Button>
      </div>
    );
  }

  // ── Render: Main ─────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Hàng đợi ghép nối</h1>
          <p className="text-gray-500 mt-1">
            Ghép nối dữ liệu seed với cửa hàng đã đăng ký
          </p>
        </div>
        <Button
          variant="outline"
          onClick={loadMatches}
          disabled={loading}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-900">Hướng dẫn ghép nối</h3>
            <p className="text-sm text-amber-800 mt-1">
              Hệ thống tự động so khớp cửa hàng từ dữ liệu seed (OpenStreetMap, thủ công) với cửa hàng
              đã đăng ký. Độ tương đồng ≥90%: Khuyến nghị duyệt, 80–89%: Cần xem xét, &lt;80%: Nên
              từ chối.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Tổng ghép nối</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <Merge className="w-8 h-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Chờ xử lý</p>
                <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
              </div>
              <Clock className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Đã duyệt</p>
                <p className="text-2xl font-bold text-emerald-600">{stats.approved}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Đã từ chối</p>
                <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm theo tên, địa chỉ, chủ sở hữu..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {(
                [
                  ['all', 'Tất cả'],
                  ['pending', 'Chờ xử lý'],
                  ['approved', 'Đã duyệt'],
                  ['rejected', 'Đã từ chối'],
                ] as [StatusFilter, string][]
              ).map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => setStatusFilter(value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    statusFilter === value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Match List */}
      <div className="space-y-4">
        {filteredMatches.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <ArrowLeftRight className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Không tìm thấy kết quả</h3>
              <p className="text-gray-500">
                {searchQuery
                  ? 'Không có ghép nối phù hợp với từ khóa tìm kiếm'
                  : statusFilter !== 'all'
                    ? `Không có ghép nối ở trạng thái "${statusFilter === 'pending' ? 'Chờ xử lý' : statusFilter === 'approved' ? 'Đã duyệt' : 'Đã từ chối'}"`
                    : 'Chưa có ghép nối nào trong hàng đợi'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredMatches.map((match) => {
            const sim = similarityColor(match.similarity);
            const isProcessing = processing === match.id;

            return (
              <Card key={match.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {renderStatusBadge(match.status)}
                      <span className="text-sm text-gray-500">
                        Ngày ghép: {formatDate(match.matchedAt)}
                      </span>
                    </div>
                    <div
                      className={`w-14 h-14 rounded-full flex items-center justify-center font-bold text-sm ring-2 ${sim.bg} ${sim.ring}`}
                    >
                      {match.similarity}%
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-start">
                    {/* Seed Store */}
                    <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 space-y-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Database className="w-4 h-4 text-blue-600" />
                        <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
                          Dữ liệu Seed
                        </span>
                      </div>
                      <h4 className="font-semibold text-gray-900">{match.seed.name || '—'}</h4>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p className="flex items-start gap-1.5">
                          <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          {match.seed.address || '—'}
                        </p>
                        {match.seed.phone && (
                          <p className="flex items-center gap-1.5">
                            <Phone className="w-3.5 h-3.5 flex-shrink-0" />
                            {match.seed.phone}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-2 pt-1">
                          {match.seed.industry && (
                            <Badge variant="secondary" className="text-xs">
                              {match.seed.industry}
                            </Badge>
                          )}
                          {match.seed.source && (
                            <Badge variant="outline" className="text-xs">
                              {match.seed.source === 'openstreetmap' ? 'OSM' : match.seed.source}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Arrow / Comparison indicator */}
                    <div className="hidden md:flex items-center justify-center self-center">
                      <div className="flex flex-col items-center gap-1">
                        <ArrowLeftRight className="w-6 h-6 text-gray-400" />
                        <span className="text-[10px] text-gray-400 font-medium uppercase">So khớp</span>
                      </div>
                    </div>

                    {/* Registered Store */}
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 space-y-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Store className="w-4 h-4 text-emerald-600" />
                        <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">
                          Cửa hàng đăng ký
                        </span>
                      </div>
                      <h4 className="font-semibold text-gray-900">{match.registered.name || '—'}</h4>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p className="flex items-start gap-1.5">
                          <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          {match.registered.address || '—'}
                        </p>
                        {match.registered.phone && (
                          <p className="flex items-center gap-1.5">
                            <Phone className="w-3.5 h-3.5 flex-shrink-0" />
                            {match.registered.phone}
                          </p>
                        )}
                        {match.registered.ownerName && (
                          <p className="text-gray-500">
                            Chủ sở hữu: {match.registered.ownerName}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-2 pt-1">
                          {match.registered.industry && (
                            <Badge variant="secondary" className="text-xs">
                              {match.registered.industry}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>

                {/* Actions */}
                {match.status === 'pending' && (
                  <CardFooter className="pt-0 flex items-center justify-end gap-2">
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={isProcessing}
                      onClick={() => setConfirmAction({ matchId: match.id, action: 'reject' })}
                      className="gap-1.5"
                    >
                      {isProcessing && confirmAction?.action === 'reject' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      Từ chối
                    </Button>
                    <Button
                      size="sm"
                      disabled={isProcessing}
                      onClick={() => setConfirmAction({ matchId: match.id, action: 'approve' })}
                      className="gap-1.5"
                    >
                      {isProcessing && confirmAction?.action === 'approve' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <CheckCircle className="w-4 h-4" />
                      )}
                      Phê duyệt
                    </Button>
                  </CardFooter>
                )}

                {match.status !== 'pending' && (
                  <CardFooter className="pt-0 flex items-center justify-end">
                    <span className="text-sm text-gray-400">
                      {match.status === 'approved' && '✓ Ghép nối đã được phê duyệt'}
                      {match.status === 'rejected' && '✗ Ghép nối đã bị từ chối'}
                      {match.status === 'merged' && '↻ Dữ liệu đã được gộp'}
                    </span>
                  </CardFooter>
                )}
              </Card>
            );
          })
        )}
      </div>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmAction !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmAction(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmAction?.action === 'approve'
                ? 'Xác nhận phê duyệt'
                : 'Xác nhận từ chối'}
            </DialogTitle>
            <DialogDescription>
              {confirmAction?.action === 'approve'
                ? 'Bạn có chắc chắn muốn phê duyệt ghép nối này? Dữ liệu seed và cửa hàng đăng ký sẽ được liên kết.'
                : 'Bạn có chắc chắn muốn từ chối ghép nối này? Hành động này có thể được hoàn tác sau.'}
            </DialogDescription>
          </DialogHeader>

          {confirmAction && (
            <div className="rounded-lg border p-3 bg-gray-50 text-sm space-y-1">
              <p>
                <span className="font-medium">Ghép nối ID:</span>{' '}
                <code className="bg-gray-200 px-1.5 py-0.5 rounded text-xs">
                  {confirmAction.matchId}
                </code>
              </p>
              {(() => {
                const m = matches.find((x) => x.id === confirmAction.matchId);
                if (!m) return null;
                return (
                  <>
                    <p>
                      <span className="font-medium">Seed:</span> {m.seed.name}
                    </p>
                    <p>
                      <span className="font-medium">Đăng ký:</span> {m.registered.name}
                    </p>
                    <p>
                      <span className="font-medium">Độ tương đồng:</span> {m.similarity}%
                    </p>
                  </>
                );
              })()}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmAction(null)}
              disabled={processing !== null}
            >
              Huỷ
            </Button>
            <Button
              variant={confirmAction?.action === 'approve' ? 'default' : 'destructive'}
              onClick={handleConfirmAction}
              disabled={processing !== null}
              className="gap-1.5"
            >
              {processing && <Loader2 className="w-4 h-4 animate-spin" />}
              {confirmAction?.action === 'approve' ? 'Phê duyệt' : 'Từ chối'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
