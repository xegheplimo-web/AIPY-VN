import { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit2, 
  Trash2, 
  Search, 
  FolderTree,
  ChevronRight,
  ChevronDown,
  Folder,
  FileText
} from 'lucide-react';

interface Category {
  id: string;
  name: string;
  slug: string;
  parentId: string | null;
  level: number;
  productCount: number;
  isActive: boolean;
  children?: Category[];
}

export default function CategoryManagerPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [form, setForm] = useState({ name: '', parentId: '' });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      // Mock data - hierarchical structure
      const mockCategories: Category[] = [
        {
          id: '1',
          name: 'Dược phẩm',
          slug: 'duoc-pham',
          parentId: null,
          level: 0,
          productCount: 1500,
          isActive: true,
          children: [
            {
              id: '1-1',
              name: 'Thuốc giảm đau',
              slug: 'thuoc-giam-dau',
              parentId: '1',
              level: 1,
              productCount: 350,
              isActive: true,
              children: [
                { id: '1-1-1', name: 'Paracetamol', slug: 'paracetamol', parentId: '1-1', level: 2, productCount: 120, isActive: true },
                { id: '1-1-2', name: 'Ibuprofen', slug: 'ibuprofen', parentId: '1-1', level: 2, productCount: 85, isActive: true },
                { id: '1-1-3', name: 'Aspirin', slug: 'aspirin', parentId: '1-1', level: 2, productCount: 145, isActive: true },
              ],
            },
            {
              id: '1-2',
              name: 'Vitamin',
              slug: 'vitamin',
              parentId: '1',
              level: 1,
              productCount: 420,
              isActive: true,
              children: [
                { id: '1-2-1', name: 'Vitamin C', slug: 'vitamin-c', parentId: '1-2', level: 2, productCount: 180, isActive: true },
                { id: '1-2-2', name: 'Vitamin D', slug: 'vitamin-d', parentId: '1-2', level: 2, productCount: 95, isActive: true },
                { id: '1-2-3', name: 'Multivitamin', slug: 'multivitamin', parentId: '1-2', level: 2, productCount: 145, isActive: true },
              ],
            },
            {
              id: '1-3',
              name: 'Thuốc kháng sinh',
              slug: 'thuoc-khang-sinh',
              parentId: '1',
              level: 1,
              productCount: 280,
              isActive: true,
            },
          ],
        },
        {
          id: '2',
          name: 'Thiết bị y tế',
          slug: 'thiet-bi-y-te',
          parentId: null,
          level: 0,
          productCount: 890,
          isActive: true,
          children: [
            {
              id: '2-1',
              name: 'Khẩu trang',
              slug: 'khau-trang',
              parentId: '2',
              level: 1,
              productCount: 350,
              isActive: true,
            },
            {
              id: '2-2',
              name: 'Nhiệt kế',
              slug: 'nhiet-ke',
              parentId: '2',
              level: 1,
              productCount: 120,
              isActive: true,
            },
            {
              id: '2-3',
              name: 'Băng y tế',
              slug: 'bang-y-te',
              parentId: '2',
              level: 1,
              productCount: 420,
              isActive: true,
            },
          ],
        },
        {
          id: '3',
          name: 'Chăm sóc cá nhân',
          slug: 'cham-soc-ca-nhan',
          parentId: null,
          level: 0,
          productCount: 650,
          isActive: true,
          children: [
            {
              id: '3-1',
              name: 'Sữa rửa mặt',
              slug: 'sua-rua-mat',
              parentId: '3',
              level: 1,
              productCount: 280,
              isActive: true,
            },
            {
              id: '3-2',
              name: 'Kem dưỡng ẩm',
              slug: 'kem-duong-am',
              parentId: '3',
              level: 1,
              productCount: 370,
              isActive: true,
            },
          ],
        },
      ];
      setCategories(mockCategories);
    } catch (err) {
      console.error('Failed to load categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleAdd = async () => {
    try {
      // Mock API call
      setShowAddModal(false);
      setForm({ name: '', parentId: '' });
      loadCategories();
    } catch (err) {
      alert('Thêm danh mục thất bại');
    }
  };

  const handleEdit = async () => {
    try {
      // Mock API call
      setEditingCategory(null);
      setForm({ name: '', parentId: '' });
      loadCategories();
    } catch (err) {
      alert('Cập nhật danh mục thất bại');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa danh mục này?')) return;
    try {
      // Mock API call
      loadCategories();
    } catch (err) {
      alert('Xóa danh mục thất bại');
    }
  };

  const renderCategory = (category: Category) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expanded.has(category.id);
    const paddingLeft = category.level * 24;

    return (
      <div key={category.id}>
        <div
          className="flex items-center gap-2 py-3 px-4 hover:bg-gray-50 border-b cursor-pointer"
          style={{ paddingLeft: `${paddingLeft + 16}px` }}
        >
          {hasChildren ? (
            <button
              onClick={() => toggleExpand(category.id)}
              className="p-1 hover:bg-gray-200 rounded"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          ) : (
            <div className="w-6" />
          )}
          {category.level === 0 ? (
            <Folder className="w-5 h-5 text-yellow-500" />
          ) : (
            <FileText className="w-5 h-5 text-blue-500" />
          )}
          <div className="flex-1">
            <span className="font-medium text-gray-900">{category.name}</span>
            <span className="text-sm text-gray-500 ml-2">({category.productCount} sản phẩm)</span>
          </div>
          {!category.isActive && (
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">Inactive</span>
          )}
          <div className="flex gap-1">
            <button
              onClick={() => {
                setEditingCategory(category);
                setForm({ name: category.name, parentId: category.parentId || '' });
              }}
              className="p-2 hover:bg-gray-200 rounded"
            >
              <Edit2 className="w-4 h-4 text-gray-600" />
            </button>
            <button
              onClick={() => handleDelete(category.id)}
              className="p-2 hover:bg-red-100 rounded"
            >
              <Trash2 className="w-4 h-4 text-red-600" />
            </button>
          </div>
        </div>
        {hasChildren && isExpanded && (
          <div>
            {category.children!.map((child) => renderCategory(child))}
          </div>
        )}
      </div>
    );
  };

  const flattenCategories = (cats: Category[]): Category[] => {
    const result: Category[] = [];
    const flatten = (category: Category) => {
      result.push(category);
      if (category.children) {
        category.children.forEach(flatten);
      }
    };
    cats.forEach(flatten);
    return result;
  };

  const filteredCategories = searchQuery
    ? flattenCategories(categories).filter((c) =>
        c.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : categories;

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
          <h1 className="text-2xl font-bold text-gray-900">Quản lý danh mục</h1>
          <p className="text-gray-500 mt-1">Quản lý taxonomy sản phẩm</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Thêm danh mục
        </button>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm danh mục..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Category Tree */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center gap-2">
            <FolderTree className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-900">Cây danh mục</span>
          </div>
        </div>
        {filteredCategories.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            Không tìm thấy kết quả
          </div>
        ) : (
          <div>
            {searchQuery
              ? filteredCategories.map((cat) => (
                  <div
                    key={cat.id}
                    className="flex items-center gap-2 py-3 px-4 hover:bg-gray-50 border-b"
                    style={{ paddingLeft: `${cat.level * 24 + 16}px` }}
                  >
                    {cat.level === 0 ? (
                      <Folder className="w-5 h-5 text-yellow-500" />
                    ) : (
                      <FileText className="w-5 h-5 text-blue-500" />
                    )}
                    <span className="font-medium text-gray-900">{cat.name}</span>
                    <span className="text-sm text-gray-500 ml-2">({cat.productCount} sản phẩm)</span>
                  </div>
                ))
              : categories.map((cat) => renderCategory(cat))}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">Thêm danh mục mới</h2>
            <div className="space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Tên danh mục"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <select
                value={form.parentId}
                onChange={(e) => setForm({ ...form, parentId: e.target.value })}
                className="w-full px-4 py-3 border rounded-lg"
              >
                <option value="">Danh mục gốc</option>
                {flattenCategories(categories).map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {'  '.repeat(cat.level)}{cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-3 border rounded-lg"
              >
                Hủy
              </button>
              <button onClick={handleAdd} className="flex-1 py-3 bg-blue-600 text-white rounded-lg">
                Lưu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">Chỉnh sửa danh mục</h2>
            <div className="space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Tên danh mục"
                className="w-full px-4 py-3 border rounded-lg"
              />
              <select
                value={form.parentId}
                onChange={(e) => setForm({ ...form, parentId: e.target.value })}
                className="w-full px-4 py-3 border rounded-lg"
              >
                <option value="">Danh mục gốc</option>
                {flattenCategories(categories)
                  .filter((c) => c.id !== editingCategory.id)
                  .map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {'  '.repeat(cat.level)}{cat.name}
                    </option>
                  ))}
              </select>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  setEditingCategory(null);
                  setForm({ name: '', parentId: '' });
                }}
                className="flex-1 py-3 border rounded-lg"
              >
                Hủy
              </button>
              <button onClick={handleEdit} className="flex-1 py-3 bg-blue-600 text-white rounded-lg">
                Cập nhật
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
