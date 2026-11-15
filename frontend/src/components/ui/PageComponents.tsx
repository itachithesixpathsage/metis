import { cn } from '../../utils/cn';

export const gridDashboard = 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-6';

interface PageProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export function Page({ title, subtitle, children }: PageProps) {
  return (
    <div className="page-content">
      <div className="page-header-content mb-6">
        <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
        {subtitle && <p className="text-slate-400 mt-1">{subtitle}</p>}
      </div>
      <div className="animate-in">{children}</div>
    </div>
  );
}

interface CardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export function Card({ title, subtitle, children, className, action }: CardProps) {
  return (
    <div className={cn('card card-hover', className)}>
      <div className="p-5 border-b border-slate-800 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
}

export function StatCard({ label, value, change, changeType = 'neutral', icon }: StatCardProps) {
  return (
    <div className="card card-hover p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-semibold text-slate-100 mono mt-1">{value}</p>
        </div>
        {icon && <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center text-xl">{icon}</div>}
      </div>
      {change && (
        <div className="mt-3 flex items-center gap-1">
          <span className={cn(
            'text-xs font-medium',
            changeType === 'positive' && 'text-green-400',
            changeType === 'negative' && 'text-red-400',
            changeType === 'neutral' && 'text-slate-400'
          )}>
            {change}
          </span>
          <span className="text-xs text-slate-500">vs previous period</span>
        </div>
      )}
    </div>
  );
}
