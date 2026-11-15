const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '');

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  environment: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`API health check failed (${response.status})`);
  }
  return response.json() as Promise<HealthResponse>;
}
