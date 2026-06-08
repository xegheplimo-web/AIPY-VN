import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface AnalyticsData {
  name: string;
  value: number;
  [key: string]: any;
}

interface AnalyticsChartProps {
  data: AnalyticsData[];
  type: 'line' | 'bar' | 'pie';
  title: string;
  dataKey?: string;
  xAxisKey?: string;
  color?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({
  data,
  type,
  title,
  dataKey = 'value',
  xAxisKey = 'name',
  color = '#0088FE',
}) => {
  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} />
          </LineChart>
        );
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xAxisKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={dataKey} fill={color} />
          </BarChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name}: ${entry.value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={dataKey}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon }) => {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-sm mt-2 ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'}`}>
              {isPositive ? '+' : ''}{change}% so với tháng trước
            </p>
          )}
        </div>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
    </div>
  );
};

interface AnalyticsDashboardProps {
  stats: Array<{
    title: string;
    value: string | number;
    change?: number;
    icon?: React.ReactNode;
  }>;
  charts: Array<{
    data: AnalyticsData[];
    type: 'line' | 'bar' | 'pie';
    title: string;
    dataKey?: string;
    xAxisKey?: string;
    color?: string;
  }>;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ stats, charts }) => {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {charts.map((chart, index) => (
          <AnalyticsChart key={index} {...chart} />
        ))}
      </div>
    </div>
  );
};
