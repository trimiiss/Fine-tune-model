import type { Dataset, Experiment, ModelOption } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...(options?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options?.headers },
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(detail.detail ?? 'Request failed')
  }
  return response.json()
}

export const api = {
  dashboard: () => request<{ experiments: number; datasets: number; completed: number; running: number; total_records: number; recent: Experiment[] }>('/dashboard'),
  datasets: () => request<Dataset[]>('/datasets'),
  uploadDataset: (file: File) => { const form = new FormData(); form.append('file', file); return request<Dataset>('/datasets/upload', { method: 'POST', body: form }) },
  deleteDataset: (id: string) => request<{ ok: boolean }>(`/datasets/${id}`, { method: 'DELETE' }),
  models: () => request<ModelOption[]>('/models'),
  experiments: () => request<Experiment[]>('/experiments'),
  createExperiment: (payload: unknown) => request<Experiment>('/experiments', { method: 'POST', body: JSON.stringify(payload) }),
  startTraining: (id: string) => request<Experiment>(`/experiments/${id}/train`, { method: 'POST' }),
  generate: (payload: unknown) => request<{ response: string; model: string; generated_tokens: number }>('/playground/generate', { method: 'POST', body: JSON.stringify(payload) }),
}

export const formatDate = (value: string) => new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
