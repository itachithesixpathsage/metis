import { NavLink } from 'react-router-dom';
import { cn } from '../../utils/cn';

const groups = [
  { label: 'Monitor', links: [{ name: 'Portfolio overview', href: '/dashboard', icon: '01' }, { name: 'Market data', href: '/market-data', icon: '02' }] },
  { label: 'Research', links: [{ name: 'Statistical analysis', href: '/statistical-analysis', icon: '03' }, { name: 'Simulation lab', href: '/simulation-lab', icon: '04' }, { name: 'Risk laboratory', href: '/risk-lab', icon: '05' }] },
  { label: 'Governance', links: [{ name: 'Decision centre', href: '/decision-centre', icon: '06' }, { name: 'Model validation', href: '/model-validation', icon: '07' }, { name: 'Research reports', href: '/research-reports', icon: '08' }] },
];

interface SidebarProps { className?: string; onClose: () => void; }
export function Sidebar({ className, onClose }: SidebarProps) {
  return <aside className={cn('sidebar', className)} aria-label="Main navigation">
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-5">
        <div className="brand-mark" aria-hidden="true">M.</div>
        <div><h1 className="m-0 text-sm font-semibold tracking-tight text-slate-100">Project Métis</h1><p className="m-0 mt-1 text-[10px] tracking-wide text-slate-500">QUANTITATIVE FX RESEARCH</p></div>
      </div>
      <nav className="flex-1 overflow-y-auto" aria-label="Primary">
        {groups.map(group => <div key={group.label} className="mb-5">
          <div className="nav-section">{group.label}</div>
          {group.links.map(item => <NavLink key={item.href} to={item.href} onClick={onClose} className={({ isActive }) => cn('nav-link', isActive && 'active')}>
            <span className="nav-glyph" aria-hidden="true">{item.icon}</span><span>{item.name}</span>
          </NavLink>)}
        </div>)}
      </nav>
      <div className="sidebar-footer flex items-center justify-between"><span>RESEARCH MODE</span><span>v0.1</span></div>
    </div>
  </aside>;
}
