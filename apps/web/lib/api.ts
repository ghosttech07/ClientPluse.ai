import { createClient } from '@supabase/supabase-js';
export const supabase = process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY, {auth:{flowType:'pkce',detectSessionInUrl:true,persistSession:true,autoRefreshToken:true}}) : null;
export async function headers(): Promise<Record<string,string>> { const token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : null; return token ? { Authorization: `Bearer ${token}` } : {}; }
const pendingReads = new Map<string, Promise<unknown>>();
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const requestHeaders = new Headers(await headers());
  if(init.body && !(init.body instanceof FormData)) requestHeaders.set('Content-Type','application/json');
  new Headers(init.headers).forEach((value,key)=>requestHeaders.set(key,value));
  const canShare = (!init.method || init.method.toUpperCase() === 'GET') && !init.signal && !init.body;
  const key = JSON.stringify([path, Array.from(requestHeaders.entries()), init.cache, init.credentials]);
  if(canShare && pendingReads.has(key)) return pendingReads.get(key) as Promise<T>;
  const request = (async () => {
  const response = await fetch(`/api${path}`, { ...init, headers: requestHeaders });
  if (!response.ok) {
    let message = response.status === 401 ? 'Your session expired. Please sign in again.' : response.status === 429 ? 'Too many requests. Please wait a minute and retry.' : response.status === 504 ? 'The AI request timed out. Please retry shortly.' : response.status >= 500 ? 'The server could not complete the request. Please retry shortly.' : 'Please check the supplied fields.';
    try { const result = await response.json(); if(typeof result.detail === 'string') message=result.detail; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<T>;
  })();
  if(canShare) pendingReads.set(key, request);
  try { return await request; }
  finally { if(canShare && pendingReads.get(key) === request) pendingReads.delete(key); }
}
export async function fileBlob(path: string) { const r = await fetch(`/api${path}`, { headers: await headers() }); if (!r.ok) throw new Error('Unable to open this source. Please sign in again.'); return r.blob(); }
export async function download(path: string, name: string) { const url = URL.createObjectURL(await fileBlob(path)); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
