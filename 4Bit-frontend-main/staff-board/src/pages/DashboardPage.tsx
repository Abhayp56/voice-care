import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Camera, CheckCircle2, Clock3, MapPin, RefreshCw, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { analyzeEvidence, getComplaints, getEvidence, updateStatus, uploadEvidence, verifyEvidence, type ApiComplaint, type ApiEvidence } from '../api';

type Advisory = { status: string; relevance_score: number; summary: string; issues?: string[]; observations?: string[] };
const ageLabel = (n = 0) => `${n} day${n === 1 ? '' : 's'} open`;

export const DashboardPage: React.FC = () => {
  const { currentUser, accessToken } = useAuth();
  const [items, setItems] = useState<ApiComplaint[]>([]);
  const [evidence, setEvidence] = useState<Record<string, ApiEvidence[]>>({});
  const [files, setFiles] = useState<Record<string, File>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [advisories, setAdvisories] = useState<Record<string, Advisory>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const isHigher = currentUser?.role === 'Higher Authority';

  const refresh = useCallback(async () => {
    if (!accessToken) return;
    try {
      const result = await getComplaints(accessToken);
      setItems(result.complaints);
      const needingReview = result.complaints.filter((c) => c.status === 'needs_review');
      const evidenceResults = await Promise.all(needingReview.map(async (c) => [c.complaint_number, await getEvidence(accessToken, c.complaint_number).catch(() => [])] as const));
      setEvidence(Object.fromEntries(evidenceResults));
      setLoadError('');
    } catch (e) { setLoadError(e instanceof Error ? e.message : 'Dashboard data could not be loaded.'); }
    finally { setLoading(false); }
  }, [accessToken]);

  useEffect(() => { void refresh(); const id = window.setInterval(() => void refresh(), 60_000); return () => window.clearInterval(id); }, [refresh]);

  const run = async (id: string, action: () => Promise<void>) => {
    setBusy((x) => ({ ...x, [id]: true })); setErrors((x) => ({ ...x, [id]: '' }));
    try { await action(); await refresh(); }
    catch (e) { setErrors((x) => ({ ...x, [id]: e instanceof Error ? e.message : 'Action failed.' })); }
    finally { setBusy((x) => ({ ...x, [id]: false })); }
  };

  const startWork = (c: ApiComplaint) => run(c.complaint_number, async () => { if (!accessToken) return; await updateStatus(accessToken, c.complaint_number, 'in_progress'); });
  const upload = (c: ApiComplaint) => run(c.complaint_number, async () => {
    const file = files[c.complaint_number]; const note = notes[c.complaint_number]?.trim();
    if (!accessToken || !file || !note) throw new Error('Choose a photo and enter resolution notes first.');
    if (!navigator.geolocation) throw new Error('This browser cannot provide GPS location.');
    const position = await new Promise<GeolocationPosition>((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, () => reject(new Error('Location permission is required to upload resolution evidence.')), { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }));
    await uploadEvidence(accessToken, c.complaint_number, file, note, { latitude: position.coords.latitude, longitude: position.coords.longitude, accuracy: position.coords.accuracy });
    await updateStatus(accessToken, c.complaint_number, 'needs_review', note);
    setFiles((x) => ({ ...x, [c.complaint_number]: undefined as unknown as File }));
  });
  const review = (c: ApiComplaint, e: ApiEvidence) => run(c.complaint_number, async () => {
    if (!accessToken) return;
    const out = await analyzeEvidence(accessToken, e.id); setAdvisories((x) => ({ ...x, [c.complaint_number]: out.result as Advisory }));
  });
  const verify = (c: ApiComplaint, e: ApiEvidence) => run(c.complaint_number, async () => {
    if (!accessToken) return;
    if (!advisories[c.complaint_number]) throw new Error('Run and read the AI advisory before human verification.');
    await verifyEvidence(accessToken, e.id, true, 'Reviewed and approved by authorized dashboard user');
  });
  const publish = (c: ApiComplaint, e: ApiEvidence) => run(c.complaint_number, async () => {
    if (!accessToken || !e.verified_at) throw new Error('Human verification is required before submission.');
    await updateStatus(accessToken, c.complaint_number, 'resolved', 'Resolution photo and GPS reviewed; submitted to public status portal.');
  });

  const labelStatus: Record<string, string> = { received: 'Received', assigned: 'Received', in_progress: 'In progress', needs_review: 'Evidence review', resolved: 'Submitted publicly', closed: 'Submitted publicly', escalated: 'Escalated' };
  return <div className="mx-auto max-w-6xl space-y-6 py-5">
    <header className="rounded-3xl bg-emerald-950 p-6 text-white shadow">
      <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-sm text-emerald-200">VoiceCare operations</p><h1 className="mt-1 text-3xl font-black">{isHigher ? 'Higher Authority Review' : 'Hospital Complaint Dashboard'}</h1><p className="mt-2 text-emerald-100">{currentUser?.role}{currentUser?.department ? ` · ${currentUser.department}` : ''} · complaints refresh every minute</p></div><button onClick={() => void refresh()} className="flex items-center gap-2 rounded-xl border border-emerald-600 px-4 py-2 font-bold"><RefreshCw size={16}/> Refresh</button></div>
      <p className="mt-5 max-w-4xl text-sm text-emerald-100">Department heads see their own department. Hospital administrators see every department. Higher Authority sees only unresolved cases open for 11 days or more.</p>
    </header>
    {loadError && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800">{loadError}</div>}
    {loading && <p className="p-6 text-center">Loading complaints…</p>}
    {!loading && !items.length && <section className="rounded-2xl border bg-white p-12 text-center"><CheckCircle2 className="mx-auto h-12 w-12 text-emerald-700"/><h2 className="mt-3 text-xl font-bold">{isHigher ? 'No cases need higher-authority review' : 'No complaints yet'}</h2><p className="mt-2 text-slate-600">{isHigher ? 'This dashboard will show a case only after it has remained unresolved for 11 days.' : 'New confirmed patient complaints will appear here.'}</p></section>}
    <div className="grid gap-4">{items.map((c) => {
      const age = c.days_open || 0; const currentEvidence = evidence[c.complaint_number]?.[0]; const advisory = advisories[c.complaint_number]; const older = age >= 11;
      return <article key={c.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-mono text-sm font-bold text-emerald-800">{c.complaint_number}</p><h2 className="mt-1 text-xl font-bold text-slate-950">{c.category_name || 'Hospital complaint'} · {c.department_name || 'Unassigned department'}</h2><p className="mt-2 whitespace-pre-wrap text-slate-700">{c.description}</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold">{labelStatus[c.status] || c.status}</span></div>
        <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-600"><span className="flex items-center gap-1"><Clock3 size={15}/>{ageLabel(age)}</span><span>Priority: {c.priority}</span></div>
        {c.warning_level === 1 && <div className="mt-4 flex gap-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-amber-950"><AlertTriangle size={18}/><span><b>First warning</b> · unresolved for 7 days</span></div>}
        {c.warning_level === 2 && <div className="mt-4 flex gap-2 rounded-xl border border-orange-400 bg-orange-50 p-3 text-orange-950"><AlertTriangle size={18}/><span><b>Second warning</b> · unresolved for 9 days</span></div>}
        {older && <div className="mt-4 rounded-xl border border-red-300 bg-red-50 p-3 font-semibold text-red-900">Higher Authority review required · no third warning is issued.</div>}
        <div className="mt-5 flex flex-wrap gap-3">
          {!['in_progress','needs_review','resolved','closed'].includes(c.status) && (!isHigher || older) && <button disabled={busy[c.complaint_number]} onClick={() => void startWork(c)} className="rounded-xl bg-emerald-900 px-4 py-2 font-bold text-white disabled:opacity-50">Start resolving / visit</button>}
          {['received','assigned','in_progress','escalated'].includes(c.status) && (!isHigher || older) && <div className="w-full space-y-3 rounded-xl bg-slate-50 p-4"><label className="block text-sm font-bold">Take/select a clear photo of the repaired issue<input className="mt-2 block w-full" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={(ev) => { const f = ev.target.files?.[0]; if (f) setFiles((x) => ({ ...x, [c.complaint_number]: f })); }}/></label><label className="block text-sm font-bold">Resolution notes<textarea className="mt-1 block w-full rounded-lg border p-2 font-normal" rows={2} value={notes[c.complaint_number] || ''} onChange={(ev) => setNotes((x) => ({ ...x, [c.complaint_number]: ev.target.value }))}/></label><p className="flex items-start gap-2 text-xs text-slate-600"><MapPin size={15}/>Browser GPS is captured at upload. It is a coordinate snapshot, not proof of where or when the photo was taken.</p><button disabled={busy[c.complaint_number]} onClick={() => void upload(c)} className="rounded-xl bg-emerald-900 px-4 py-2 font-bold text-white disabled:opacity-50"><Camera className="mr-2 inline" size={16}/>Upload photo + GPS</button></div>}
          {currentEvidence && <div className="w-full space-y-3 rounded-xl border border-blue-200 bg-blue-50 p-4"><h3 className="font-bold">Resolution evidence for {c.complaint_number}</h3>{currentEvidence.signed_url && <img className="max-h-80 rounded-lg" src={currentEvidence.signed_url} alt="Submitted resolution evidence"/>}<p className="text-sm">{currentEvidence.notes}</p>{currentEvidence.gps_latitude != null && <p className="text-xs text-slate-700">GPS snapshot: {currentEvidence.gps_latitude.toFixed(5)}, {currentEvidence.gps_longitude?.toFixed(5)} · accuracy {Math.round(currentEvidence.gps_accuracy_m || 0)} m</p>}
            {!advisory && <button disabled={busy[c.complaint_number]} onClick={() => void review(c,currentEvidence)} className="rounded-xl border border-emerald-800 px-4 py-2 font-bold text-emerald-950"><ShieldCheck className="mr-2 inline" size={16}/>Run AI evidence review</button>}
            {advisory && <div className="rounded-lg bg-white p-3 text-sm"><b>AI advisory:</b> {advisory.status.replace(/_/g,' ')} · {Math.round(advisory.relevance_score*100)}% relevance<p className="mt-1">{advisory.summary}</p>{advisory.issues?.length ? <p className="mt-1 text-amber-800">{advisory.issues.join(' ')}</p> : null}</div>}
            {advisory && !currentEvidence.verified_at && <button disabled={busy[c.complaint_number]} onClick={() => void verify(c,currentEvidence)} className="rounded-xl border border-emerald-800 px-4 py-2 font-bold text-emerald-950">I reviewed this evidence · verify</button>}
            {currentEvidence.verified_at && <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-emerald-800">Evidence verified</span><button disabled={busy[c.complaint_number] || (older && !isHigher) || (!older && isHigher)} onClick={() => void publish(c,currentEvidence)} className="rounded-xl bg-emerald-900 px-4 py-2 font-bold text-white disabled:opacity-40">{older ? 'Higher Authority: Submit to public website' : 'Submit resolution to public website'}</button></div>}
          </div>}
        </div>
        {errors[c.complaint_number] && <p role="alert" className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{errors[c.complaint_number]}</p>}
      </article>;
    })}</div>
  </div>;
};
export default DashboardPage;
