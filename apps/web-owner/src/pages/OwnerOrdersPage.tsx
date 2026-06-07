import { type ColumnDef } from '@tanstack/react-table';
import { Check, Truck, X } from 'lucide-react';
import { useState } from 'react';
import { DataTable } from '../components/ui/DataTable';

interface Order {
  id: string;
  order_number: string;
  customer: string;
  total: string;
  status: string;
  date: string;
  items: string[];
}

const STATUS_TABS = ['all', 'pending', 'confirmed', 'preparing', 'ready', 'completed'];
const STATUS_LABELS: Record<string, string> = {
  all: 'Tat ca',
  pending: 'Cho xac nhan',
  confirmed: 'Da xac nhan',
  preparing: 'Dang chuan bi',
  ready: 'San sang',
  completed: 'Hoan thanh',
};

export default function OwnerOrdersPage() {
  const [activeTab, setActiveTab] = useState('all');
  const [orders, setOrders] = useState<Order[]>([
    { id: '1', order_number: 'ORD-2024-00001', customer: 'Nguyen Van A', total: '350,000', status: 'pending', date: '2024-12-01', items: ['Panadol Extra 500mg x2'] },
    { id: '2', order_number: 'ORD-2024-00002', customer: 'Tran Thi B', total: '125,000', status: 'confirmed', date: '2024-12-01', items: ['Vitamin C 1000mg x1'] },
  ]);

  const filtered = activeTab === 'all' ? orders : orders.filter(o => o.status === activeTab);

  const updateStatus = (id: string, newStatus: string) => {
    setOrders(prev => prev.map(o => o.id === id ? { ...o, status: newStatus } : o));
  };

  const columns: ColumnDef<Order>[] = [
    {
      accessorKey: 'order_number',
      header: 'Ma don hang',
      cell: ({ row }) => <div className="font-medium">{row.getValue('order_number')}</div>,
    },
    {
      accessorKey: 'customer',
      header: 'Khach hang',
    },
    {
      accessorKey: 'date',
      header: 'Ngay dat',
    },
    {
      accessorKey: 'items',
      header: 'San pham',
      cell: ({ row }) => (
        <div className="text-sm text-gray-600 max-w-xs truncate">
          {row.getValue('items').join(', ')}
        </div>
      ),
    },
    {
      accessorKey: 'total',
      header: 'Tong tien',
      cell: ({ row }) => (
        <div className="font-bold text-blue-600">{row.getValue('total')}đ</div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Trang thai',
      cell: ({ row }) => (
        <span className={`text-xs px-2 py-1 rounded-full ${
          row.getValue('status') === 'completed' ? 'bg-green-100 text-green-700' :
          row.getValue('status') === 'pending' ? 'bg-yellow-100 text-yellow-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {STATUS_LABELS[row.getValue('status')]}
        </span>
      ),
    },
    {
      id: 'actions',
      header: 'Hanh dong',
      cell: ({ row }) => {
        const status = row.getValue('status');
        return (
          <div className="flex gap-2">
            {status === 'pending' && (
              <>
                <button 
                  onClick={() => updateStatus(row.original.id, 'confirmed')} 
                  className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg flex items-center gap-1"
                >
                  <Check className="w-4 h-4" /> Chap nhan
                </button>
                <button 
                  onClick={() => updateStatus(row.original.id, 'cancelled')} 
                  className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg flex items-center gap-1"
                >
                  <X className="w-4 h-4" /> Tu choi
                </button>
              </>
            )}
            {status === 'confirmed' && (
              <button 
                onClick={() => updateStatus(row.original.id, 'preparing')} 
                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg flex items-center gap-1"
              >
                <Truck className="w-4 h-4" /> Bat dau chuan bi
              </button>
            )}
            {status === 'preparing' && (
              <button 
                onClick={() => updateStatus(row.original.id, 'ready')} 
                className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg"
              >
                San sang giao
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Quan ly don hang</h1>

        <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                activeTab === tab ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
              }`}
            >
              {STATUS_LABELS[tab]}
            </button>
          ))}
        </div>

        <DataTable columns={columns} data={filtered} searchKey="order_number" />
      </div>
    </div>
  );
}
