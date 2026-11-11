const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export type PublicComplaint = { complaint_number: string; department_name: string | null; category_name: string | null; status: string; submission_date: string | null };
export type DepartmentStats = { department_name: string; total_complaints: number; resolved_count: number; open_count: number };
async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail; } catch { /* non-JSON error */ }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
export const getPublicComplaints = () => get<{ total: number; complaints: PublicComplaint[] }>('/api/public/complaints?limit=100');
export const trackComplaint = (id: string) => get<PublicComplaint>(`/api/public/complaints/${encodeURIComponent(id.replace(/^#/, ''))}`);
export const getDepartmentStats = () => get<DepartmentStats[]>('/api/public/department-statistics');
