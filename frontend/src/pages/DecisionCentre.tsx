import { useState, type FormEvent } from 'react';
import { apiRequest, type DecisionResult } from '../api';
import { Card, Page } from '../components/ui/PageComponents';

export function DecisionCentre() {
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError(null); setResult(null);
    const form = new FormData(event.currentTarget);
    try { setResult(await apiRequest<DecisionResult>('/decisions/evaluate', { method: 'POST', body: JSON.stringify({ symbol: form.get('symbol'), current_risk: Number(form.get('current_risk')), risk_limit: Number(form.get('risk_limit')), proposed_action: form.get('action') }) })); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Decision evaluation failed'); }
  };
  return <Page title="Decision Centre" subtitle="Evaluate a proposed action against a risk limit" eyebrow="Research workspace">
    <Card title="Risk policy evaluation" subtitle="POST /api/v1/decisions/evaluate">
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm">Symbol<input name="symbol" defaultValue="EURUSD" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Current risk<input name="current_risk" type="number" min="0" step="any" defaultValue="0.8" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Risk limit<input name="risk_limit" type="number" min="0.000001" step="any" defaultValue="1" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Proposed action<select name="action" className="block mt-1 w-full rounded bg-slate-800 p-2"><option>hold</option><option>increase</option><option>reduce</option><option>close</option></select></label>
        <button className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950 sm:col-span-2 lg:col-span-4">Evaluate decision</button>
      </form>
      {error && <p role="alert" className="mt-4 text-red-400">{error}</p>}
      {result && <div className="mt-5 rounded bg-slate-800 p-4"><p className={result.approved ? 'text-green-400' : 'text-amber-400'}>{result.approved ? 'Approved' : 'Not approved'} · {result.action.toUpperCase()}</p><p className="mt-2">{result.reason}</p><p className="mt-2 text-xs text-slate-400">Evaluated {new Date(result.evaluated_at).toLocaleString()}</p></div>}
    </Card>
  </Page>;
}
