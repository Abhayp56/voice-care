const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '');
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || '';

export type StaffProfile = { id: string; email?: string; full_name: string; role: string; department_id?: string | null; department_name?: string | null };
export type ApiComplaint = {
  id: string; complaint_number: string; patient_name?: string | null; patient_phone?: string | null;
  description: string; language: string; category_id: string; department_id: string; priority: string;
  status: string; assigned_to?: string | null; assigned_to_name?: string | null; department_name?: string | null;
  category_name?: string | null; created_at: string; updated_at: string;
  days_open?: number; warning_level?: number; escalation_stage?: string; higher_authority_review?: boolean;
};
export type ApiEvidence = { id: string; complaint_id: string; file_path: string; file_type: string; notes?: string; submitted_by?: string; submitted_by_name?: string; created_at: string; verified_at?: string | null; signed_url?: string | null; gps_latitude?: number | null; gps_longitude?: number | null; gps_accuracy_m?: number | null };

async function backendFetch(input: RequestInfo | URL, init?: RequestInit) {
  try {
    return await fetch(input, init);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach the VoiceCare backend at ${API_BASE}. Start the backend and keep its terminal running.`);
    }
    throw error;
  }
}

export async function api<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);
  if (init?.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await backendFetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail; } catch { /* non-JSON error */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function signIn(email: string, password: string) {
  if (!SUPABASE_URL || !SUPABASE_KEY) throw new Error('Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in staff-board/.env.');
  const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', apikey: SUPABASE_KEY },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    if (response.status === 400 || response.status === 401) throw new Error('Email or password is incorrect.');
    throw new Error(`Supabase sign-in failed (${response.status}).`);
  }
  return response.json() as Promise<{ access_token: string; refresh_token: string; expires_in: number; user: { id: string; email?: string } }>;
}

export const getMyProfile = (token: string) => api<StaffProfile>('/api/auth/me', token);
export const getComplaints = (token: string) => api<{ complaints: ApiComplaint[] }>('/api/complaints?limit=100', token);
export const getDepartments = () => backendFetch(`${API_BASE}/api/departments`).then(async (r) => {
  if (!r.ok) throw new Error(`Unable to load departments (${r.status}).`);
  return r.json() as Promise<Array<{ id: string; name: string }>>;
});
export const updateStatus = (token: string, id: string, status: string, note?: string) =>
  api<ApiComplaint>(`/api/complaints/${encodeURIComponent(id)}/status`, token, { method: 'PATCH', body: JSON.stringify({ status, note }) });
export const uploadEvidence = (token: string, id: string, file: File, notes: string, gps: { latitude: number; longitude: number; accuracy: number }) => {
  const form = new FormData(); form.append('file', file); form.append('notes', notes); form.append('gps_latitude', String(gps.latitude)); form.append('gps_longitude', String(gps.longitude)); form.append('gps_accuracy_m', String(gps.accuracy));
  return api<ApiEvidence>(`/api/complaints/${encodeURIComponent(id)}/evidence`, token, { method: 'POST', body: form });
};
export const getEvidence = (token: string, id: string) => api<ApiEvidence[]>(`/api/complaints/${encodeURIComponent(id)}/evidence`, token);
export const analyzeEvidence = (token: string, evidenceId: string) => api<{ result: unknown; requires_human_review: boolean }>(`/api/evidence/${encodeURIComponent(evidenceId)}/analyze`, token, { method: 'POST' });
export const verifyEvidence = (token: string, evidenceId: string, verified: boolean, notes?: string) =>
  api<ApiEvidence>(`/api/evidence/${encodeURIComponent(evidenceId)}/verify`, token, { method: 'POST', body: JSON.stringify({ verified, notes }) });
