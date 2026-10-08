import { createClient } from '@supabase/supabase-js';
export const supabase = process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY, {auth:{flowType:'pkce',detectSessionInUrl:true,persistSession:true,autoRefreshToken:true}}) : null;
export type Evidence = { id: string; file_id: string; file_name: string; modality: string; content: string; page?: number; timestamp?: number; event_time?: string; row?: number; extraction?: string };
export type EvidenceFile = { id: string; name: string; mime: string; size: number; status: string; error?: string; meta: { pages?: number; rows?: number; columns?: string[]; statistics?: Record<string, { min?: number; max?: number; mean?: number; missing?: number }>; chart_data?: Record<string,string>[]; limitations?: string[]; extraction?: string }; created_at: string };
export type Workspace = { id: string; name: string; description: string; industry: string; created_at: string; file_count?: number; ready_count?: number; processing_count?: number; files?: EvidenceFile[]; segments?: Evidence[] };
export type Message = { id: string; role: string; content: string; citations: Evidence[]; analysis: Record<string, unknown>; created_at: string };
export async function headers(): Promise<Record<string,string>> { const token = supabase ? (await supabase.auth.getSession()).data.session?.access_token : null; return token ? { Authorization: `Bearer ${token}` } : {}; }
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const requestHeaders = new Headers(await headers());
  if(init.body && !(init.body instanceof FormData)) requestHeaders.set('Content-Type','application/json');
  new Headers(init.headers).forEach((value,key)=>requestHeaders.set(key,value));
  const response = await fetch(`/api${path}`, { ...init, headers: requestHeaders });
  if (!response.ok) {
    let message = response.status === 401 ? 'Your session expired. Please sign in again.' : response.status === 429 ? 'Too many requests. Please wait a minute and retry.' : response.status === 504 ? 'The AI request timed out. Please retry shortly.' : response.status >= 500 ? 'The server could not complete the request. Please retry shortly.' : 'Please check the supplied fields.';
    try { const result = await response.json(); if(typeof result.detail === 'string') message=result.detail; } catch {}
    throw new Error(message);
  }
  return response.json();
}
export async function fileBlob(path: string) { const r = await fetch(`/api${path}`, { headers: await headers() }); if (!r.ok) throw new Error('Unable to open this source. Please sign in again.'); return r.blob(); }
export async function download(path: string, name: string) { const url = URL.createObjectURL(await fileBlob(path)); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
export const industries = [
  { name: 'Manufacturing', eyebrow: 'OPERATIONAL INTELLIGENCE', description: 'Find the story behind equipment failures. Connect sensor trends, maintenance records, and visual evidence.', color: '#6998ff', icon: 'factory', question: 'What evidence may explain why Machine A stopped?' },
  { name: 'Education', eyebrow: 'LEARNING INTELLIGENCE', description: 'Turn lectures, textbooks, and handwritten notes into a connected learning experience.', color: '#b29aff', icon: 'education', question: 'Summarize the key concepts in my study material.' },
  { name: 'Insurance', eyebrow: 'CLAIMS INTELLIGENCE', description: 'Bring clarity to every claim. Review photographs, statements, and policy documents together.', color: '#5ce0b7', icon: 'insurance', question: 'Does the evidence support the described vehicle damage?' },
  { name: 'E-commerce', eyebrow: 'DELIVERY INTELLIGENCE', description: 'Trace an incident from warehouse to doorstep with connected, source-backed evidence.', color: '#ffb77c', icon: 'commerce', question: 'What may have caused the laptop damage?' },
];

