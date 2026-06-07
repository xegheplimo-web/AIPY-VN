import { useState, useEffect } from 'react';
import { Search, Check, X, Eye } from 'lucide-react';
import api from '../services/api';

interface Store {
  id: string;
  name: string;
  address: string;
  industry: string;
  status: string;
  location_verified: boolean;
}

export default function StoresManagementPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadStores();
  }, []);

  const loadStores = async () => {
    try {
      const res = await api.get('/stores/?limit=100');
      setStores(res.data.stores || []);
    } catch (err) {
      console.error('Failed to load stores:', err);
    }
  };

  const filtered = stores.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.address.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Quan ly cua hang</h1>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tim cua hang..."
            className="w-full pl-10 pr-4 py-3 border rounded-xl"
          />
        </div>

        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Ten</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Dia chi</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Nganh</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Trang thai</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Hanh dong</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((store) => (
                <tr key={store.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{store.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{store.address}</td>
                  <td className="px-4 py-3 text-sm">{store.industry}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded-full ${store.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {store.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="p-2 hover:bg-gray-200 rounded-lg mr-1"><Eye className="w-4 h-4" /></button>
                    <button className="p-2 hover:bg-green-100 text-green-600 rounded-lg mr-1"><Check className="w-4 h-4" /></button>
                    <button className="p-2 hover:bg-red-100 text-red-600 rounded-lg"><X className="w-4 h-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
