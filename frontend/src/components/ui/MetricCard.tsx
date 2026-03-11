import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: { value: number; isPositive: boolean };
}

export default function MetricCard({ title, value, subtitle, icon: Icon, color = '#3B82F6', trend }: MetricCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
          {trend && (
            <p className={`text-xs font-medium mt-1 ${trend.isPositive ? 'text-green-600' : 'text-red-500'}`}>
              {trend.isPositive ? '+' : ''}{trend.value}% vs mes anterior
            </p>
          )}
        </div>
        <div className="p-2.5 rounded-lg" style={{ backgroundColor: `${color}15` }}>
          <Icon size={22} style={{ color }} />
        </div>
      </div>
    </div>
  );
}
