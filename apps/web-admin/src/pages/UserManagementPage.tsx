import { useState } from 'react';
import { Search, UserCog, Ban, Eye } from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([
    { id: '1', name: 'Nguyen Van A', email: 'user1@example.com', role: 'customer', status: 'active' },
    { id: '2', name: 'Tran Thi B', email: 'owner1@example.com', role: 'owner', status: 'active' },
    { id: '3', name: 'Le Van C', email: 'admin@example.com', role: 'admin', status: 'active' },
  ]);
  const [search, setSearch] = useState('');

  const filtered = users.filter(u =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const toggleStatus = (id: string) => {
    setUsers(prev => prev.map(u => u.id === id ? { ...u, status: u.status === 'active' ? 'banned' : 'active' } : u));
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Quan ly nguoi dung</h1>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tim nguoi dung..."
            className="w-full pl-10 pr-4 py-3 border rounded-xl"
          />
        </div>

        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Ten</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Email</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Vai tro</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Trang thai</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Hanh dong</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{user.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      user.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                      user.role === 'owner' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded-full ${user.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="p-2 hover:bg-gray-200 rounded-lg mr-1"><Eye className="w-4 h-4" /></button>
                    <button className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg mr-1"><UserCog className="w-4 h-4" /></button>
                    <button onClick={() => toggleStatus(user.id)} className="p-2 hover:bg-red-100 text-red-600 rounded-lg"><Ban className="w-4 h-4" /></button>
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
