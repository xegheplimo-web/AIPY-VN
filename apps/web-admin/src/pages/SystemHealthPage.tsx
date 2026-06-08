import { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  Cpu, 
  HardDrive, 
  MemoryStick,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  Zap,
  Globe,
  Users,
  ShoppingBag
} from 'lucide-react';

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
}

interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'degraded';
  uptime: string;
  lastCheck: Date;
}

export default function SystemHealthPage() {
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSystemData();
    if (autoRefresh) {
      const interval = setInterval(loadSystemData, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadSystemData = async () => {
    try {
      // Mock data - sẽ thay bằng API call sau
      const mockMetrics: SystemMetric[] = [
        { name: 'CPU Usage', value: 45, unit: '%', status: 'healthy', trend: 'stable' },
        { name: 'Memory Usage', value: 72, unit: '%', status: 'warning', trend: 'up' },
        { name: 'Disk Usage', value: 58, unit: '%', status: 'healthy', trend: 'stable' },
        { name: 'Network I/O', value: 125, unit: 'MB/s', status: 'healthy', trend: 'up' },
        { name: 'Database Connections', value: 45, unit: '', status: 'healthy', trend: 'stable' },
        { name: 'Cache Hit Rate', value: 85, unit: '%', status: 'healthy', trend: 'up' },
      ];

      const mockServices: ServiceStatus[] = [
        { name: 'API Server', status: 'running', uptime: '15d 4h 23m', lastCheck: new Date() },
        { name: 'Database (PostgreSQL)', status: 'running', uptime: '15d 4h 25m', lastCheck: new Date() },
        { name: 'Redis Cache', status: 'running', uptime: '15d 4h 20m', lastCheck: new Date() },
        { name: 'Search Engine', status: 'running', uptime: '15d 4h 15m', lastCheck: new Date() },
        { name: 'Worker Queue', status: 'running', uptime: '15d 4h 10m', lastCheck: new Date() },
        { name: 'Email Service', status: 'degraded', uptime: '15d 4h 5m', lastCheck: new Date() },
      ];

      setMetrics(mockMetrics);
      setServices(mockServices);
    } catch (err) {
      console.error('Failed to load system data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config = {
      healthy: { label: 'Healthy', color: 'bg-green-100 text-green-700' },
      warning: { label: 'Warning', color: 'bg-yellow-100 text-yellow-700' },
      critical: { label: 'Critical', color: 'bg-red-100 text-red-700' },
      running: { label: 'Running', color: 'bg-green-100 text-green-700' },
      stopped: { label: 'Stopped', color: 'bg-red-100 text-red-700' },
      degraded: { label: 'Degraded', color: 'bg-yellow-100 text-yellow-700' },
    };
    const { label, color } = config[status as keyof typeof config];
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${color}`}>{label}</span>;
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <Activity className="w-4 h-4 text-green-600" />;
    if (trend === 'down') return <Activity className="w-4 h-4 text-red-600" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
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
          <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
          <p className="text-gray-500 mt-1">Monitor system performance and service status</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              autoRefresh ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Auto Refresh
          </button>
          <button
            onClick={loadSystemData}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">12,456</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
          <div className="flex items-center gap-1 mt-2 text-sm text-green-600">
            <Activity className="w-4 h-4" />
            <span>+12.5% this week</span>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Active Stores</p>
              <p className="text-2xl font-bold text-gray-900">1,234</p>
            </div>
            <ShoppingBag className="w-8 h-8 text-purple-500" />
          </div>
          <div className="flex items-center gap-1 mt-2 text-sm text-green-600">
            <Activity className="w-4 h-4" />
            <span>+8.3% this week</span>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Orders Today</p>
              <p className="text-2xl font-bold text-gray-900">456</p>
            </div>
            <ShoppingBag className="w-8 h-8 text-green-500" />
          </div>
          <div className="flex items-center gap-1 mt-2 text-sm text-green-600">
            <Activity className="w-4 h-4" />
            <span>+15.2% vs yesterday</span>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">API Requests/min</p>
              <p className="text-2xl font-bold text-gray-900">2,345</p>
            </div>
            <Zap className="w-8 h-8 text-yellow-500" />
          </div>
          <div className="flex items-center gap-1 mt-2 text-sm text-yellow-600">
            <Activity className="w-4 h-4" />
            <span>Peak load warning</span>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5" />
          System Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics.map((metric) => (
            <div key={metric.name} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">{metric.name}</span>
                {getTrendIcon(metric.trend)}
              </div>
              <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-gray-900">
                  {metric.value}
                </span>
                <span className="text-sm text-gray-500 mb-1">{metric.unit}</span>
              </div>
              <div className="mt-2">
                {getStatusBadge(metric.status)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Service Status */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Service Status
        </h3>
        <div className="space-y-3">
          {services.map((service) => (
            <div key={service.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  service.status === 'running' ? 'bg-green-500' :
                  service.status === 'stopped' ? 'bg-red-500' :
                  'bg-yellow-500'
                }`} />
                <div>
                  <p className="font-medium text-gray-900">{service.name}</p>
                  <p className="text-sm text-gray-500">Uptime: {service.uptime}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">
                  Last check: {service.lastCheck.toLocaleTimeString('vi-VN')}
                </span>
                {getStatusBadge(service.status)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5" />
            CPU & Memory
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">CPU Usage</span>
                <span className="font-medium">45%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '45%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Memory Usage</span>
                <span className="font-medium text-yellow-600">72%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '72%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Disk Usage</span>
                <span className="font-medium">58%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '58%' }} />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Database Performance
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Connection Pool</span>
                <span className="font-medium">45/100</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '45%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Query Latency</span>
                <span className="font-medium">25ms</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '25%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Cache Hit Rate</span>
                <span className="font-medium text-green-600">85%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '85%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          Recent Alerts
        </h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-yellow-900">Memory usage above 70%</p>
              <p className="text-sm text-yellow-700 mt-1">System memory usage has exceeded 70% threshold</p>
              <p className="text-xs text-yellow-600 mt-2">10 minutes ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-blue-900">Database backup completed</p>
              <p className="text-sm text-blue-700 mt-1">Daily backup completed successfully</p>
              <p className="text-xs text-blue-600 mt-2">1 hour ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
