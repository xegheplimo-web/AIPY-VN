import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Activity,
  Server,
  Database,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  Zap,
  Layers,
  HardDrive,
  Cpu,
  Globe,
  Info,
} from 'lucide-react';
import api from '../services/api';

// ── Types ────────────────────────────────────────────────────────────────────

type ServiceStatusValue = 'ok' | 'error' | 'disabled' | 'unknown';
type OverallStatus = 'healthy' | 'degraded' | 'down';

interface HealthServiceEntry {
  status: ServiceStatusValue;
  latency_ms?: number;
  error?: string;
}

interface HealthResponse {
  status: string;
  version?: string;
  environment?: string;
  services: Record<string, string | HealthServiceEntry>;
  uptime?: string;
  timestamp?: string;
}

interface ServiceCard {
  key: string;
  name: string;
  icon: React.ReactNode;
  status: 'UP' | 'DOWN' | 'DEGRADED';
  latencyMs: number | null;
  error: string | null;
  lastChecked: Date;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function parseServiceStatus(
  raw: string | HealthServiceEntry | undefined
): { status: 'UP' | 'DOWN' | 'DEGRADED'; latencyMs: number | null; error: string | null } {
  if (raw === undefined || raw === null) {
    return { status: 'DOWN', latencyMs: null, error: 'Không có dữ liệu' };
  }

  if (typeof raw === 'string') {
    if (raw === 'ok') return { status: 'UP', latencyMs: null, error: null };
    if (raw === 'disabled') return { status: 'DEGRADED', latencyMs: null, error: 'Dịch vụ bị tắt' };
    if (raw.startsWith('error')) return { status: 'DOWN', latencyMs: null, error: raw.replace('error: ', '') };
    return { status: 'DOWN', latencyMs: null, error: raw };
  }

  // Object form
  const obj = raw as HealthServiceEntry;
  const s = obj.status;
  if (s === 'ok') return { status: 'UP', latencyMs: obj.latency_ms ?? null, error: null };
  if (s === 'disabled') return { status: 'DEGRADED', latencyMs: obj.latency_ms ?? null, error: 'Dịch vụ bị tắt' };
  if (s === 'error') return { status: 'DOWN', latencyMs: obj.latency_ms ?? null, error: obj.error ?? 'Lỗi không xác định' };
  return { status: 'DOWN', latencyMs: obj.latency_ms ?? null, error: obj.error ?? String(s) };
}

function mapOverallStatus(raw: string): OverallStatus {
  if (raw === 'ok' || raw === 'healthy') return 'healthy';
  if (raw === 'degraded') return 'degraded';
  return 'down';
}

function overallFromServices(cards: ServiceCard[]): OverallStatus {
  const hasDown = cards.some((c) => c.status === 'DOWN');
  const hasDegraded = cards.some((c) => c.status === 'DEGRADED');
  if (hasDown) return 'down';
  if (hasDegraded) return 'degraded';
  return 'healthy';
}

// ── Service metadata ─────────────────────────────────────────────────────────

const SERVICE_META: Record<string, { name: string; icon: React.ReactNode }> = {
  database: { name: 'Cơ sở dữ liệu (PostgreSQL)', icon: <Database className="w-5 h-5" /> },
  cache: { name: 'Redis Cache', icon: <Zap className="w-5 h-5" /> },
  postgis: { name: 'PostGIS', icon: <Layers className="w-5 h-5" /> },
  vector_db: { name: 'Vector DB (Qdrant)', icon: <HardDrive className="w-5 h-5" /> },
};

const REFRESH_INTERVAL = 30; // seconds

// ── Component ────────────────────────────────────────────────────────────────

export default function SystemHealthPage() {
  const [cards, setCards] = useState<ServiceCard[]>([]);
  const [overallStatus, setOverallStatus] = useState<OverallStatus>('healthy');
  const [version, setVersion] = useState<string>('');
  const [environment, setEnvironment] = useState<string>('');
  const [uptime, setUptime] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL);
  const [refreshing, setRefreshing] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState<Date | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoRefreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHealth = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    setError(null);

    try {
      const startTime = performance.now();
      const data: HealthResponse = await api.getSystemHealth();
      const apiLatency = Math.round(performance.now() - startTime);

      const now = new Date();
      const services = data.services ?? {};
      const serviceKeys = Object.keys(services);

      // Build service cards from API response
      const builtCards: ServiceCard[] = serviceKeys.map((key) => {
        const parsed = parseServiceStatus(services[key] as string | HealthServiceEntry);
        const meta = SERVICE_META[key] ?? { name: key, icon: <Server className="w-5 h-5" /> };
        return {
          key,
          name: meta.name,
          icon: meta.icon,
          status: parsed.status,
          latencyMs: parsed.latencyMs,
          error: parsed.error,
          lastChecked: now,
        };
      });

      // Add API Server card (derived from the fact the call succeeded)
      builtCards.push({
        key: 'api_server',
        name: 'API Server',
        icon: <Globe className="w-5 h-5" />,
        status: 'UP',
        latencyMs: apiLatency,
        error: null,
        lastChecked: now,
      });

      setCards(builtCards);
      setOverallStatus(mapOverallStatus(data.status ?? '') || overallFromServices(builtCards));
      setVersion(data.version ?? '');
      setEnvironment(data.environment ?? '');
      setUptime(data.uptime ?? '');
      setLastFetchTime(now);
    } catch (err: any) {
      console.error('Không thể tải trạng thái hệ thống:', err);
      setError(err?.message || 'Không thể kết nối đến máy chủ');

      // If we had previous data, mark API server as down but keep other services
      if (cards.length > 0) {
        setCards((prev) =>
          prev.map((c) =>
            c.key === 'api_server'
              ? { ...c, status: 'DOWN' as const, error: 'Không thể kết nối', lastChecked: new Date() }
              : c
          )
        );
        setOverallStatus('down');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  // Auto-refresh interval
  useEffect(() => {
    if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    if (autoRefresh) {
      setCountdown(REFRESH_INTERVAL);
      autoRefreshRef.current = setInterval(() => {
        fetchHealth();
        setCountdown(REFRESH_INTERVAL);
      }, REFRESH_INTERVAL * 1000);
    }
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    };
  }, [autoRefresh, fetchHealth]);

  // Countdown timer
  useEffect(() => {
    if (countdownRef.current) clearInterval(countdownRef.current);
    if (autoRefresh) {
      countdownRef.current = setInterval(() => {
        setCountdown((prev) => (prev <= 1 ? REFRESH_INTERVAL : prev - 1));
      }, 1000);
    }
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [autoRefresh]);

  const handleManualRefresh = () => {
    fetchHealth(true);
    setCountdown(REFRESH_INTERVAL);
  };

  // ── Status helpers ──────────────────────────────────────────────────────

  const statusColor = (status: 'UP' | 'DOWN' | 'DEGRADED') => {
    if (status === 'UP') return 'text-emerald-600';
    if (status === 'DOWN') return 'text-red-600';
    return 'text-amber-600';
  };

  const statusBg = (status: 'UP' | 'DOWN' | 'DEGRADED') => {
    if (status === 'UP') return 'bg-emerald-100 text-emerald-700';
    if (status === 'DOWN') return 'bg-red-100 text-red-700';
    return 'bg-amber-100 text-amber-700';
  };

  const statusDot = (status: 'UP' | 'DOWN' | 'DEGRADED') => {
    if (status === 'UP') return 'bg-emerald-500';
    if (status === 'DOWN') return 'bg-red-500';
    return 'bg-amber-500';
  };

  const statusLabel = (status: 'UP' | 'DOWN' | 'DEGRADED') => {
    if (status === 'UP') return 'Hoạt động';
    if (status === 'DOWN') return 'Ngưng hoạt động';
    return 'Giảm hiệu suất';
  };

  const overallColorMap: Record<OverallStatus, { bg: string; text: string; border: string }> = {
    healthy: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
    degraded: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
    down: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  };

  const overallLabelMap: Record<OverallStatus, string> = {
    healthy: 'Hệ thống hoạt động bình thường',
    degraded: 'Hệ thống giảm hiệu suất',
    down: 'Hệ thống gặp sự cố',
  };

  const overallIconMap: Record<OverallStatus, React.ReactNode> = {
    healthy: <CheckCircle className="w-8 h-8 text-emerald-500" />,
    degraded: <AlertTriangle className="w-8 h-8 text-amber-500" />,
    down: <XCircle className="w-8 h-8 text-red-500" />,
  };

  // ── Loading state ───────────────────────────────────────────────────────

  if (loading && cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="relative">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-emerald-500" />
          <Activity className="w-6 h-6 text-emerald-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="text-gray-500 text-sm">Đang kiểm tra trạng thái hệ thống...</p>
      </div>
    );
  }

  // ── Error state (no data at all) ────────────────────────────────────────

  if (error && cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center max-w-md">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-red-800 mb-2">Không thể tải dữ liệu</h2>
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={() => fetchHealth(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  const oc = overallColorMap[overallStatus];
  const upCount = cards.filter((c) => c.status === 'UP').length;
  const downCount = cards.filter((c) => c.status === 'DOWN').length;
  const degradedCount = cards.filter((c) => c.status === 'DEGRADED').length;

  // ── Render ──────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trạng thái hệ thống</h1>
          <p className="text-gray-500 mt-1">Theo dõi hiệu suất và trạng thái các dịch vụ</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              autoRefresh
                ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
            Tự động làm mới
          </button>
          {/* Manual refresh */}
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-sm font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Làm mới
          </button>
        </div>
      </div>

      {/* Countdown & last fetch info */}
      {autoRefresh && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Clock className="w-3.5 h-3.5" />
          <span>
            Làm mới sau {countdown}s
          </span>
          {lastFetchTime && (
            <>
              <span className="text-gray-300">•</span>
              <span>Cập nhật lúc {lastFetchTime.toLocaleTimeString('vi-VN')}</span>
            </>
          )}
        </div>
      )}

      {/* Overall Status Banner */}
      <div className={`${oc.bg} ${oc.border} border rounded-xl p-6`}>
        <div className="flex items-center gap-4">
          {overallIconMap[overallStatus]}
          <div className="flex-1">
            <h2 className={`text-lg font-semibold ${oc.text}`}>{overallLabelMap[overallStatus]}</h2>
            <p className="text-sm text-gray-600 mt-0.5">
              {upCount} hoạt động
              {degradedCount > 0 && <> · {degradedCount} giảm hiệu suất</>}
              {downCount > 0 && <> · {downCount} ngưng hoạt động</>}
            </p>
          </div>
          {/* Version & Environment */}
          <div className="hidden sm:flex items-center gap-4 text-sm">
            {version && (
              <div className="flex items-center gap-1.5 text-gray-600">
                <Info className="w-4 h-4" />
                <span>Phiên bản: <strong>{version}</strong></span>
              </div>
            )}
            {environment && (
              <span
                className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                  environment === 'production'
                    ? 'bg-emerald-100 text-emerald-700'
                    : environment === 'staging'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                {environment === 'production' ? 'Sản xuất' : environment === 'staging' ? 'Staging' : environment}
              </span>
            )}
          </div>
        </div>
        {/* Mobile version info */}
        {(version || environment) && (
          <div className="flex sm:hidden items-center gap-4 text-sm mt-3 pt-3 border-t border-gray-200/60">
            {version && (
              <span className="text-gray-600">Phiên bản: <strong>{version}</strong></span>
            )}
            {environment && (
              <span className="text-gray-600">Môi trường: <strong>{environment}</strong></span>
            )}
          </div>
        )}
      </div>

      {/* Uptime info */}
      {uptime && (
        <div className="flex items-center gap-2 bg-white border rounded-xl p-4">
          <Cpu className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-600">Thời gian hoạt động liên tục:</span>
          <span className="text-sm font-semibold text-gray-900">{uptime}</span>
        </div>
      )}

      {/* Service Status Cards */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Trạng thái dịch vụ
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map((card) => (
            <div
              key={card.key}
              className={`relative rounded-xl border p-4 transition ${
                card.status === 'UP'
                  ? 'border-emerald-200 bg-emerald-50/30'
                  : card.status === 'DOWN'
                  ? 'border-red-200 bg-red-50/30'
                  : 'border-amber-200 bg-amber-50/30'
              }`}
            >
              {/* Status dot pulse */}
              <div className="absolute top-4 right-4">
                <span className={`relative flex h-3 w-3`}>
                  {card.status === 'UP' && (
                    <>
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
                    </>
                  )}
                  {card.status === 'DOWN' && (
                    <>
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
                    </>
                  )}
                  {card.status === 'DEGRADED' && (
                    <>
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500" />
                    </>
                  )}
                </span>
              </div>

              {/* Icon & Name */}
              <div className="flex items-center gap-3 mb-3">
                <div className={`${statusColor(card.status)}`}>{card.icon}</div>
                <h4 className="font-medium text-gray-900 text-sm">{card.name}</h4>
              </div>

              {/* Status badge */}
              <div className="mb-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusBg(card.status)}`}>
                  {statusLabel(card.status)}
                </span>
              </div>

              {/* Latency */}
              {card.latencyMs !== null && (
                <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-2">
                  <Zap className="w-3.5 h-3.5" />
                  <span>Độ trễ: <strong className="text-gray-700">{card.latencyMs}ms</strong></span>
                </div>
              )}

              {/* Error message */}
              {card.error && (
                <div className="flex items-start gap-1.5 text-xs text-red-500 mt-2">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                  <span>{card.error}</span>
                </div>
              )}

              {/* Last checked */}
              <div className="flex items-center gap-1.5 text-xs text-gray-400 mt-3 pt-2 border-t border-gray-100">
                <Clock className="w-3 h-3" />
                <span>Kiểm tra lúc: {card.lastChecked.toLocaleTimeString('vi-VN')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Table */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Tổng quan dịch vụ
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-500">Dịch vụ</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Trạng thái</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Độ trễ</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Ghi chú</th>
                <th className="text-left py-3 px-4 font-medium text-gray-500">Kiểm tra lúc</th>
              </tr>
            </thead>
            <tbody>
              {cards.map((card) => (
                <tr key={card.key} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${statusDot(card.status)}`} />
                      <span className="font-medium text-gray-900">{card.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusBg(card.status)}`}>
                      {statusLabel(card.status)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600">
                    {card.latencyMs !== null ? `${card.latencyMs}ms` : '—'}
                  </td>
                  <td className="py-3 px-4 text-gray-500">
                    {card.error || '—'}
                  </td>
                  <td className="py-3 px-4 text-gray-500">
                    {card.lastChecked.toLocaleTimeString('vi-VN')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info footer */}
      <div className="text-xs text-gray-400 text-center pb-4">
        Tự động làm mới mỗi {REFRESH_INTERVAL} giây · Dữ liệu từ <code className="bg-gray-100 px-1 rounded">GET /health</code>
      </div>
    </div>
  );
}
