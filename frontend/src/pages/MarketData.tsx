import { useEffect, useState, type FormEvent } from 'react';
import { apiRequest, type PriceSeries } from '../api';
import { Card, Page } from '../components/ui/PageComponents';

export function MarketData() {
  const [symbol, setSymbol] = useState('EURUSD');
  const [series, setSeries] = useState<PriceSeries | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const load = async (event?: FormEvent) => {
    event?.preventDefault(); setLoading(true); setError(null);
    try { setSeries(await apiRequest<PriceSeries>(`/market-data/${symbol.trim().toUpperCase()}`)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Market data request failed'); }
    finally { setLoading(false); }
  };
  const queryRange = async () => {
    setLoading(true); setError(null);
    try {
      const end = new Date();
      const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
      const result = await apiRequest<Record<string, PriceSeries>>('/market-data/query', { method: 'POST', body: JSON.stringify({ symbols: [symbol.trim().toUpperCase()], start: start.toISOString(), end: end.toISOString(), frequency: '15min' }) });
      setSeries(result[symbol.trim().toUpperCase()]);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Market data query failed'); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  return <Page title="Market Data" subtitle="Intraday FX market data from the synthetic API feed" eyebrow="Research workspace">
    <Card title="FX price series" subtitle="GET /api/v1/market-data/{symbol}">
      <form onSubmit={load} className="flex flex-wrap items-end gap-3 mb-5">
        <label className="text-sm">Symbol<input className="block mt-1 rounded bg-slate-800 p-2" value={symbol} onChange={e => setSymbol(e.target.value)} maxLength={6} /></label>
        <button className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950" disabled={loading}>{loading ? 'Loading…' : 'Load series'}</button>
        <button type="button" onClick={() => void queryRange()} disabled={loading} className="rounded border border-slate-600 px-4 py-2">Query last 24 hours</button>
      </form>
      {error && <p role="alert" className="text-red-400">{error}</p>}
      {series && <><p className="mb-3 text-sm text-slate-400">{series.symbol} · {series.provider} · {series.frequency} · {series.data.length} observations</p>
        <div className="table-container"><table className="table"><thead><tr><th>Timestamp (UTC)</th><th className="text-right">Price</th></tr></thead>
          <tbody>{series.data.slice(-20).reverse().map(point => <tr key={point.timestamp}><td>{new Date(point.timestamp).toLocaleString()}</td><td className="text-right mono">{point.price.toFixed(5)}</td></tr>)}</tbody></table></div>
      </>}
    </Card>
  </Page>;
}
