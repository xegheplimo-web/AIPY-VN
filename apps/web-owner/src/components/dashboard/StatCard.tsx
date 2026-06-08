import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  trend: string;
}

export default function StatCard({ icon: Icon, label, value, trend }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border">
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-5 h-5 text-blue-600" />
        <span className="text-xs text-green-600 font-medium">{trend}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  );
}
