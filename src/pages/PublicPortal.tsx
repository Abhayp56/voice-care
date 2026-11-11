import React, { useEffect, useState } from 'react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
type PublicCase = { complaint_number: string; department_name?: string | null; category_name?: string | null; status: string; submission_date?: string | null };

export default function PublicPortal() {
  const [cases, setCases] = useState<PublicCase[]>([]);
  const [departmentStats, setDepartmentStats] = useState<Record<string, unknown>[]>([]);
  const [tracking, setTracking] = useState('');
  const [result, setResult] = useState<PublicCase | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/public/complaints?limit=25`).then(async (response) => { const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Public status is unavailable.'); return data; }),
      fetch(`${API_BASE}/api/public/department-statistics`).then(async (response) => { const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Department statistics are unavailable.'); return data; }),
    ]).then(([publicData, stats]) => { setCases(publicData.complaints || []); setDepartmentStats(Array.isArray(stats) ? stats : []); })
      .catch((err) => setError(err instanceof Error ? err.message : 'Public status is unavailable.'));
  }, []);
  const track = async (event: React.FormEvent) => {
    event.preventDefault(); setError(''); setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/public/complaints/${encodeURIComponent(tracking.trim())}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Complaint not found.');
      setResult(data);
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not look up that number.'); }
  };
  return <main className="mx-auto max-w-5xl space-y-6 p-5 pt-24 sm:p-8"><h1 className="text-3xl font-bold text-emerald-950">Public transparency</h1><p>Only privacy-safe complaint status fields are shown here.</p>
    <form onSubmit={track} className="flex flex-col gap-3 sm:flex-row"><label className="sr-only" htmlFor="tracking-id">Complaint reference</label><input id="tracking-id" value={tracking} onChange={(e) => setTracking(e.target.value)} placeholder="VC-YYYY-0001" className="flex-1 rounded border p-3"/><button className="rounded bg-emerald-900 px-5 py-3 font-semibold text-white">Check status</button></form>
    {result && <article className="rounded-xl border bg-white p-4"><strong>{result.complaint_number}</strong> · {result.status}<p>{result.category_name || 'Category pending'} · {result.department_name || 'Department pending'}</p></article>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <section className="space-y-3"><h2 className="text-xl font-bold">Recent public records</h2>{cases.map((item) => <article key={item.complaint_number} className="rounded-xl border bg-white p-4"><strong>{item.complaint_number}</strong><p>{item.category_name || 'Category'} · {item.department_name || 'Department'} · {item.status}</p></article>)}{!cases.length && !error && <p>No public records were returned.</p>}</section>
    <section className="space-y-3"><h2 className="text-xl font-bold">Department statistics</h2>{departmentStats.map((item, index) => <article key={String(item.department_id || item.department_name || index)} className="rounded-xl border bg-white p-4"><pre className="overflow-auto text-sm">{JSON.stringify(item, null, 2)}</pre></article>)}</section>
  </main>;
}
