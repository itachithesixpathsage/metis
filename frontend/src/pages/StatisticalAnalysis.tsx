import { useState } from 'react';
import { apiRequest, type AnalyticsReturns, type PriceSeries, type VolatilityResult } from '../api';
import { Card, Page, StatCard } from '../components/ui/PageComponents';

export function StatisticalAnalysis() {
  const [symbol, setSymbol] = useState('EURUSD');
  const [returns, setReturns] = useState<AnalyticsReturns | null>(null);
  const [volatility, setVolatility] = useState<VolatilityResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const analyze = async () => {
    setLoading(true); setError(null); setReturns(null); setVolatility(null);
    try {
      const prices = await apiRequest<PriceSeries>(`/market-data/${symbol.toUpperCase()}`);
      const result = await apiRequest<AnalyticsReturns>('/analytics/returns', { method: 'POST', body: JSON.stringify({ prices: prices.data.map(point => point.price), method: 'log' }) });
      const vol = await apiRequest<VolatilityResult>('/analytics/volatility', { method: 'POST', body: JSON.stringify({ returns: result.returns, annualization_factor: 252 }) });
      setReturns(result); setVolatility(vol);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Analysis request failed'); }
    finally { setLoading(false); }
  };
  return <Page title="Statistical Analysis" subtitle="Returns and realized volatility calculated by the analytics API" eyebrow="Research workspace">
    <Card title="Return and volatility analysis" subtitle="Market data → POST /analytics/returns → POST /analytics/volatility">
      <div className="flex items-end gap-3 mb-5"><label className="text-sm">FX symbol<input className="block mt-1 rounded bg-slate-800 p-2" value={symbol} onChange={e => setSymbol(e.target.value)} /></label>
        <button onClick={() => void analyze()} disabled={loading} className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950">{loading ? 'Analyzing…' : 'Run analysis'}</button></div>
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {returns && volatility && <><div className="grid-dashboard"><StatCard label="Mean log return" value={returns.mean.toFixed(7)} /><StatCard label="Period volatility" value={volatility.volatility.toFixed(6)} /><StatCard label="Annualized volatility" value={`${(volatility.annualized_volatility * 100).toFixed(2)}%`} /><StatCard label="Observations" value={volatility.observations} /></div>
        <div className="mt-5 table-container"><table className="table"><thead><tr><th>Recent log returns</th></tr></thead><tbody>{returns.returns.slice(-12).reverse().map((value, index) => <tr key={index}><td className="mono">{value.toFixed(7)}</td></tr>)}</tbody></table></div></>}
    </Card>
  </Page>;
}
