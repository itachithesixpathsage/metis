import { useState, type FormEvent } from 'react';
import { apiRequest, type Portfolio } from '../api';
import { Card } from './ui/PageComponents';

export function PortfolioApiPanel() {
  const [name, setName] = useState('Research portfolio');
  const [portfolioId, setPortfolioId] = useState('');
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  const create = async (event: FormEvent) => {
    event.preventDefault(); setError(null);
    try {
      const result = await apiRequest<Portfolio>('/portfolio', { method: 'POST', body: JSON.stringify({ name, base_currency: 'USD', positions: [{ symbol: 'EURUSD', side: 'long', notional: 100000, entry_price: 1.085 }] }) });
      setPortfolio(result); setPortfolioId(result.portfolio_id);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create portfolio'); }
  };
  const load = async (event: FormEvent) => {
    event.preventDefault(); setError(null);
    try { setPortfolio(await apiRequest<Portfolio>(`/portfolio/${portfolioId.trim()}`)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load portfolio'); }
  };
  return <Card title="Mock portfolio API" subtitle="Create and retrieve an in-memory portfolio">
    <div className="grid gap-5 lg:grid-cols-2">
      <form onSubmit={create} className="flex items-end gap-3"><label className="text-sm">Portfolio name<input value={name} onChange={e => setName(e.target.value)} required className="mt-1 block w-full rounded bg-slate-800 p-2" /></label><button className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950">Create</button></form>
      <form onSubmit={load} className="flex items-end gap-3"><label className="text-sm">Portfolio ID<input value={portfolioId} onChange={e => setPortfolioId(e.target.value)} required className="mt-1 block w-full rounded bg-slate-800 p-2" /></label><button className="rounded border border-slate-600 px-4 py-2">Retrieve</button></form>
    </div>
    {error && <p role="alert" className="mt-4 text-red-400">{error}</p>}
    {portfolio && <p className="mt-4 text-sm text-slate-300">{portfolio.name} · {portfolio.base_currency} · {portfolio.positions.length} positions · ID {portfolio.portfolio_id}</p>}
  </Card>;
}
