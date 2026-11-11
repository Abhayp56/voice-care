import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Info, Sparkles } from 'lucide-react';
import { Complaint, EvidenceData } from '../../types/complaint';
import { useAuth } from '../../context/AuthContext';
import { analyzeEvidence } from '../../api';

type Assessment = { status: string; relevance_score: number; quality: string; issues: string[]; observations: string[]; summary: string; requires_human_review: true };

export const AiEvidenceAssessment: React.FC<{ complaint: Complaint; evidence: EvidenceData }> = ({ complaint, evidence }) => {
  const { accessToken } = useAuth();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const requestedEvidence = useRef<string | null>(null);
  const runAssessment = useCallback(async () => {
    if (!accessToken || !evidence.id) return;
    setBusy(true); setError('');
    try { const result = await analyzeEvidence(accessToken, evidence.id); setAssessment(result.result as Assessment); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'AI advisory is unavailable.'); }
    finally { setBusy(false); }
  }, [accessToken, evidence.id]);

  useEffect(() => {
    if (!evidence.id || requestedEvidence.current === evidence.id) return;
    requestedEvidence.current = evidence.id;
    void runAssessment();
  }, [evidence.id, runAssessment]);

  return <section aria-label="AI Evidence Assessment" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 space-y-3">
    <div className="flex items-center gap-2 font-bold text-emerald-950"><Sparkles className="w-5 h-5" /> Evidence review advisory</div>
    <p className="text-sm text-slate-700">AI can assess whether this photo appears relevant. It cannot confirm authenticity or close the complaint; an authorized human makes the final decision.</p>
    {busy && <p className="text-sm text-slate-700">AI is reviewing whether the submitted photo appears relevant…</p>}
    {!assessment && !busy && <button type="button" onClick={() => void runAssessment()} disabled={!evidence.id} className="px-4 py-2 rounded-xl bg-emerald-900 text-white font-bold disabled:opacity-50">Retry AI review</button>}
    {error && <p role="alert" className="text-sm text-rose-700">{error}</p>}
    {assessment && <div className="rounded-xl bg-white border border-emerald-100 p-4 space-y-2">
      <div className="font-bold text-slate-900">{assessment.status.replace(/_/g, ' ')} · {Math.round(assessment.relevance_score * 100)}% relevance score</div>
      <p className="text-sm text-slate-700">{assessment.summary}</p>
      {assessment.quality && <p className="text-xs text-slate-600">Image quality: {assessment.quality}</p>}
      {assessment.observations?.length > 0 && <ul className="list-disc pl-5 text-sm text-slate-700">{assessment.observations.map((item, index) => <li key={index}>{item}</li>)}</ul>}
      {assessment.issues?.length > 0 && <ul className="list-disc pl-5 text-sm text-amber-800">{assessment.issues.map((item, index) => <li key={index}>{item}</li>)}</ul>}
      <div className="flex items-start gap-2 text-xs text-amber-900"><Info className="w-4 h-4 shrink-0" />Human review is required.</div>
    </div>}
    <p className="text-xs text-slate-500">For complaint {complaint.id}</p>
  </section>;
};

export default AiEvidenceAssessment;
