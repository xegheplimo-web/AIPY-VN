import {
  Ban,
  MoreVertical,
  Phone,
  Search,
  ShieldCheck,
  User as UserIcon,
  XCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'customer' | 'owner' | 'admin';
  status: 'active' | 'suspended' | 'banned';
  createdAt: Date;
  lastLogin?: Date;
  addresses: number;
  orders: number;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [filter, setFilter] = useState<'all' | 'active' | 'suspended' | 'banned'>('all');
  const [roleFilter, setRoleFilter] = useState<'all' | 'customer' | 'owner' | 'admin'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      // Mock data - sẽ thay bằng API call sau
      const mockUsers: User[] = [
        {
          id: '1',
          name: 'Nguyễn Văn A',
          email: 'nguyenvana@example.com',
          phone: '0901234567',
          role: 'customer',
          status: 'active',
          createdAt: new Date('2024-01-15'),
          lastLogin: new Date(),
          addresses: 2,
          orders: 15,
        },
        {
          id: '2',
          name: 'Trần Thị B',
          email: 'tranhib@example.com',
          phone: '0912345678',
          role: 'owner',
          status: 'active',
          createdAt: new Date('2024-02-20'),
          lastLogin: new Date(),
          addresses: 1,
          orders: 45,
        },
        {
          id: '3',
          name: 'Lê Văn C',
          email: 'levanc@example.com',
          phone: '0923456789',
          role: 'customer',
          status: 'suspended',
          createdAt: new Date('2024-03-10'),
          lastLogin: new Date('2024-05-01'),
          addresses: 1,
          orders: 8,
        },
        {
          id: '4',
          name: 'Admin User',
          email: 'admin@aishop.vn',
          phone: '0934567890',
          role: 'admin',
          status: 'active',
          createdAt: new Date('2024-01-01'),
          lastLogin: new Date(),
          addresses: 0,
          orders: 0,
        },
      ];
      setUsers(mockUsers);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async (userId: string) => {
    try {
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'suspended' as const } : u))
      );
    } catch (err) {
      alert('Khóa tài khoản thất bại');
    }
  };

  const handleBan = async (userId: string) => {
    const reason = prompt('Lý do khóa tài khoản:');
    if (!reason) return;

    try {
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'banned' as const } : u))
      );
    } catch (err) {
      alert('Khóa tài khoản thất bại');
    }
  };

  const handleActivate = async (userId: string) => {
    try {
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, status: 'active' as const } : u))
      );
    } catch (err) {
      alert('Kích hoạt tài khoản thất bại');
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesFilter = filter === 'all' || u.status === filter;
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const matchesSearch =
      searchQuery === '' ||
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.phone.includes(searchQuery);
    return matchesFilter && matchesRole && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    const config = {
      active: { label: 'Hoạt động', color: 'bg-green-100 text-green-700' },
      suspended: { label: 'Tạm khóa', color: 'bg-yellow-100 text-yellow-700' },
      banned: { label: 'Đã khóa', color: 'bg-red-100 text-red-700' },
    };
    const { label, color } = config[status as keyof typeof config];
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${color}`}>{label}</span>;
  };

  const getRoleBadge = (role: string) => {
    const config = {
      customer: { label: 'Khách hàng', color: 'bg-blue-100 text-blue-700' },
      owner: { label: 'Chủ cửa hàng', color: 'bg-purple-100 text-purple-700' },
      admin: { label: 'Quản trị viên', color: 'bg-red-100 text-red-700' },
    };
    const { label, color } = config[role as keyof typeof config];
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
          <h1 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h1>
          <p className="text-gray-500 mt-1">Quản lý tài khoản người dùng</p>
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
              placeholder="Tìm kiếm người dùng..."
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
              <option value="active">Hoạt động</option>
              <option value="suspended">Tạm khóa</option>
              <option value="banned">Đã khóa</option>
            </select>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as any)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tất cả vai trò</option>
              <option value="customer">Khách hàng</option>
              <option value="owner">Chủ cửa hàng</option>
              <option value="admin">Quản trị viên</option>
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
              <p className="text-2xl font-bold text-gray-900">{users.length}</p>
            </div>
            <UserIcon className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Hoạt động</p>
              <p className="text-2xl font-bold text-green-600">
                {users.filter((u) => u.status === 'active').length}
              </p>
            </div>
            <ShieldCheck className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tạm khóa</p>
              <p className="text-2xl font-bold text-yellow-600">
                {users.filter((u) => u.status === 'suspended').length}
              </p>
            </div>
            <Ban className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã khóa</p>
              <p className="text-2xl font-bold text-red-600">
                {users.filter((u) => u.status === 'banned').length}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* User List */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left py-3 px-4 font-medium text-gray-600">Người dùng</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Liên hệ</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Vai trò</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Trạng thái</th>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Ngày tham gia</th>
              <th className="text-right py-3 px-4 font-medium text-gray-600">Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-gray-500">
                  Không tìm thấy kết quả
                </td>
              </tr>
            ) : (
              filteredUsers.map((user) => (
                <tr key={user.id} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <UserIcon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-1 text-gray-600">
                        <Phone size={14} /> {user.phone}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">{getRoleBadge(user.role)}</td>
                  <td className="py-4 px-4">{getStatusBadge(user.status)}</td>
                  <td className="py-4 px-4 text-sm text-gray-600">
                    {user.createdAt.toLocaleDateString('vi-VN')}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setSelectedUser(user)}
                        className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                        title="Xem chi tiết"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                      {user.status === 'active' && (
                        <>
                          <button
                            onClick={() => handleSuspend(user.id)}
                            className="p-2 bg-yellow-100 text-yellow-600 rounded-lg hover:bg-yellow-200"
                            title="Tạm khóa"
                          >
                            <Ban className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleBan(user.id)}
                            className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                            title="Khóa tài khoản"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      {user.status !== 'active' && (
                        <button
                          onClick={() => handleActivate(user.id)}
                          className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                          title="Kích hoạt"
                        >
                          <ShieldCheck className="w-4 h-4" />
                        </button>
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
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b">
              <h2 className="text-xl font-bold">Chi tiết người dùng</h2>
              <button
                onClick={() => setSelectedUser(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <UserIcon className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">{selectedUser.name}</h3>
                  <p className="text-gray-500">{selectedUser.email}</p>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Số điện thoại:</span>
                  <span className="font-medium">{selectedUser.phone}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Vai trò:</span>
                  <span>{getRoleBadge(selectedUser.role)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Trạng thái:</span>
                  <span>{getStatusBadge(selectedUser.status)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Ngày tham gia:</span>
                  <span className="font-medium">
                    {selectedUser.createdAt.toLocaleDateString('vi-VN')}
                  </span>
                </div>
                {selectedUser.lastLogin && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Đăng nhập lần cuối:</span>
                    <span className="font-medium">
                      {selectedUser.lastLogin.toLocaleString('vi-VN')}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Số địa chỉ:</span>
                  <span className="font-medium">{selectedUser.addresses}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Số đơn hàng:</span>
                  <span className="font-medium">{selectedUser.orders}</span>
                </div>
              </div>
            </div>
            <div className="p-6 border-t flex gap-3 justify-end">
              <button
                onClick={() => setSelectedUser(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Đóng
              </button>
              {selectedUser.status === 'active' && (
                <button
                  onClick={() => {
                    handleSuspend(selectedUser.id);
                    setSelectedUser(null);
                  }}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                >
                  Tạm khóa
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
