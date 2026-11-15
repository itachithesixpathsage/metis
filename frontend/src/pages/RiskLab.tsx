import { useState } from 'react';
import { apiRequest, type PriceSeries, type RiskResult } from '../api';
import { Card, Page, StatCard } from '../components/ui/PageComponents';

export function RiskLab() {
  const [symbol, setSymbol] = useState('EURUSD');
  const [confidence, setConfidence] = useState('0.95');
  const [risk, setRisk] = useState<RiskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const analyze = async () => {
    setLoading(true); setError(null); setRisk(null);
    try {
      const series = await apiRequest<PriceSeries>(`/market-data/${symbol.toUpperCase()}`);
      const prices = series.data.map(point => point.price);
      const returns = prices.slice(1).map((price, index) => Math.log(price / prices[index]));
      setRisk(await apiRequest<RiskResult>('/risk/analyze', { method: 'POST', body: JSON.stringify({ returns, confidence: Number(confidence) }) }));
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Risk analysis failed'); }
    finally { setLoading(false); }
  };
  return <Page title="Risk Laboratory" subtitle="Historical VaR, expected shortfall, and drawdown from the risk API" eyebrow="Research workspace">
    <Card title="Historical risk analysis" subtitle="Market data → POST /api/v1/risk/analyze">
      <div className="flex flex-wrap items-end gap-3 mb-5"><label className="text-sm">FX symbol<input className="block mt-1 rounded bg-slate-800 p-2" value={symbol} onChange={e => setSymbol(e.target.value)} /></label>
        <label className="text-sm">Confidence<select className="block mt-1 rounded bg-slate-800 p-2" value={confidence} onChange={e => setConfidence(e.target.value)}><option value="0.95">95%</option><option value="0.99">99%</option></select></label>
        <button onClick={() => void analyze()} disabled={loading} className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950">{loading ? 'Calculating…' : 'Analyze risk'}</button></div>
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {risk && <div className="grid-dashboard"><StatCard label={`VaR (${(risk.confidence * 100).toFixed(0)}%)`} value={`${(risk.var * 100).toFixed(3)}%`} /><StatCard label="Expected shortfall" value={`${(risk.expected_shortfall * 100).toFixed(3)}%`} /><StatCard label="Maximum drawdown" value={`${(risk.max_drawdown * 100).toFixed(3)}%`} /></div>}
    </Card>
  </Page>;
}
