import {
  Ban,
  Loader2,
  MoreHorizontal,
  Phone,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserCog,
  User as UserIcon,
  Users,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { DataTable } from '../components/ui/DataTable';
import type { ColumnDef } from '@tanstack/react-table';

// ─── Types ───────────────────────────────────────────────────────────────────

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'customer' | 'owner' | 'admin';
  status: 'active' | 'suspended' | 'banned';
  createdAt: Date;
  lastLogin?: Date;
}

type RoleFilter = 'all' | 'customer' | 'owner' | 'admin';

interface ConfirmDialogState {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  variant: 'destructive' | 'default';
  onConfirm: () => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getStatusBadge(status: string) {
  const config = {
    active: { label: 'Hoạt động', className: 'bg-green-100 text-green-700 border-green-200' },
    suspended: { label: 'Tạm khóa', className: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
    banned: { label: 'Đã khóa', className: 'bg-red-100 text-red-700 border-red-200' },
  } as const;
  const entry = config[status as keyof typeof config] ?? config.active;
  return (
    <Badge variant="outline" className={entry.className}>
      {entry.label}
    </Badge>
  );
}

function getRoleBadge(role: string) {
  const config = {
    customer: { label: 'Khách hàng', className: 'bg-sky-100 text-sky-700 border-sky-200' },
    owner: { label: 'Chủ cửa hàng', className: 'bg-violet-100 text-violet-700 border-violet-200' },
    admin: { label: 'Quản trị viên', className: 'bg-rose-100 text-rose-700 border-rose-200' },
  } as const;
  const entry = config[role as keyof typeof config] ?? config.customer;
  return (
    <Badge variant="outline" className={entry.className}>
      {entry.label}
    </Badge>
  );
}

function formatDate(date: Date): string {
  try {
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

/**
 * Safely extract the users array from a potentially nested API response.
 * Handles: { users: [...] }, { data: { users: [...] } }, { data: [...] }
 */
function extractUsers(response: any): any[] {
  if (Array.isArray(response)) return response;
  if (response?.users && Array.isArray(response.users)) return response.users;
  if (response?.data?.users && Array.isArray(response.data.users)) return response.data.users;
  if (response?.data && Array.isArray(response.data)) return response.data;
  return [];
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all');

  // Confirmation dialog
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>({
    open: false,
    title: '',
    description: '',
    confirmLabel: '',
    variant: 'default',
    onConfirm: () => {},
  });

  // Ban reason dialog
  const [banDialog, setBanDialog] = useState<{ open: boolean; userId: string; reason: string }>({
    open: false,
    userId: '',
    reason: '',
  });

  // Loading state for individual actions
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // ─── Load Users ──────────────────────────────────────────────────────────

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getUsers({ limit: 500 });
      const rawUsers = extractUsers(response);

      const transformed: User[] = rawUsers.map((u: any) => ({
        id: u.id ?? u._id ?? '',
        name: u.name ?? u.full_name ?? u.displayName ?? '',
        email: u.email ?? '',
        phone: u.phone ?? '',
        role: u.role ?? 'customer',
        status: u.status ?? 'active',
        createdAt: u.createdAt ? new Date(u.createdAt) : u.created_at ? new Date(u.created_at) : new Date(),
        lastLogin: u.lastLogin ? new Date(u.lastLogin) : u.last_login ? new Date(u.last_login) : undefined,
      }));

      setUsers(transformed);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      setError(err?.message ?? 'Không thể tải danh sách người dùng. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // ─── Actions ─────────────────────────────────────────────────────────────

  const handleSuspend = (userId: string, userName: string) => {
    setConfirmDialog({
      open: true,
      title: 'Tạm khóa người dùng',
      description: `Bạn có chắc muốn tạm khóa tài khoản "${userName}"? Người dùng sẽ không thể đăng nhập cho đến khi được kích hoạt lại.`,
      confirmLabel: 'Tạm khóa',
      variant: 'destructive',
      onConfirm: async () => {
        try {
          setActionLoading(userId);
          await api.suspendUser(userId);
          toast.success(`Đã tạm khóa tài khoản "${userName}"`);
          setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: 'suspended' as const } : u)));
        } catch (err: any) {
          toast.error(err?.message ?? 'Tạm khóa tài khoản thất bại');
        } finally {
          setActionLoading(null);
          setConfirmDialog((prev) => ({ ...prev, open: false }));
        }
      },
    });
  };

  const handleBan = (userId: string) => {
    setBanDialog({ open: true, userId, reason: '' });
  };

  const confirmBan = async () => {
    const { userId, reason } = banDialog;
    const userName = users.find((u) => u.id === userId)?.name ?? '';
    try {
      setActionLoading(userId);
      await api.banUser(userId, reason || 'Vi phạm chính sách');
      toast.success(`Đã khóa tài khoản "${userName}"`);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: 'banned' as const } : u)));
    } catch (err: any) {
      toast.error(err?.message ?? 'Khóa tài khoản thất bại');
    } finally {
      setActionLoading(null);
      setBanDialog({ open: false, userId: '', reason: '' });
    }
  };

  const handleActivate = async (userId: string, userName: string) => {
    try {
      setActionLoading(userId);
      await api.activateUser(userId);
      toast.success(`Đã kích hoạt tài khoản "${userName}"`);
      setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, status: 'active' as const } : u)));
    } catch (err: any) {
      toast.error(err?.message ?? 'Kích hoạt tài khoản thất bại');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    const userName = users.find((u) => u.id === userId)?.name ?? '';
    const roleLabels: Record<string, string> = {
      customer: 'Khách hàng',
      owner: 'Chủ cửa hàng',
      admin: 'Quản trị viên',
    };
    setConfirmDialog({
      open: true,
      title: 'Thay đổi vai trò',
      description: `Bạn có chắc muốn thay đổi vai trò của "${userName}" thành "${roleLabels[newRole] ?? newRole}"?`,
      confirmLabel: 'Xác nhận',
      variant: 'default',
      onConfirm: async () => {
        try {
          setActionLoading(userId);
          await api.updateUserRole(userId, newRole);
          toast.success(`Đã cập nhật vai trò của "${userName}"`);
          setUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role: newRole as User['role'] } : u)));
        } catch (err: any) {
          toast.error(err?.message ?? 'Cập nhật vai trò thất bại');
        } finally {
          setActionLoading(null);
          setConfirmDialog((prev) => ({ ...prev, open: false }));
        }
      },
    });
  };

  // ─── Computed Values ─────────────────────────────────────────────────────

  const filteredUsers = users.filter((u) => {
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      q === '' ||
      u.name.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      u.phone.includes(q) ||
      u.role.toLowerCase().includes(q);
    return matchesRole && matchesSearch;
  });

  const stats = {
    total: users.length,
    active: users.filter((u) => u.status === 'active').length,
    suspended: users.filter((u) => u.status === 'suspended').length,
    banned: users.filter((u) => u.status === 'banned').length,
  };

  const roleTabs: { value: RoleFilter; label: string; count: number }[] = [
    { value: 'all', label: 'Tất cả', count: stats.total },
    { value: 'customer', label: 'Khách hàng', count: users.filter((u) => u.role === 'customer').length },
    { value: 'owner', label: 'Chủ cửa hàng', count: users.filter((u) => u.role === 'owner').length },
    { value: 'admin', label: 'Quản trị viên', count: users.filter((u) => u.role === 'admin').length },
  ];

  // ─── Table Columns ───────────────────────────────────────────────────────

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: 'name',
      header: 'Người dùng',
      cell: ({ row }) => {
        const user = row.original;
        return (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-sky-100 rounded-full flex items-center justify-center flex-shrink-0">
              <UserIcon className="w-4 h-4 text-sky-600" />
            </div>
            <div className="min-w-0">
              <p className="font-medium text-gray-900 truncate">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'phone',
      header: 'Liên hệ',
      cell: ({ row }) => (
        <div className="flex items-center gap-1.5 text-sm text-gray-600">
          <Phone size={14} className="text-gray-400 flex-shrink-0" />
          <span>{row.original.phone || '—'}</span>
        </div>
      ),
    },
    {
      accessorKey: 'role',
      header: 'Vai trò',
      cell: ({ row }) => getRoleBadge(row.original.role),
      filterFn: (row, _columnId, filterValue) => {
        if (filterValue === 'all') return true;
        return row.original.role === filterValue;
      },
    },
    {
      accessorKey: 'status',
      header: 'Trạng thái',
      cell: ({ row }) => getStatusBadge(row.original.status),
    },
    {
      accessorKey: 'createdAt',
      header: 'Ngày tham gia',
      cell: ({ row }) => (
        <span className="text-sm text-gray-600">{formatDate(row.original.createdAt)}</span>
      ),
    },
    {
      id: 'actions',
      header: 'Hành động',
      cell: ({ row }) => {
        const user = row.original;
        const isLoading = actionLoading === user.id;

        return (
          <div className="flex items-center justify-end">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <MoreHorizontal className="h-4 w-4" />
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52">
                <DropdownMenuLabel>Hành động</DropdownMenuLabel>
                <DropdownMenuSeparator />

                {/* Activate / Suspend / Ban based on current status */}
                {user.status === 'active' && (
                  <>
                    <DropdownMenuItem
                      onClick={() => handleSuspend(user.id, user.name)}
                      className="text-yellow-700 focus:text-yellow-700 focus:bg-yellow-50 cursor-pointer"
                    >
                      <Ban className="mr-2 h-4 w-4" />
                      Tạm khóa
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => handleBan(user.id)}
                      className="text-red-700 focus:text-red-700 focus:bg-red-50 cursor-pointer"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Khóa tài khoản
                    </DropdownMenuItem>
                  </>
                )}

                {(user.status === 'suspended' || user.status === 'banned') && (
                  <DropdownMenuItem
                    onClick={() => handleActivate(user.id, user.name)}
                    className="text-green-700 focus:text-green-700 focus:bg-green-50 cursor-pointer"
                  >
                    <ShieldCheck className="mr-2 h-4 w-4" />
                    Kích hoạt
                  </DropdownMenuItem>
                )}

                {user.status === 'suspended' && (
                  <DropdownMenuItem
                    onClick={() => handleBan(user.id)}
                    className="text-red-700 focus:text-red-700 focus:bg-red-50 cursor-pointer"
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Khóa tài khoản
                  </DropdownMenuItem>
                )}

                {user.status === 'banned' && (
                  <DropdownMenuItem
                    onClick={() => handleSuspend(user.id, user.name)}
                    className="text-yellow-700 focus:text-yellow-700 focus:bg-yellow-50 cursor-pointer"
                  >
                    <Ban className="mr-2 h-4 w-4" />
                    Chuyển sang tạm khóa
                  </DropdownMenuItem>
                )}

                <DropdownMenuSeparator />
                <DropdownMenuLabel>Thay đổi vai trò</DropdownMenuLabel>

                {(['customer', 'owner', 'admin'] as const)
                  .filter((r) => r !== user.role)
                  .map((role) => (
                    <DropdownMenuItem
                      key={role}
                      onClick={() => handleRoleChange(user.id, role)}
                      className="cursor-pointer"
                    >
                      <UserCog className="mr-2 h-4 w-4" />
                      {role === 'customer' ? 'Khách hàng' : role === 'owner' ? 'Chủ cửa hàng' : 'Quản trị viên'}
                    </DropdownMenuItem>
                  ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        );
      },
    },
  ];

  // ─── Render: Loading ─────────────────────────────────────────────────────

  if (loading && users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        <p className="text-gray-500 text-sm">Đang tải danh sách người dùng...</p>
      </div>
    );
  }

  // ─── Render: Error ───────────────────────────────────────────────────────

  if (error && users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <ShieldAlert className="h-12 w-12 text-red-400" />
        <div className="text-center">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Không thể tải dữ liệu</h2>
          <p className="text-gray-500 text-sm max-w-md">{error}</p>
        </div>
        <Button onClick={loadUsers} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Thử lại
        </Button>
      </div>
    );
  }

  // ─── Render: Main ────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h1>
          <p className="text-gray-500 mt-1">Quản lý tài khoản và phân quyền người dùng</p>
        </div>
        <Button onClick={loadUsers} variant="outline" size="sm" className="gap-2" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Làm mới
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tổng số</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <Users className="w-8 h-8 text-gray-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Hoạt động</p>
              <p className="text-2xl font-bold text-green-600">{stats.active}</p>
            </div>
            <ShieldCheck className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tạm khóa</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.suspended}</p>
            </div>
            <Ban className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Đã khóa</p>
              <p className="text-2xl font-bold text-red-600">{stats.banned}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Role Filter Tabs + Search */}
      <div className="bg-white rounded-xl shadow-sm border p-4 space-y-4">
        {/* Role Tabs */}
        <div className="flex flex-wrap gap-2">
          {roleTabs.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setRoleFilter(tab.value)}
              className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                roleFilter === tab.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.label}
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  roleFilter === tab.value ? 'bg-blue-500 text-blue-100' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tên, email, số điện thoại..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>
      </div>

      {/* Error banner (when data exists but refetch failed) */}
      {error && users.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center justify-between">
          <p className="text-sm text-red-700">{error}</p>
          <Button onClick={loadUsers} variant="outline" size="sm" className="gap-1 text-red-700 border-red-300 hover:bg-red-100">
            <RefreshCw className="h-3.5 w-3.5" />
            Thử lại
          </Button>
        </div>
      )}

      {/* Data Table */}
      <div className="bg-white rounded-xl shadow-sm border">
        <DataTable
          columns={columns}
          data={filteredUsers}
          searchKey="name"
          searchable={false}
        />
      </div>

      {/* ─── Confirmation Dialog (Suspend / Role Change) ─────────────────── */}
      <Dialog
        open={confirmDialog.open}
        onOpenChange={(open) => {
          if (!open) setConfirmDialog((prev) => ({ ...prev, open: false }));
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{confirmDialog.title}</DialogTitle>
            <DialogDescription>{confirmDialog.description}</DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setConfirmDialog((prev) => ({ ...prev, open: false }))}
            >
              Hủy
            </Button>
            <Button
              variant={confirmDialog.variant === 'destructive' ? 'destructive' : 'default'}
              onClick={confirmDialog.onConfirm}
            >
              {confirmDialog.confirmLabel}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ─── Ban Reason Dialog ────────────────────────────────────────────── */}
      <Dialog
        open={banDialog.open}
        onOpenChange={(open) => {
          if (!open) setBanDialog({ open: false, userId: '', reason: '' });
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Khóa tài khoản</DialogTitle>
            <DialogDescription>
              Vui lòng nhập lý do khóa tài khoản. Người dùng sẽ bị vô hiệu hóa hoàn toàn.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <label htmlFor="ban-reason" className="text-sm font-medium text-gray-700 mb-1.5 block">
              Lý do khóa
            </label>
            <textarea
              id="ban-reason"
              value={banDialog.reason}
              onChange={(e) => setBanDialog((prev) => ({ ...prev, reason: e.target.value }))}
              placeholder="Nhập lý do khóa tài khoản..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm resize-none"
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setBanDialog({ open: false, userId: '', reason: '' })}
            >
              Hủy
            </Button>
            <Button variant="destructive" onClick={confirmBan}>
              <XCircle className="mr-2 h-4 w-4" />
              Khóa tài khoản
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
