import { useState } from 'react';
import { Check, X, Eye } from 'lucide-react';

interface Match {
  id: string;
  seed_store_name: string;
  registered_store_name: string;
  similarity: number;
  status: string;
}

export default function MatchQueuePage() {
  const [matches, setMatches] = useState<Match[]>([
    { id: '1', seed_store_name: 'Nha thuoc An Khang - Nguyen Trai', registered_store_name: 'Nha thuoc An Khang Q1', similarity: 0.95, status: 'pending' },
    { id: '2', seed_store_name: 'Tiem tap hoa Minh Anh', registered_store_name: 'Minh Anh Store', similarity: 0.88, status: 'pending' },
  ]);

  const handleApprove = (id: string) => {
    setMatches(prev => prev.map(m => m.id === id ? { ...m, status: 'approved' } : m));
  };

  const handleReject = (id: string) => {
    setMatches(prev => prev.filter(m => m.id !== id));
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Match Queue</h1>

        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Seed Store</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Registered Store</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Tuong dong</th>
                <th className="px-4 py-3 text-center text-sm font-medium">Trang thai</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Hanh dong</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {matches.map((match) => (
                <tr key={match.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{match.seed_store_name}</td>
                  <td className="px-4 py-3">{match.registered_store_name}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-medium ${match.similarity > 0.9 ? 'text-green-600' : 'text-yellow-600'}`}>
                      {(match.similarity * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded-full ${match.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {match.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="p-2 hover:bg-gray-200 rounded-lg mr-1"><Eye className="w-4 h-4" /></button>
                    <button onClick={() => handleApprove(match.id)} className="p-2 hover:bg-green-100 text-green-600 rounded-lg mr-1"><Check className="w-4 h-4" /></button>
                    <button onClick={() => handleReject(match.id)} className="p-2 hover:bg-red-100 text-red-600 rounded-lg"><X className="w-4 h-4" /></button>
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
