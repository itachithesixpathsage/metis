import { useState, type FormEvent } from 'react';
import { apiRequest, type AsyncJob } from '../api';
import { Card, Page } from '../components/ui/PageComponents';
import { useJob } from '../useJob';

export function SimulationLab() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { job, error: pollingError } = useJob(jobId);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError(null); setJobId(null);
    const form = new FormData(event.currentTarget);
    try {
      const response = await apiRequest<AsyncJob>('/simulations', { method: 'POST', body: JSON.stringify({ symbol: form.get('symbol'), initial_price: Number(form.get('initial_price')), volatility: Number(form.get('volatility')), drift: Number(form.get('drift')), paths: Number(form.get('paths')), steps: Number(form.get('steps')) }) });
      setJobId(response.job_id);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not submit simulation'); }
  };
  return <Page title="Simulation Laboratory" subtitle="Submit a simulation job and follow its progress" eyebrow="Research workspace">
    <Card title="Monte Carlo simulation" subtitle="POST /api/v1/simulations · poll GET /api/v1/jobs/{job_id}">
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <label className="text-sm">Symbol<input name="symbol" defaultValue="EURUSD" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Initial price<input name="initial_price" type="number" step="any" defaultValue="1.085" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Annual drift<input name="drift" type="number" step="any" defaultValue="0" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Volatility<input name="volatility" type="number" step="any" defaultValue="0.1" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Paths<input name="paths" type="number" min="100" defaultValue="10000" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <label className="text-sm">Steps<input name="steps" type="number" min="1" defaultValue="16" className="block mt-1 w-full rounded bg-slate-800 p-2" /></label>
        <button className="rounded bg-lime-300 px-4 py-2 font-semibold text-slate-950 sm:col-span-2 lg:col-span-3">Start simulation</button>
      </form>
      {(error || pollingError) && <p role="alert" className="mt-4 text-red-400">{error ?? pollingError}</p>}
      {job && <div className="mt-5 rounded bg-slate-800 p-4"><p>Job {job.job_id} · {job.status} · {job.progress}%</p><progress className="mt-2 w-full" max="100" value={job.progress} />
        {job.result && <pre className="mt-3 overflow-auto text-sm">{JSON.stringify(job.result, null, 2)}</pre>}{job.report_id && <p className="mt-2 text-sm text-lime-300">Report ID: {job.report_id}</p>}{job.error && <p className="text-red-400">{job.error}</p>}</div>}
    </Card>
  </Page>;
}
