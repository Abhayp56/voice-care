import React, { useState } from 'react';
import { Camera, X } from 'lucide-react';
import { Complaint } from '../../types/complaint';

interface UploadEvidenceModalProps {
  complaint: Complaint;
  isOpen: boolean;
  onClose: () => void;
  onSubmitEvidence: (complaintId: string, file: File, notes: string) => Promise<void>;
}

export const UploadEvidenceModal: React.FC<UploadEvidenceModalProps> = ({ complaint, isOpen, onClose, onSubmitEvidence }) => {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (!isOpen) return null;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('');
    if (!file) { setError('Choose a real JPEG, PNG, or WebP resolution photo.'); return; }
    if (file.size > 5 * 1024 * 1024) { setError('Evidence photos must be 5 MB or smaller.'); return; }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { setError('Only JPEG, PNG, and WebP photos are accepted.'); return; }
    if (notes.trim().length < 5) { setError('Enter a resolution note of at least 5 characters.'); return; }
    setBusy(true);
    try { await onSubmitEvidence(complaint.id, file, notes.trim()); setFile(null); setNotes(''); onClose(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Evidence upload failed.'); }
    finally { setBusy(false); }
  };

  return <div role="dialog" aria-modal="true" aria-labelledby="evidence-title" className="fixed inset-0 z-50 bg-slate-900/75 flex items-center justify-center p-4">
    <form onSubmit={submit} className="bg-white rounded-3xl max-w-xl w-full shadow-2xl overflow-hidden">
      <div className="flex items-center justify-between bg-emerald-950 text-white p-5">
        <div><h2 id="evidence-title" className="font-black text-lg">Submit resolution evidence</h2><p className="text-sm text-emerald-100">{complaint.id} · {complaint.assignedDepartment}</p></div>
        <button type="button" onClick={onClose} aria-label="Close" className="p-2 rounded-lg hover:bg-white/10"><X /></button>
      </div>
      <div className="p-6 space-y-4">
        <label className="block text-sm font-bold text-slate-700">Photo evidence (JPEG, PNG or WebP; up to 5 MB)
          <input className="block w-full mt-2 text-sm" type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </label>
        {file && <p className="text-sm text-slate-600 flex items-center gap-2"><Camera className="w-4 h-4" />{file.name} ({Math.ceil(file.size / 1024)} KB)</p>}
        <label className="block text-sm font-bold text-slate-700">What was done to resolve this complaint?
          <textarea className="block w-full mt-2 border rounded-xl p-3 text-sm" rows={4} minLength={5} maxLength={1000} value={notes} onChange={(e) => setNotes(e.target.value)} required />
        </label>
        {error && <p role="alert" className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-3">{error}</p>}
      </div>
      <div className="p-5 border-t flex justify-end gap-3">
        <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl border font-bold">Cancel</button>
        <button disabled={busy} className="px-5 py-2 rounded-xl bg-emerald-900 text-white font-bold disabled:opacity-50">{busy ? 'Uploading…' : 'Upload evidence'}</button>
      </div>
    </form>
  </div>;
};
