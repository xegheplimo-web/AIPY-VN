import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plus,
  Pencil,
  Trash2,
  Search,
  FolderTree,
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  Tag,
  RefreshCw,
  AlertCircle,
  Loader2,
  Package,
  Layers,
  FolderPlus,
  X,
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../services/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface CategoryRaw {
  id: string;
  name: string;
  slug?: string;
  icon_url?: string;
  parent_id?: string | null;
  product_count?: number;
  is_active?: boolean;
  level?: number;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  iconUrl: string;
  parentId: string | null;
  level: number;
  productCount: number;
  isActive: boolean;
  children: Category[];
}

interface CategoryForm {
  name: string;
  slug: string;
  iconUrl: string;
  parentId: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

function buildTree(items: CategoryRaw[]): Category[] {
  const map = new Map<string, Category>();
  const roots: Category[] = [];

  // First pass – create all nodes
  for (const item of items) {
    map.set(item.id, {
      id: item.id,
      name: item.name || '',
      slug: item.slug || generateSlug(item.name || ''),
      iconUrl: item.icon_url || '',
      parentId: item.parent_id || null,
      level: 0,
      productCount: typeof item.product_count === 'number' ? item.product_count : 0,
      isActive: item.is_active !== false,
      children: [],
    });
  }

  // Second pass – attach children and compute level
  for (const item of items) {
    const node = map.get(item.id)!;
    if (item.parent_id && map.has(item.parent_id)) {
      map.get(item.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  // Compute levels
  const setLevel = (nodes: Category[], depth: number) => {
    for (const n of nodes) {
      n.level = depth;
      setLevel(n.children, depth + 1);
    }
  };
  setLevel(roots, 0);

  return roots;
}

function flattenTree(nodes: Category[]): Category[] {
  const result: Category[] = [];
  const walk = (list: Category[]) => {
    for (const n of list) {
      result.push(n);
      walk(n.children);
    }
  };
  walk(nodes);
  return result;
}

const EMPTY_FORM: CategoryForm = {
  name: '',
  slug: '',
  iconUrl: '',
  parentId: '',
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function CategoryManagerPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [flatList, setFlatList] = useState<Category[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<CategoryForm>(EMPTY_FORM);
  const [slugManual, setSlugManual] = useState(false);

  // Delete confirmation state
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const [deleting, setDeleting] = useState(false);

  // ─── Data loading ────────────────────────────────────────────────────────

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getCategories({ limit: 500, page: 1 });
      // Safely extract array from various possible response shapes
      const raw: CategoryRaw[] = Array.isArray(response)
        ? response
        : response?.categories
          ? response.categories
          : response?.data
            ? response.data
            : [];

      const tree = buildTree(raw);
      setCategories(tree);
      setFlatList(flattenTree(tree));

      // Auto-expand root categories on first load
      if (expanded.size === 0) {
        setExpanded(new Set(tree.map((c) => c.id)));
      }
    } catch (err: any) {
      const msg =
        err?.message || 'Không thể tải danh mục. Vui lòng thử lại.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [expanded]);

  useEffect(() => {
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ─── Tree interaction ────────────────────────────────────────────────────

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandAll = () => setExpanded(new Set(flatList.map((c) => c.id)));
  const collapseAll = () => setExpanded(new Set());

  // ─── Search / filter ─────────────────────────────────────────────────────

  const filteredTree = useMemo(() => {
    if (!searchQuery.trim()) return categories;

    const q = searchQuery.toLowerCase();
    const matchingIds = new Set(
      flatList
        .filter((c) => c.name.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q))
        .map((c) => c.id),
    );

    // Also include ancestors so the tree path is visible
    const visible = new Set<string>();
    const addAncestors = (id: string) => {
      visible.add(id);
      const node = flatList.find((c) => c.id === id);
      if (node?.parentId) addAncestors(node.parentId);
    };
    matchingIds.forEach(addAncestors);

    const prune = (nodes: Category[]): Category[] =>
      nodes
        .filter((n) => visible.has(n.id))
        .map((n) => ({ ...n, children: prune(n.children) }));

    return prune(categories);
  }, [categories, flatList, searchQuery]);

  // ─── Stats ───────────────────────────────────────────────────────────────

  const stats = useMemo(() => {
    const total = flatList.length;
    const topLevel = categories.length;
    const subCategories = total - topLevel;
    return { total, topLevel, subCategories };
  }, [flatList, categories]);

  // ─── Modal helpers ───────────────────────────────────────────────────────

  const openAddModal = () => {
    setIsEditing(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
    setSlugManual(false);
    setModalOpen(true);
  };

  const openEditModal = (cat: Category) => {
    setIsEditing(true);
    setEditingId(cat.id);
    setForm({
      name: cat.name,
      slug: cat.slug,
      iconUrl: cat.iconUrl,
      parentId: cat.parentId || '',
    });
    setSlugManual(true); // Don't auto-overwrite when editing
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setForm(EMPTY_FORM);
    setEditingId(null);
    setSlugManual(false);
  };

  const handleNameChange = (name: string) => {
    setForm((prev) => ({
      ...prev,
      name,
      slug: slugManual ? prev.slug : generateSlug(name),
    }));
  };

  const handleSlugChange = (slug: string) => {
    setSlugManual(true);
    setForm((prev) => ({ ...prev, slug }));
  };

  // ─── Submit (create / update) ───────────────────────────────────────────

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error('Tên danh mục không được để trống');
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        name: form.name.trim(),
        slug: form.slug.trim() || generateSlug(form.name.trim()),
        icon_url: form.iconUrl.trim() || null,
        parent_id: form.parentId || null,
      };

      if (isEditing && editingId) {
        await api.updateCategory(editingId, payload);
        toast.success('Cập nhật danh mục thành công');
      } else {
        await api.createCategory(payload);
        toast.success('Thêm danh mục thành công');
      }

      closeModal();
      await loadCategories();
    } catch (err: any) {
      toast.error(err?.message || (isEditing ? 'Cập nhật danh mục thất bại' : 'Thêm danh mục thất bại'));
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Delete ──────────────────────────────────────────────────────────────

  const openDeleteConfirm = (cat: Category) => {
    setDeleteTarget(cat);
  };

  const closeDeleteConfirm = () => {
    setDeleteTarget(null);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteCategory(deleteTarget.id);
      toast.success('Xóa danh mục thành công');
      closeDeleteConfirm();
      await loadCategories();
    } catch (err: any) {
      toast.error(err?.message || 'Xóa danh mục thất bại');
    } finally {
      setDeleting(false);
    }
  };

  // ─── Render: tree row ────────────────────────────────────────────────────

  const renderRow = (cat: Category): React.ReactNode => {
    const hasChildren = cat.children.length > 0;
    const isExpanded = expanded.has(cat.id);
    const indent = cat.level * 28;

    const parentName = cat.parentId
      ? flatList.find((c) => c.id === cat.parentId)?.name ?? '—'
      : '—';

    return (
      <div key={cat.id}>
        {/* Main row */}
        <div
          className="flex items-center gap-2 py-2.5 px-3 hover:bg-gray-50 border-b border-gray-100 transition-colors group"
          style={{ paddingLeft: `${indent + 12}px` }}
        >
          {/* Expand toggle */}
          <button
            onClick={() => hasChildren && toggleExpand(cat.id)}
            className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded transition ${
              hasChildren
                ? 'hover:bg-gray-200 cursor-pointer'
                : 'cursor-default'
            }`}
            aria-label={hasChildren ? (isExpanded ? 'Thu gọn' : 'Mở rộng') : undefined}
          >
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown size={16} className="text-gray-500" />
              ) : (
                <ChevronRight size={16} className="text-gray-500" />
              )
            ) : (
              <span className="w-4" />
            )}
          </button>

          {/* Icon */}
          <div className="flex-shrink-0">
            {cat.iconUrl ? (
              <img
                src={cat.iconUrl}
                alt=""
                className="w-5 h-5 object-contain rounded"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}
            <span
              className={cat.iconUrl ? 'hidden' : ''}
            >
              {hasChildren ? (
                isExpanded ? (
                  <FolderOpen size={18} className="text-amber-500" />
                ) : (
                  <Folder size={18} className="text-amber-500" />
                )
              ) : (
                <Tag size={16} className="text-gray-400" />
              )}
            </span>
          </div>

          {/* Name */}
          <div className="flex-1 min-w-0">
            <span className="font-medium text-gray-900 truncate">{cat.name}</span>
          </div>

          {/* Slug */}
          <div className="hidden md:block w-36 truncate text-sm text-gray-500">
            {cat.slug}
          </div>

          {/* Parent */}
          <div className="hidden lg:block w-32 truncate text-sm text-gray-500">
            {parentName}
          </div>

          {/* Product count */}
          <div className="w-28 text-right">
            <span className="inline-flex items-center gap-1 text-sm text-gray-600">
              <Package size={13} className="text-gray-400" />
              {cat.productCount} SP
            </span>
          </div>

          {/* Status */}
          <div className="w-20 text-center">
            {cat.isActive ? (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700">
                Hoạt động
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                Ẩn
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="w-20 flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => openEditModal(cat)}
              className="p-1.5 hover:bg-blue-50 rounded transition"
              title="Chỉnh sửa"
            >
              <Pencil size={15} className="text-blue-600" />
            </button>
            <button
              onClick={() => openDeleteConfirm(cat)}
              className="p-1.5 hover:bg-red-50 rounded transition"
              title="Xóa"
            >
              <Trash2 size={15} className="text-red-500" />
            </button>
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div>{cat.children.map((child) => renderRow(child))}</div>
        )}
      </div>
    );
  };

  // ─── Render: flat search results ─────────────────────────────────────────

  const renderSearchRow = (cat: Category) => {
    const parentName = cat.parentId
      ? flatList.find((c) => c.id === cat.parentId)?.name ?? '—'
      : '—';

    return (
      <div
        key={cat.id}
        className="flex items-center gap-2 py-2.5 px-3 hover:bg-gray-50 border-b border-gray-100 transition-colors group"
        style={{ paddingLeft: `${cat.level * 28 + 12}px` }}
      >
        <span className="w-6" />
        <Tag size={16} className="text-gray-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <span className="font-medium text-gray-900 truncate">{cat.name}</span>
        </div>
        <div className="hidden md:block w-36 truncate text-sm text-gray-500">{cat.slug}</div>
        <div className="hidden lg:block w-32 truncate text-sm text-gray-500">{parentName}</div>
        <div className="w-28 text-right text-sm text-gray-600">
          <span className="inline-flex items-center gap-1">
            <Package size={13} className="text-gray-400" />
            {cat.productCount} SP
          </span>
        </div>
        <div className="w-20 flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => openEditModal(cat)}
            className="p-1.5 hover:bg-blue-50 rounded transition"
            title="Chỉnh sửa"
          >
            <Pencil size={15} className="text-blue-600" />
          </button>
          <button
            onClick={() => openDeleteConfirm(cat)}
            className="p-1.5 hover:bg-red-50 rounded transition"
            title="Xóa"
          >
            <Trash2 size={15} className="text-red-500" />
          </button>
        </div>
      </div>
    );
  };

  // ─── Render: parent select options (recursive) ──────────────────────────

  const renderParentOption = (cat: Category, depth = 0): React.ReactNode[] => {
    const prefix = '\u00A0\u00A0'.repeat(depth) + (depth > 0 ? '└ ' : '');
    const options: React.ReactNode[] = [
      <option key={cat.id} value={cat.id}>
        {prefix}
        {cat.name}
      </option>,
    ];
    for (const child of cat.children) {
      options.push(...renderParentOption(child, depth + 1));
    }
    return options;
  };

  const parentOptions = useMemo(() => {
    const opts: React.ReactNode[] = [
      <option key="__root__" value="">
        — Danh mục gốc —
      </option>,
    ];
    // When editing, exclude the category itself and its descendants to avoid circular references
    const excludeIds = new Set<string>();
    if (isEditing && editingId) {
      const addDescendants = (id: string) => {
        excludeIds.add(id);
        const node = flatList.find((c) => c.id === id);
        if (node) node.children.forEach((ch) => addDescendants(ch.id));
      };
      addDescendants(editingId);
    }

    const prune = (nodes: Category[]): Category[] =>
      nodes
        .filter((n) => !excludeIds.has(n.id))
        .map((n) => ({ ...n, children: prune(n.children) }));

    for (const cat of prune(categories)) {
      opts.push(...renderParentOption(cat));
    }
    return opts;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categories, flatList, isEditing, editingId]);

  // ─── Loading state ──────────────────────────────────────────────────────

  if (loading && categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
        <p className="text-gray-500 text-sm">Đang tải danh mục…</p>
      </div>
    );
  }

  // ─── Error state ────────────────────────────────────────────────────────

  if (error && categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-4">
        <AlertCircle className="w-12 h-12 text-red-400" />
        <div className="text-center">
          <p className="font-medium text-gray-900 mb-1">Không thể tải danh mục</p>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button
            onClick={loadCategories}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <RefreshCw size={16} />
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  // ─── Main render ────────────────────────────────────────────────────────

  const isSearching = searchQuery.trim().length > 0;
  const searchResults = isSearching
    ? flattenTree(filteredTree)
    : [];

  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý danh mục</h1>
          <p className="text-gray-500 mt-1">Quản lý phân loại sản phẩm theo cấu trúc cây</p>
        </div>
        <button
          onClick={openAddModal}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm"
        >
          <Plus size={18} />
          Thêm danh mục
        </button>
      </div>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Tổng danh mục</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <Layers className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Danh mục gốc</p>
              <p className="text-2xl font-bold text-amber-600">{stats.topLevel}</p>
            </div>
            <Folder className="w-8 h-8 text-amber-400" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Danh mục con</p>
              <p className="text-2xl font-bold text-green-600">{stats.subCategories}</p>
            </div>
            <FolderPlus className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* ── Search & controls ───────────────────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm danh mục theo tên hoặc slug…"
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
          {!isSearching && (
            <div className="flex gap-2">
              <button
                onClick={expandAll}
                className="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 transition"
              >
                Mở tất cả
              </button>
              <button
                onClick={collapseAll}
                className="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 transition"
              >
                Thu gọn
              </button>
            </div>
          )}
          <button
            onClick={loadCategories}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Làm mới
          </button>
        </div>
      </div>

      {/* ── Category tree / search results ──────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        {/* Table header */}
        <div className="flex items-center gap-2 px-3 py-3 border-b bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wide">
          <span className="w-6" />
          <span className="w-5" />
          <span className="flex-1">Tên danh mục</span>
          <span className="hidden md:block w-36">Slug</span>
          <span className="hidden lg:block w-32">Danh mục cha</span>
          <span className="w-28 text-right">Sản phẩm</span>
          <span className="w-20 text-center">Trạng thái</span>
          <span className="w-20 text-right">Thao tác</span>
        </div>

        {/* Tree body */}
        {isSearching ? (
          searchResults.length === 0 ? (
            <div className="p-12 text-center">
              <Search className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Không tìm thấy danh mục phù hợp với "{searchQuery}"</p>
            </div>
          ) : (
            <div>{searchResults.map(renderSearchRow)}</div>
          )
        ) : categories.length === 0 ? (
          <div className="p-12 text-center">
            <FolderTree className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">Chưa có danh mục nào</p>
            <button
              onClick={openAddModal}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Plus size={16} />
              Tạo danh mục đầu tiên
            </button>
          </div>
        ) : (
          <div className="max-h-[60vh] overflow-y-auto">
            {filteredTree.map(renderRow)}
          </div>
        )}
      </div>

      {/* ── Add / Edit Modal ────────────────────────────────────────────── */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-lg shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b">
              <h2 className="text-lg font-bold text-gray-900">
                {isEditing ? 'Chỉnh sửa danh mục' : 'Thêm danh mục mới'}
              </h2>
              <button
                onClick={closeModal}
                className="p-1.5 hover:bg-gray-100 rounded-lg transition"
              >
                <X size={18} className="text-gray-500" />
              </button>
            </div>

            {/* Form */}
            <div className="p-5 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tên danh mục <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="Nhập tên danh mục…"
                  className="w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              {/* Slug */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slug
                </label>
                <input
                  type="text"
                  value={form.slug}
                  onChange={(e) => handleSlugChange(e.target.value)}
                  placeholder="tu-dong-tao-tu-ten"
                  className="w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Để trống sẽ tự tạo từ tên danh mục
                </p>
              </div>

              {/* Icon URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL biểu tượng
                </label>
                <input
                  type="text"
                  value={form.iconUrl}
                  onChange={(e) => setForm((prev) => ({ ...prev, iconUrl: e.target.value }))}
                  placeholder="https://example.com/icon.png"
                  className="w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {form.iconUrl && (
                  <div className="mt-2 flex items-center gap-2">
                    <img
                      src={form.iconUrl}
                      alt="Preview"
                      className="w-8 h-8 object-contain border rounded"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <span className="text-xs text-gray-400">Xem trước</span>
                  </div>
                )}
              </div>

              {/* Parent */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Danh mục cha
                </label>
                <select
                  value={form.parentId}
                  onChange={(e) => setForm((prev) => ({ ...prev, parentId: e.target.value }))}
                  className="w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {parentOptions}
                </select>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 p-5 border-t bg-gray-50 rounded-b-xl">
              <button
                onClick={closeModal}
                className="px-4 py-2.5 text-sm font-medium border rounded-lg hover:bg-gray-100 transition"
                disabled={submitting}
              >
                Hủy
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || !form.name.trim()}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting && <Loader2 size={16} className="animate-spin" />}
                {isEditing ? 'Cập nhật' : 'Tạo danh mục'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete confirmation modal ───────────────────────────────────── */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl">
            <div className="p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <Trash2 size={20} className="text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Xóa danh mục</h3>
                  <p className="text-sm text-gray-500">
                    Hành động này không thể hoàn tác
                  </p>
                </div>
              </div>

              <p className="text-gray-700 mb-3">
                Bạn có chắc chắn muốn xóa danh mục <strong>"{deleteTarget.name}"</strong>?
              </p>

              {/* Warnings */}
              {(deleteTarget.children.length > 0 || deleteTarget.productCount > 0) && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle size={18} className="text-amber-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-amber-800 space-y-1">
                      {deleteTarget.children.length > 0 && (
                        <p>
                          ⚠️ Danh mục này có <strong>{deleteTarget.children.length}</strong> danh mục con. Tất cả sẽ bị ảnh hưởng.
                        </p>
                      )}
                      {deleteTarget.productCount > 0 && (
                        <p>
                          ⚠️ Danh mục này đang chứa <strong>{deleteTarget.productCount}</strong> sản phẩm.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-3 p-5 border-t bg-gray-50 rounded-b-xl">
              <button
                onClick={closeDeleteConfirm}
                className="px-4 py-2.5 text-sm font-medium border rounded-lg hover:bg-gray-100 transition"
                disabled={deleting}
              >
                Hủy
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
              >
                {deleting && <Loader2 size={16} className="animate-spin" />}
                Xóa danh mục
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
