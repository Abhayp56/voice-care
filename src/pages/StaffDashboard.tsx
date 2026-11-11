import React, { useState } from 'react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
type CaseItem = { id: string; complaint_number: string; category_name?: string; department_name?: string; status: string; priority: string; description: string };
type EvidenceResult = { id: string; complaint_id: string; file_path: string };

export default function StaffDashboard() {
  const [token, setToken] = useState('');
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [lifecycle, setLifecycle] = useState<Record<string, string>>({});
  const [evidenceFiles, setEvidenceFiles] = useState<Record<string, File>>({});
  const [evidenceByComplaint, setEvidenceByComplaint] = useState<Record<string, EvidenceResult>>({});
  const [analysisByComplaint, setAnalysisByComplaint] = useState<Record<string, unknown>>({});
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = async (event: React.FormEvent) => {
    event.preventDefault(); setError(''); setBusy(true); setCases([]); setStats(null);
    try {
      const headers = { Authorization: `Bearer ${token.trim()}` };
      const [statsResponse, caseResponse] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/stats`, { headers }),
        fetch(`${API_BASE}/api/complaints?limit=50`, { headers }),
      ]);
      const [statsData, caseData] = await Promise.all([statsResponse.json(), caseResponse.json()]);
      if (!statsResponse.ok) throw new Error(statsData.detail || `Dashboard request failed (${statsResponse.status})`);
      if (!caseResponse.ok) throw new Error(caseData.detail || `Complaint request failed (${caseResponse.status})`);
      setStats(statsData); setCases(caseData.complaints || []);
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not load staff data.'); }
    finally { setBusy(false); }
  };
  const updateStatus = async (item: CaseItem, status: string) => {
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(item.id)}/status`, {
        method: 'PATCH', headers: { Authorization: `Bearer ${token.trim()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Status update failed (${response.status})`);
      setCases((current) => current.map((row) => row.id === item.id ? { ...row, status: data.status } : row));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not update status.'); }
  };
  const loadLifecycle = async (item: CaseItem) => {
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(item.id)}/lifecycle`, { headers: { Authorization: `Bearer ${token.trim()}` } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Lifecycle information is unavailable.');
      const deadline = data.lifecycle?.resolution_due_at ? new Date(data.lifecycle.resolution_due_at).toLocaleString() : 'SLA policy not configured';
      setLifecycle((current) => ({ ...current, [item.id]: deadline }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not load lifecycle information.'); }
  };
  const uploadEvidence = async (item: CaseItem) => {
    const file = evidenceFiles[item.id];
    if (!file) return;
    setError('');
    try {
      const form = new FormData(); form.append('file', file); form.append('notes', reviewNotes[item.id] || '');
      const response = await fetch(`${API_BASE}/api/complaints/${encodeURIComponent(item.id)}/evidence`, { method: 'POST', headers: { Authorization: `Bearer ${token.trim()}` }, body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Evidence upload failed (${response.status})`);
      setEvidenceByComplaint((current) => ({ ...current, [item.id]: data }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not upload evidence.'); }
  };
  const analyzeEvidence = async (item: CaseItem) => {
    const evidence = evidenceByComplaint[item.id]; if (!evidence) return;
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/evidence/${encodeURIComponent(evidence.id)}/analyze`, { method: 'POST', headers: { Authorization: `Bearer ${token.trim()}` } });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Evidence analysis failed (${response.status})`);
      setAnalysisByComplaint((current) => ({ ...current, [item.id]: data.result }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not analyze evidence.'); }
  };
  const reviewEvidence = async (item: CaseItem, verified: boolean) => {
    const evidence = evidenceByComplaint[item.id]; if (!evidence) return;
    setError('');
    try {
      const response = await fetch(`${API_BASE}/api/evidence/${encodeURIComponent(evidence.id)}/verify`, {
        method: 'POST', headers: { Authorization: `Bearer ${token.trim()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ verified, notes: reviewNotes[item.id] || '' }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Human review failed (${response.status})`);
      setEvidenceByComplaint((current) => ({ ...current, [item.id]: data }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not save human review.'); }
  };
  return <main className="mx-auto max-w-6xl space-y-6 p-5 pt-24 sm:p-8"><h1 className="text-3xl font-bold text-emerald-950">Staff and authority dashboard</h1><p>The backend applies the signed-in profile’s role and department permissions. Your token stays in this page and is not saved.</p>
    <form onSubmit={load} className="flex flex-col gap-3 sm:flex-row"><label className="sr-only" htmlFor="staff-token">Supabase access token</label><input id="staff-token" type="password" autoComplete="off" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste Supabase access token" className="flex-1 rounded border p-3"/><button disabled={busy || !token.trim()} className="rounded bg-emerald-900 px-5 py-3 font-semibold text-white disabled:opacity-50">{busy ? 'Loading…' : 'Load dashboard'}</button></form>
    {error && <p role="alert" className="rounded bg-red-50 p-3 text-red-800">{error}</p>}
    {stats && <section className="rounded-xl border bg-white p-4"><h2 className="mb-2 text-xl font-bold">Operational statistics</h2><pre className="overflow-auto text-sm">{JSON.stringify(stats, null, 2)}</pre></section>}
    <section className="space-y-3"><h2 className="text-xl font-bold">Complaints</h2>{cases.map((item) => <article key={item.id} className="space-y-3 rounded-xl border bg-white p-4"><div className="flex flex-wrap justify-between gap-2"><strong>{item.complaint_number}</strong><span>{item.status} · {item.priority}</span></div><p className="font-semibold">{item.category_name || 'Category'} · {item.department_name || 'Department'}</p><p>{item.description}</p>
      <label className="block text-sm font-semibold" htmlFor={`status-${item.id}`}>Update status (permissions are enforced by the backend)</label><select id={`status-${item.id}`} value={item.status} onChange={(event) => void updateStatus(item, event.target.value)} className="rounded border p-2"><option value={item.status}>{item.status}</option>{['in_progress', 'needs_review', 'resolved', 'escalated', 'closed'].filter((status) => status !== item.status).map((status) => <option key={status} value={status}>{status}</option>)}</select>
      <div><button onClick={() => void loadLifecycle(item)} className="rounded border px-3 py-2 text-sm font-semibold">View lifecycle and SLA</button>{lifecycle[item.id] && <p className="mt-2 text-sm">Resolution deadline: {lifecycle[item.id]}</p>}</div>
      <div className="space-y-2 border-t pt-3"><h3 className="font-semibold">Resolution evidence</h3><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const file = event.target.files?.[0]; if (file) setEvidenceFiles((current) => ({ ...current, [item.id]: file })); }} /><textarea value={reviewNotes[item.id] || ''} onChange={(event) => setReviewNotes((current) => ({ ...current, [item.id]: event.target.value }))} maxLength={2000} placeholder="Resolution note" className="block w-full rounded border p-2"/><button onClick={() => void uploadEvidence(item)} disabled={!evidenceFiles[item.id]} className="rounded border px-3 py-2 text-sm disabled:opacity-50">Upload evidence</button>
        {evidenceByComplaint[item.id] && <div className="flex flex-wrap gap-2"><button onClick={() => void analyzeEvidence(item)} className="rounded border px-3 py-2 text-sm">AI evidence advice</button><button onClick={() => void reviewEvidence(item, true)} className="rounded bg-emerald-800 px-3 py-2 text-sm text-white">Human approve</button><button onClick={() => void reviewEvidence(item, false)} className="rounded bg-red-700 px-3 py-2 text-sm text-white">Human reject</button></div>}
        {analysisByComplaint[item.id] && <pre className="overflow-auto rounded bg-slate-50 p-3 text-xs">{JSON.stringify(analysisByComplaint[item.id], null, 2)}</pre>}
      </div></article>)}</section>
  </main>;
}
