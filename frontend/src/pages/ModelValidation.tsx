import { useState, type FormEvent } from 'react';
import { apiRequest, type AsyncJob } from '../api';
import { Card, Page } from '../components/ui/PageComponents';
import { useJob } from '../useJob';

export function ModelValidation() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { job, error: pollingError } = useJob(jobId);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setJobId(null); setError(null);
    const form = new FormData(event.currentTarget);
    try {
      const result = await apiRequest<AsyncJob>('/backtesting/run', { method: 'POST', body: JSON.stringify({ symbol: form.get('symbol'), strategy: form.get('strategy'), start: new Date(String(form.get('start'))).toISOString(), end: new Date(String(form.get('end'))).toISOString(), initial_capital: Number(form.get('capital')) }) });
      setJobId(result.job_id);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not submit backtest'); }
  };
  return <Page title="Model Validation" subtitle="Run a backtest asynchronously and inspect its generated report" eyebrow="Research workspace">
    <Card title="Strategy backtest" subtitle="POST /api/v1/backtesting/run · poll GET /api/v1/jobs/{job_id}">
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <label className="text-sm">Symbol<input name="symbol" defaultValue="EURUSD" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Strategy<input name="strategy" defaultValue="momentum" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Initial capital<input name="capital" type="number" min="1" defaultValue="100000" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Start date<input name="start" type="date" required defaultValue="2025-01-01" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">End date<input name="end" type="date" required defaultValue="2025-12-31" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <button className="self-end rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950">Run backtest</button>
      </form>
      {(error || pollingError) && <p role="alert" className="mt-4 text-red-400">{error ?? pollingError}</p>}
      {job && <div className="mt-5 rounded bg-slate-800 p-4"><p>Job {job.job_id} · {job.status} · {job.progress}%</p><progress className="mt-2 w-full" max="100" value={job.progress} />
        {job.result && <pre className="mt-3 overflow-auto text-sm">{JSON.stringify(job.result, null, 2)}</pre>}{job.report_id && <p className="mt-2 text-sm text-lime-300">Report ID: {job.report_id}</p>}{job.error && <p className="text-red-400">{job.error}</p>}</div>}
    </Card>
  </Page>;
}
