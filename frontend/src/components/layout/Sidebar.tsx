import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../../utils/cn';

const navigation = [
  { name: 'Portfolio Overview', href: '/dashboard', icon: '📊' },
  { name: 'Market Data', href: '/market-data', icon: '📈' },
  { name: 'Statistical Analysis', href: '/statistical-analysis', icon: '📉' },
  { name: 'Simulation Lab', href: '/simulation-lab', icon: '🧪' },
  { name: 'Risk Lab', href: '/risk-lab', icon: '⚠️' },
  { name: 'Decision Centre', href: '/decision-centre', icon: '🎯' },
  { name: 'Model Validation', href: '/model-validation', icon: '✅' },
  { name: 'Research Reports', href: '/research-reports', icon: '📄' },
] as const;

interface SidebarProps {
  className?: string;
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ className, open, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={cn('sidebar', className)}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex flex-col h-full">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
          <div className="w-10 h-10 rounded-lg bg-metis-600/20 flex items-center justify-center">
            <span className="text-xl">📐</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-100">Project Métis</h1>
            <p className="text-xs text-slate-500">Quantitative FX Research</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto" aria-label="Primary">
          <ul className="space-y-1" role="list">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <li key={item.href}>
                  <NavLink
                    to={item.href}
                    onClick={onClose}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                      isActive
                        ? 'text-slate-100 bg-slate-800 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <span aria-hidden="true">{item.icon}</span>
                    <span>{item.name}</span>
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-metis-500" aria-hidden="true" />
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-slate-800">
          <div className="text-xs text-slate-500 text-center">
            v0.1.0 • Research Mode
          </div>
        </div>
      </div>
    </aside>
  );
}