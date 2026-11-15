import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { getHealth, type HealthResponse } from '../../api';

const titles: Record<string, string> = {
  '/dashboard': 'PORTFOLIO / OVERVIEW', '/market-data': 'RESEARCH / MARKET DATA', '/statistical-analysis': 'RESEARCH / STATISTICS',
  '/simulation-lab': 'RESEARCH / SIMULATION', '/risk-lab': 'RESEARCH / RISK', '/decision-centre': 'GOVERNANCE / DECISIONS',
  '/model-validation': 'GOVERNANCE / VALIDATION', '/research-reports': 'GOVERNANCE / REPORTS',
};
interface HeaderProps { onMenuClick: () => void; }
export function Header({ onMenuClick }: HeaderProps) {
  const { pathname } = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    const refreshHealth = async () => {
      try {
        const result = await getHealth();
        if (active) {
          setHealth(result);
          setApiUnavailable(false);
        }
      } catch {
        if (active) {
          setApiUnavailable(true);
          setHealth(null);
        }
      }
    };

    void refreshHealth();
    const interval = window.setInterval(() => void refreshHealth(), 30_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return <header className="page-header"><div className="header-inner">
    <div className="flex items-center gap-4"><button type="button" onClick={onMenuClick} className="menu-button lg:hidden" aria-label="Open navigation menu">
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M4 6h16M4 12h16M4 18h16"/></svg>
    </button><span className="header-title">{titles[pathname] ?? 'METIS / RESEARCH'}</span></div>
    <div className="flex items-center gap-4"><div className="header-status" title={health ? `API v${health.version} · ${health.environment}` : undefined}><span className="status-dot" style={{ backgroundColor: health ? '#d4f36c' : apiUnavailable ? '#f87171' : '#94a3b8' }}/><span>{health ? `API ${health.status}` : apiUnavailable ? 'API unavailable' : 'Checking API'}</span></div><span className="header-pill">{health ? `v${health.version}` : 'API'}</span><div className="grid h-8 w-8 place-items-center rounded-full border border-[#3b493f] bg-[#263329] font-mono text-xs text-[#d4f36c]">M</div></div>
  </div></header>;
}
