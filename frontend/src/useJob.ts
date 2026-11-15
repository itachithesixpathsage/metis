import { useEffect, useState } from 'react';
import { apiRequest, type AsyncJob } from './api';

export function useJob(jobId: string | null) {
  const [job, setJob] = useState<AsyncJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!jobId) { setJob(null); setError(null); return; }
    let active = true;
    let timer = 0;
    const poll = async () => {
      try {
        const current = await apiRequest<AsyncJob>(`/jobs/${jobId}`);
        if (!active) return;
        setJob(current);
        setError(null);
        if (current.status === 'queued' || current.status === 'running') timer = window.setTimeout(poll, 500);
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : 'Could not check job status');
      }
    };
    void poll();
    return () => { active = false; window.clearTimeout(timer); };
  }, [jobId]);
  return { job, error };
}
