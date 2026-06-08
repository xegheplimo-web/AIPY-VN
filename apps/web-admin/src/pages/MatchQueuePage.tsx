import {
  AlertTriangle,
  Building2,
  CheckCircle,
  MapPin,
  Merge,
  Percent,
  Search,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface SeedStore {
  id: string;
  name: string;
  address: string;
  phone: string;
  latitude: number;
  longitude: number;
  industry: string;
  source: 'openstreetmap' | 'manual';
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
  submittedAt: Date;
}

interface Match {
  seed: SeedStore;
  registered: RegisteredStore;
  similarity: number;
  status: 'pending' | 'approved' | 'rejected' | 'merged';
}

export default function MatchQueuePage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'high' | 'medium' | 'low'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMatches();
  }, []);

  const loadMatches = async () => {
    try {
      // Mock data - sẽ thay bằng API call sau
      const mockMatches: Match[] = [
        {
          seed: {
            id: 'seed-1',
            name: 'Nhà thuốc An Khang',
            address: '123 Nguyễn Trãi, Quận 1, TP.HCM',
            phone: '0901234567',
            latitude: 10.7726,
            longitude: 106.698,
            industry: 'Dược phẩm',
            source: 'openstreetmap',
          },
          registered: {
            id: 'reg-1',
            name: 'Nhà thuốc An Khang Q1',
            address: '123 Nguyễn Trãi, Quận 1, TP.HCM',
            phone: '0901234567',
            email: 'anhkang@example.com',
            latitude: 10.7726,
            longitude: 106.698,
            industry: 'Dược phẩm',
            ownerName: 'Nguyễn Văn A',
            submittedAt: new Date(),
          },
          similarity: 96,
          status: 'pending',
        },
        {
          seed: {
            id: 'seed-2',
            name: 'Nhà thuốc Long Châu',
            address: '456 Lê Lợi, Quận 3, TP.HCM',
            phone: '0912345678',
            latitude: 10.785,
            longitude: 106.695,
            industry: 'Dược phẩm',
            source: 'openstreetmap',
          },
          registered: {
            id: 'reg-2',
            name: 'Nhà thuốc Long Châu Lê Lợi',
            address: '456 Lê Lợi, Quận 3, TP.HCM',
            phone: '0912345678',
            email: 'longchau@example.com',
            latitude: 10.785,
            longitude: 106.695,
            industry: 'Dược phẩm',
            ownerName: 'Trần Thị B',
            submittedAt: new Date(),
          },
          similarity: 92,
          status: 'pending',
        },
        {
          seed: {
            id: 'seed-3',
            name: 'Nhà thuốc Pharmacity',
            address: '789 Hai Bà Trưng, Quận 5, TP.HCM',
            phone: '0923456789',
            latitude: 10.775,
            longitude: 106.71,
            industry: 'Dược phẩm',
            source: 'manual',
          },
          registered: {
            id: 'reg-3',
            name: 'Pharmacity Q5',
            address: '789 Hai Bà Trưng, Quận 5, TP.HCM',
            phone: '0923456789',
            email: 'pharmacity@example.com',
            latitude: 10.775,
            longitude: 106.71,
            industry: 'Dược phẩm',
            ownerName: 'Lê Văn C',
            submittedAt: new Date(),
          },
          similarity: 88,
          status: 'pending',
        },
        {
          seed: {
            id: 'seed-4',
            name: 'Nhà thuốc Pharmacity',
            address: '123 Võ Văn Tần, Quận 6',
            phone: '0934567890',
            latitude: 10.78,
            longitude: 106.72,
            industry: 'Dược phẩm',
            source: 'openstreetmap',
          },
          registered: {
            id: 'reg-4',
            name: 'Nhà thuốc mới',
            address: '456 Võ Văn Tần, Quận 6',
            phone: '0934567890',
            email: 'new@example.com',
            latitude: 10.78,
            longitude: 106.72,
            industry: 'Dược phẩm',
            ownerName: 'Nguyễn Văn D',
            submittedAt: new Date(),
          },
          similarity: 75,
          status: 'pending',
        },
      ];
      setMatches(mockMatches);
    } catch (err) {
      console.error('Failed to load matches:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (matchId: string) => {
    try {
      setMatches((prev) =>
        prev.map((m) =>
          `${m.seed.id}-${m.registered.id}` === matchId ? { ...m, status: 'approved' as const } : m
        )
      );
    } catch (err) {
      alert('Phê duyệt thất bại');
    }
  };

  const handleMerge = async (matchId: string) => {
    try {
      setMatches((prev) =>
        prev.map((m) =>
          `${m.seed.id}-${m.registered.id}` === matchId ? { ...m, status: 'merged' as const } : m
        )
      );
    } catch (err) {
      alert('Gộp thất bại');
    }
  };

  const handleReject = async (matchId: string) => {
    try {
      setMatches((prev) =>
        prev.map((m) =>
          `${m.seed.id}-${m.registered.id}` === matchId ? { ...m, status: 'rejected' as const } : m
        )
      );
    } catch (err) {
      alert('Từ chối thất bại');
    }
  };

  const filteredMatches = matches.filter((m) => {
    const matchesFilter = filter === 'all' || m.status === filter;
    const matchesSearch =
      searchQuery === '' ||
      m.seed.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.registered.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSimilarity =
      filter === 'high'
        ? m.similarity >= 90
        : filter === 'medium'
          ? m.similarity >= 80 && m.similarity < 90
          : filter === 'low'
            ? m.similarity < 80
            : true;
    return matchesFilter && matchesSearch && matchesSimilarity;
  });

  const getSimilarityBadge = (similarity: number) => {
    if (similarity >= 90) {
      return { label: `${similarity}%`, color: 'bg-green-100 text-green-700' };
    } else if (similarity >= 80) {
      return { label: `${similarity}%`, color: 'bg-yellow-100 text-yellow-700' };
    } else {
      return { label: `${similarity}%`, color: 'bg-red-100 text-red-700' };
    }
  };

  const getStatusBadge = (status: string) => {
    const config = {
      pending: { label: 'Chờ xử lý', color: 'bg-yellow-100 text-yellow-700' },
      approved: { label: 'Đã duyệt', color: 'bg-green-100 text-green-700' },
      rejected: { label: 'Đã từ chối', color: 'bg-red-100 text-red-700' },
      merged: { label: 'Đã gộp', color: 'bg-blue-100 text-blue-700' },
    };
    const { label, color } = config[status as keyof typeof config];
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${color}`}>{label}</span>;
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
          <h1 className="text-2xl font-bold text-gray-900">Match Queue</h1>
          <p className="text-gray-500 mt-1">Ghép dữ liệu seed với cửa hàng đăng ký</p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">Thông tin Match Queue</h3>
            <p className="text-sm text-blue-800 mt-1">
              Hệ thống tự động so sánh cửa hàng từ dữ liệu seed (OpenStreetMap, manual) với cửa hàng
              đăng ký. Similarity ≥90%: Tự động gộp, 80-89%: Cần review, &lt;80%: Từ chối.
            </p>
          </div>
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
            {['all', 'pending', 'high', 'medium', 'low'].map((status) => (
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
                    ? 'Chờ xử lý'
                    : status === 'high'
                      ? '≥90%'
                      : status === 'medium'
                        ? '80-89%'
                        : '&lt;80%'}
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
              <p className="text-sm text-gray-500">Tổng số match</p>
              <p className="text-2xl font-bold text-gray-900">{matches.length}</p>
            </div>
            <Merge className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Similarity cao (≥90%)</p>
              <p className="text-2xl font-bold text-green-600">
                {matches.filter((m) => m.similarity >= 90).length}
              </p>
            </div>
            <Percent className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Trung bình (80-89%)</p>
              <p className="text-2xl font-bold text-yellow-600">
                {matches.filter((m) => m.similarity >= 80 && m.similarity < 90).length}
              </p>
            </div>
            <Percent className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Thấp (&lt;80%)</p>
              <p className="text-2xl font-bold text-red-600">
                {matches.filter((m) => m.similarity < 80).length}
              </p>
            </div>
            <Percent className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Match List */}
      <div className="space-y-4">
        {filteredMatches.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
            <Merge className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Không tìm thấy kết quả</p>
          </div>
        ) : (
          filteredMatches.map((match) => (
            <div
              key={`${match.seed.id}-${match.registered.id}`}
              className="bg-white rounded-xl shadow-sm border p-6"
            >
              <div className="flex items-start gap-6">
                {/* Seed Store */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="w-4 h-4 text-blue-600" />
                    <span className="text-xs text-blue-600 font-medium">SEED DATA</span>
                  </div>
                  <h3 className="font-semibold text-gray-900">{match.seed.name}</h3>
                  <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                    <MapPin size={14} /> {match.seed.address}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm text-gray-600">
                    <span>📞 {match.seed.phone}</span>
                    <span>🏭 {match.seed.industry}</span>
                    <span>📍 {match.seed.source}</span>
                  </div>
                </div>

                {/* Similarity */}
                <div className="flex flex-col items-center justify-center px-4">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-lg ${getSimilarityBadge(match.similarity).color}`}
                  >
                    {match.similarity}%
                  </div>
                  <span className="text-xs text-gray-500 mt-2">Similarity</span>
                </div>

                {/* Registered Store */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="w-4 h-4 text-green-600" />
                    <span className="text-xs text-green-600 font-medium">ĐĂNG KÝ</span>
                  </div>
                  <h3 className="font-semibold text-gray-900">{match.registered.name}</h3>
                  <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                    <MapPin size={14} /> {match.registered.address}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm text-gray-600">
                    <span>📞 {match.registered.phone}</span>
                    <span>👤 {match.registered.ownerName}</span>
                    <span>🏭 {match.registered.industry}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <div className="flex items-center gap-2">{getStatusBadge(match.status)}</div>
                <div className="flex gap-2">
                  {match.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleMerge(`${match.seed.id}-${match.registered.id}`)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                      >
                        <Merge className="w-4 h-4" />
                        Gộp
                      </button>
                      <button
                        onClick={() => handleApprove(`${match.seed.id}-${match.registered.id}`)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Duyệt riêng
                      </button>
                      <button
                        onClick={() => handleReject(`${match.seed.id}-${match.registered.id}`)}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
                      >
                        <XCircle className="w-4 h-4" />
                        Từ chối
                      </button>
                    </>
                  )}
                  {match.status === 'merged' && (
                    <span className="text-sm text-green-600 flex items-center gap-1">
                      <CheckCircle size={16} /> Đã gộp thành công
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
