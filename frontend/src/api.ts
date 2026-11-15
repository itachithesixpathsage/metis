const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '');

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
}

export interface DashboardData {
  metrics: { label: string; value: string; change: string; change_type: 'positive' | 'negative' | 'neutral' }[];
  positions: { pair: string; direction: string; notional: string; entry: string; current: string; pnl: string; risk_pct: string }[];
  exposures: { currency: string; value: string; width: string; direction: 'positive' | 'negative' }[];
  var_decomposition: { pair: string; cvar: string; pct: string }[];
  recent_decisions: { time: string; pair: string; action: string; reason: string; type: string }[];
}

export interface PriceSeries { symbol: string; provider: string; frequency: string; data: { timestamp: string; price: number }[] }
export interface AnalyticsReturns { method: string; returns: number[]; mean: number; volatility: number }
export interface VolatilityResult { volatility: number; annualized_volatility: number; observations: number }
export interface AsyncJob { job_id: string; status: 'queued' | 'running' | 'completed' | 'failed'; progress: number; result?: Record<string, unknown> | null; error?: string | null; report_id?: string | null }
export interface Portfolio { portfolio_id: string; name: string; base_currency: string; positions: { symbol: string; side: 'long' | 'short'; notional: number; entry_price: number }[]; created_at: string }
export interface RiskResult { confidence: number; var: number; expected_shortfall: number; max_drawdown: number }
export interface DecisionResult { approved: boolean; action: string; reason: string; evaluated_at: string }
export interface Report { report_id: string; title: string; generated_at: string; summary: string; metrics: Record<string, number | string> }

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json() as { detail?: unknown };
      message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* Keep the HTTP status message. */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`API health check failed (${response.status})`);
  }
  return response.json() as Promise<HealthResponse>;
}

export async function getDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/mock/dashboard`);
  if (!response.ok) {
    throw new Error(`Dashboard request failed (${response.status})`);
  }
  return response.json() as Promise<DashboardData>;
}
