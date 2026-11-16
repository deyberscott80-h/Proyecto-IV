import type { NewReview, Review, ReviewStats } from './types';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ? (typeof error.detail === 'string' ? error.detail : 'Revisa los datos del formulario') : `Error HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  list: () => request<Review[]>('/api/reviews'),
  stats: () => request<ReviewStats>('/api/reviews/stats'),
  create: (data: NewReview) => request<Review>('/api/reviews', { method:'POST', body:JSON.stringify(data) }),
  reply: (id:number, response:string) => request<Review>(`/api/reviews/${id}/reply`, { method:'PATCH', body:JSON.stringify({response}) }),
  visibility: (id:number, visible:boolean) => request<Review>(`/api/reviews/${id}/visibility`, { method:'PATCH', body:JSON.stringify({visible}) }),
  delete: (id:number) => request<void>(`/api/reviews/${id}`, { method:'DELETE' }),
};
