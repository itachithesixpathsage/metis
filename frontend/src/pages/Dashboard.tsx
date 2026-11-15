import { useEffect, useState } from 'react';
import { getDashboard, type DashboardData } from '../api';
import { Page, Card, StatCard, gridDashboard } from '../components/ui/PageComponents';
import { PortfolioApiPanel } from '../components/PortfolioApiPanel';

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getDashboard().then((result) => {
      if (active) setData(result);
    }).catch((cause: unknown) => {
      if (active) setError(cause instanceof Error ? cause.message : 'Could not load dashboard data');
    });
    return () => { active = false; };
  }, []);

  return (
    <Page title="Portfolio Overview" subtitle="Portfolio risk dashboard and position monitoring">
      {error && <div role="alert" className="card p-4 text-red-400">Dashboard data could not be loaded: {error}</div>}
      {!data && !error && <div role="status" className="card p-4 text-slate-400">Loading portfolio data…</div>}
      {data && <>
        <PortfolioApiPanel />
        <div className={gridDashboard}>
          {data.metrics.map((metric) => <StatCard key={metric.label} label={metric.label} value={metric.value} change={metric.change} changeType={metric.change_type} />)}
        </div>

        <div className="grid-2">
          <Card title="Active Positions" subtitle="Current FX portfolio positions">
            <div className="table-container"><table className="table">
              <thead><tr><th>Pair</th><th className="text-right">Direction</th><th className="text-right">Notional</th><th className="text-right">Entry</th><th className="text-right">Current</th><th className="text-right">Unrealized P&amp;L</th><th className="text-right">Risk %</th></tr></thead>
              <tbody>{data.positions.map((position) => <tr key={position.pair}>
                <td className="font-mono font-medium">{position.pair}</td>
                <td className="text-right"><span className={`badge badge-${position.direction === 'LONG' ? 'success' : 'danger'}`}>{position.direction}</span></td>
                <td className="text-right mono">{position.notional}</td><td className="text-right mono">{position.entry}</td><td className="text-right mono">{position.current}</td>
                <td className="text-right mono number-positive">{position.pnl}</td><td className="text-right mono">{position.risk_pct}</td>
              </tr>)}</tbody>
            </table></div>
          </Card>

          <Card title="Currency Exposure" subtitle="Net currency exposure by base currency">
            <div className="space-y-4">{data.exposures.map((exposure) => <div key={exposure.currency}>
              <div className="flex justify-between text-sm mb-1"><span>{exposure.currency}</span><span className={`font-mono font-medium number-${exposure.direction}`}>{exposure.value}</span></div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full" style={{ width: exposure.width, backgroundColor: exposure.direction === 'positive' ? '#22c55e' : '#ef4444' }} /></div>
            </div>)}</div>
          </Card>
        </div>

        <div className="grid-2">
          <Card title="VaR Decomposition" subtitle="Component VaR by position">
            <div className="space-y-3">{data.var_decomposition.map((item) => <div key={item.pair} className="flex items-center justify-between">
              <div className="flex items-center gap-3"><div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center text-xs font-mono">{item.pair.split('/')[0]}</div><span className="font-medium">{item.pair}</span></div>
              <div className="text-right"><div className="font-mono text-slate-200">{item.cvar}</div><div className="text-xs text-slate-500">{item.pct} of total</div></div>
            </div>)}</div>
          </Card>

          <Card title="Recent Decisions" subtitle="Latest risk engine recommendations">
            <div className="space-y-3">{data.recent_decisions.map((item) => <div key={`${item.time}-${item.pair}`} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
              <div className="flex items-center gap-3"><span className="text-xs text-slate-500 font-mono">{item.time}</span><span className="font-mono font-medium">{item.pair}</span><span className={`badge badge-${item.type === 'success' ? 'success' : 'warning'}`}>{item.action}</span></div>
              <span className="text-xs text-slate-500 max-w-[200px] truncate">{item.reason}</span>
            </div>)}</div>
          </Card>
        </div>
      </>}
    </Page>
  );
}
