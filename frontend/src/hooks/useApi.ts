import { useCallback } from 'react';

const base = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const tokenKey = 'qarzdaftar_token';

export function setToken(token: string | null) {
  if (token) localStorage.setItem(tokenKey, token);
  else localStorage.removeItem(tokenKey);
}
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = localStorage.getItem(tokenKey);
  if (token) headers.set('Authorization', 'Bearer ' + token);
  if (options.body) headers.set('Content-Type', 'application/json');
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 25000);
  try {
    const response = await fetch(base + '/api/v1' + path,
      Object.assign({}, options, { headers, signal: controller.signal }));
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401) {
        setToken(null);
        window.dispatchEvent(new Event('qarzdaftar:unauthorized'));
      }
      throw new ApiError(typeof body?.detail === 'string' ? body.detail : "So'rov bajarilmadi. Qayta urinib ko'ring.", response.status);
    }
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("Aloqani tekshiring. So'rov javobi olinmadi.", 0);
  } finally { window.clearTimeout(timeout); }
}
export function useApi() {
  return useCallback(<T,>(path: string, options?: RequestInit) => api<T>(path, options), []);
}
