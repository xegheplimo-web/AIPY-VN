import { type ColumnDef } from '@tanstack/react-table';
import { Edit2, Plus, Trash2, Upload } from 'lucide-react';
import { useEffect, useState } from 'react';
import { DataTable } from '../components/ui/DataTable';
import api from '../services/api';

interface Product {
  id: string;
  name: string;
  price?: number;
  stock: number;
  unit: string;
  status: string;
}

export default function ProductManagementPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({ name: '', price: '', stock: '0', unit: 'cai', barcode: '', brand: '', shelf_location: '' });

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const res = await api.get('/owner/products?store_id=store-1&limit=100');
      setProducts(res.data.products || []);
    } catch (err) {
      console.error('Failed to load products:', err);
    }
  };

  const handleAdd = async () => {
    try {
      await api.post('/owner/products?store_id=store-1', {
        name: form.name,
        price: parseFloat(form.price),
        stock: parseInt(form.stock),
        unit: form.unit,
        barcode: form.barcode,
        brand: form.brand,
        shelf_location: form.shelf_location,
      });
      setShowAddModal(false);
      setForm({ name: '', price: '', stock: '0', unit: 'cai', barcode: '', brand: '', shelf_location: '' });
      loadProducts();
    } catch (err) {
      alert('Them san pham that bai!');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Ban chac chan muon xoa?')) return;
    try {
      await api.delete(`/owner/products/${id}?store_id=store-1`);
      loadProducts();
    } catch (err) {
      alert('Xoa that bai!');
    }
  };

  const columns: ColumnDef<Product>[] = [
    {
      accessorKey: 'name',
      header: 'Ten san pham',
      cell: ({ row }) => <div className="font-medium">{row.getValue('name')}</div>,
    },
    {
      accessorKey: 'price',
      header: 'Gia',
      cell: ({ row }) => (
        <div className="text-right">
          {row.getValue('price') ? `${Number(row.getValue('price')).toLocaleString('vi-VN')}đ` : '-'}
        </div>
      ),
    },
    {
      accessorKey: 'stock',
      header: 'Ton kho',
      cell: ({ row }) => (
        <div className={`text-right ${row.getValue('stock') < 10 ? 'text-red-600 font-medium' : ''}`}>
          {row.getValue('stock')}
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Trang thai',
      cell: ({ row }) => (
        <div className="text-center">
          <span className={`text-xs px-2 py-1 rounded-full ${
            row.getValue('status') === 'active' 
              ? 'bg-green-100 text-green-700' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {row.getValue('status')}
          </span>
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'Hanh dong',
      cell: ({ row }) => (
        <div className="text-right">
          <button className="p-2 hover:bg-gray-200 rounded-lg mr-1">
            <Edit2 className="w-4 h-4" />
          </button>
          <button 
            onClick={() => handleDelete(row.original.id)} 
            className="p-2 hover:bg-red-100 text-red-600 rounded-lg"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Quan ly san pham</h1>
          <div className="flex gap-2">
            <button className="px-4 py-2 border rounded-lg flex items-center gap-2 hover:bg-gray-50">
              <Upload className="w-4 h-4" /> Import CSV
            </button>
            <button onClick={() => setShowAddModal(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg flex items-center gap-2 hover:bg-blue-700">
              <Plus className="w-4 h-4" /> Them san pham
            </button>
          </div>
        </div>

        <DataTable columns={columns} data={products} searchKey="name" />

        {/* Add Product Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h2 className="text-lg font-bold mb-4">Them san pham moi</h2>
              <div className="space-y-3">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ten san pham" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} placeholder="Gia (VND)" type="number" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} placeholder="Ton kho" type="number" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} placeholder="Don vi" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} placeholder="Ma vach" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} placeholder="Thuong hieu" className="w-full px-4 py-3 border rounded-lg" />
                <input value={form.shelf_location} onChange={(e) => setForm({ ...form, shelf_location: e.target.value })} placeholder="Vi tri ke" className="w-full px-4 py-3 border rounded-lg" />
              </div>
              <div className="flex gap-3 mt-4">
                <button onClick={() => setShowAddModal(false)} className="flex-1 py-3 border rounded-lg">Huy</button>
                <button onClick={handleAdd} className="flex-1 py-3 bg-blue-600 text-white rounded-lg">Luu</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
