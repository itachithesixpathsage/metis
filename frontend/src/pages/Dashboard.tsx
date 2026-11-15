import { Page, Card, StatCard, gridDashboard } from '../components/ui/PageComponents';

export function Dashboard() {
  return (
    <Page
      title="Portfolio Overview"
      subtitle="Real-time portfolio risk dashboard and position monitoring"
    >
      {/* Key Metrics */}
      <div className={gridDashboard}>
        <StatCard
          label="Total Portfolio Value"
          value="$2,847,392"
          change="+2.34%"
          changeType="positive"
          icon="💰"
        />
        <StatCard
          label="Portfolio VaR (95%)"
          value="-$34,218"
          change="-1.2%"
          changeType="positive"
          icon="⚠️"
        />
        <StatCard
          label="Expected Shortfall (95%)"
          value="-$47,891"
          change="-0.8%"
          changeType="positive"
          icon="📉"
        />
        <StatCard
          label="Max Drawdown"
          value="-4.72%"
          change="+0.3%"
          changeType="negative"
          icon="📊"
        />
        <StatCard
          label="Gross Exposure"
          value="$8,940,000"
          change="+5.1%"
          changeType="neutral"
          icon="📈"
        />
        <StatCard
          label="Net Exposure"
          value="$1,240,000"
          change="-2.4%"
          changeType="positive"
          icon="🔄"
        />
      </div>

      {/* Portfolio Positions & Risk Breakdown */}
      <div className="grid-2">
        <Card title="Active Positions" subtitle="Current FX portfolio positions">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Pair</th>
                  <th className="text-right">Direction</th>
                  <th className="text-right">Notional</th>
                  <th className="text-right">Entry</th>
                  <th className="text-right">Current</th>
                  <th className="text-right">Unrealized P&L</th>
                  <th className="text-right">Risk %</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-mono font-medium">EUR/USD</td>
                  <td className="text-right"><span className="badge badge-success">LONG</span></td>
                  <td className="text-right mono">€2,500,000</td>
                  <td className="text-right mono">1.0845</td>
                  <td className="text-right mono">1.0912</td>
                  <td className="text-right mono number-positive">+$15,420</td>
                  <td className="text-right mono">2.1%</td>
                </tr>
                <tr>
                  <td className="font-mono font-medium">GBP/USD</td>
                  <td className="text-right"><span className="badge badge-danger">SHORT</span></td>
                  <td className="text-right mono">£1,800,000</td>
                  <td className="text-right mono">1.2678</td>
                  <td className="text-right mono">1.2634</td>
                  <td className="text-right mono number-positive">+$7,920</td>
                  <td className="text-right mono">1.4%</td>
                </tr>
                <tr>
                  <td className="font-mono font-medium">USD/JPY</td>
                  <td className="text-right"><span className="badge badge-success">LONG</span></td>
                  <td className="text-right mono">$3,000,000</td>
                  <td className="text-right mono">151.45</td>
                  <td className="text-right mono">152.18</td>
                  <td className="text-right mono number-positive">+$14,580</td>
                  <td className="text-right mono">1.8%</td>
                </tr>
                <tr>
                  <td className="font-mono font-medium">AUD/USD</td>
                  <td className="text-right"><span className="badge badge-danger">SHORT</span></td>
                  <td className="text-right mono">AUD 2,200,000</td>
                  <td className="text-right mono">0.6589</td>
                  <td className="text-right mono">0.6542</td>
                  <td className="text-right mono number-positive">+$10,340</td>
                  <td className="text-right mono">1.2%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Currency Exposure" subtitle="Net currency exposure by base currency">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>USD</span>
                <span className="font-mono font-medium number-positive">+$1,240,000</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: '45%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>EUR</span>
                <span className="font-mono font-medium number-positive">+€2,500,000</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: '52%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>GBP</span>
                <span className="font-mono font-medium number-negative">-£1,800,000</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-red-500" style={{ width: '38%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>JPY</span>
                <span className="font-mono font-medium number-positive">+¥456,540,000</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: '48%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>AUD</span>
                <span className="font-mono font-medium number-negative">-AUD 2,200,000</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-red-500" style={{ width: '22%' }} />
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Risk Decomposition */}
      <div className="grid-2">
        <Card title="VaR Decomposition" subtitle="Component VaR by position">
          <div className="space-y-3">
            {[
              { pair: 'EUR/USD', cvar: '$12,840', pct: '37.5%' },
              { pair: 'GBP/USD', cvar: '$8,210', pct: '24.0%' },
              { pair: 'USD/JPY', cvar: '$9,150', pct: '26.7%' },
              { pair: 'AUD/USD', cvar: '$4,018', pct: '11.8%' },
            ].map((item) => (
              <div key={item.pair} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center text-xs font-mono">
                    {item.pair.split('/')[0]}
                  </div>
                  <span className="font-medium">{item.pair}</span>
                </div>
                <div className="text-right">
                  <div className="font-mono text-slate-200">{item.cvar}</div>
                  <div className="text-xs text-slate-500">{item.pct} of total</div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Recent Decisions" subtitle="Latest risk engine recommendations">
          <div className="space-y-3">
            {[
              { time: '14:32', pair: 'EUR/USD', action: 'HOLD', reason: 'All constraints satisfied', type: 'success' },
              { time: '13:45', pair: 'GBP/USD', action: 'REDUCE', reason: 'Soft VaR limit breached (92%)', type: 'warning' },
              { time: '12:18', pair: 'USD/JPY', action: 'HOLD', reason: 'All constraints satisfied', type: 'success' },
              { time: '11:05', pair: 'AUD/USD', action: 'HOLD', reason: 'All constraints satisfied', type: 'success' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 font-mono">{item.time}</span>
                  <span className="font-mono font-medium">{item.pair}</span>
                  <span className={`badge badge-${item.type === 'success' ? 'success' : 'warning'}`}>{item.action}</span>
                </div>
                <span className="text-xs text-slate-500 max-w-[200px] truncate">{item.reason}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Page>
  );
}