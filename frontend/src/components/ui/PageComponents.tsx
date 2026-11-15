import { cn } from '../../utils/cn';

export const gridDashboard = 'grid-dashboard';

interface PageProps { title: string; subtitle?: string; children: React.ReactNode; eyebrow?: string; action?: React.ReactNode; }
export function Page({ title, subtitle, children, eyebrow = 'Portfolio intelligence', action }: PageProps) {
  return <div className="page-content animate-in">
    <div className="page-heading">
      <div><div className="eyebrow">{eyebrow}</div><h1 className="page-title">{title}</h1>{subtitle && <p className="page-subtitle">{subtitle}</p>}</div>
      {action}
    </div>
    {children}
  </div>;
}

interface CardProps { title: string; subtitle?: string; children: React.ReactNode; className?: string; action?: React.ReactNode; }
export function Card({ title, subtitle, children, className, action }: CardProps) {
  return <section className={cn('card card-hover', className)}>
    <div className="card-head"><div><h2 className="card-title">{title}</h2>{subtitle && <p className="card-subtitle">{subtitle}</p>}</div>{action}</div>
    <div className="card-body">{children}</div>
  </section>;
}

interface StatCardProps { label: string; value: string | number; change?: string; changeType?: 'positive' | 'negative' | 'neutral'; icon?: React.ReactNode; }
export function StatCard({ label, value, change, changeType = 'neutral' }: StatCardProps) {
  return <div className="card stat-card">
    <div className="stat-label">{label}</div><div className="stat-value mono">{value}</div>
    {change && <div className="stat-foot"><span className={cn('stat-change', `stat-${changeType}`)}>{change}</span><span>vs previous period</span></div>}
  </div>;
}

interface ModulePlaceholderProps { name: string; description: string; code: string; focus: string[]; }
export function ModulePlaceholder({ name, description, code, focus }: ModulePlaceholderProps) {
  return <div className="card module-panel">
    <div className="module-copy">
      <div className="eyebrow">Research workspace / {code}</div>
      <h2 className="module-title">A clearer view of {name.toLowerCase()}.</h2>
      <p>{description} This workspace is being prepared for the research workflow, with the core inputs and outputs brought together in one place.</p>
      <div className="module-meta">{focus.map(item => <span key={item}>{item}</span>)}</div>
    </div>
    <div className="module-visual" aria-hidden="true">
      <div className="module-orbit"/><div className="module-core">{code}</div>
      <span className="module-chip one">INPUTS</span><span className="module-chip two">ANALYSIS</span><span className="module-chip three">OUTPUT</span>
    </div>
  </div>;
}
