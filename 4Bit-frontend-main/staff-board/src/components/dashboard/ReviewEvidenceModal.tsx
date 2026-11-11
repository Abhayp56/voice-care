import React, { useState } from 'react';
import {
  X,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  AlertTriangle,
  ZoomIn,
  Shield,
  RotateCcw,
} from 'lucide-react';
import { Complaint } from '../../types/complaint';
import { Button } from '../common/Button';
import { StatusBadge } from '../common/StatusBadge';
import { AiEvidenceAssessment } from './AiEvidenceAssessment';

interface ReviewEvidenceModalProps {
  complaint: Complaint;
  isOpen: boolean;
  onClose: () => void;
  onApproveResolve: (complaintId: string) => void;
  onRejectReopen: (complaintId: string, reason: string) => void;
}

const REWORK_PRESETS = [
  'The photo is unclear; please upload a clearer image.',
  'The reported issue is still visible; please complete the repair.',
  'The photo does not show the reported area; please upload relevant evidence.',
];

export const ReviewEvidenceModal: React.FC<ReviewEvidenceModalProps> = ({
  complaint,
  isOpen,
  onClose,
  onApproveResolve,
  onRejectReopen,
}) => {
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isImageExpanded, setIsImageExpanded] = useState(false);

  if (!isOpen || !complaint.evidence) return null;

  const { evidence } = complaint;
  const wardDisplay = complaint.ward || complaint.wardArea || 'Location not provided';

  const handleApprove = () => {
    setIsProcessing(true);
    void Promise.resolve(onApproveResolve(complaint.id)).then(onClose).catch((error) => { alert(error instanceof Error ? error.message : 'Could not approve evidence.'); }).finally(() => setIsProcessing(false));
  };

  const handleReject = () => {
    if (!rejectReason.trim()) {
      alert('Please specify why this evidence is being rejected before sending back for rework.');
      return;
    }
    setIsProcessing(true);
    void Promise.resolve(onRejectReopen(complaint.id, rejectReason.trim())).then(onClose).catch((error) => { alert(error instanceof Error ? error.message : 'Could not request rework.'); }).finally(() => setIsProcessing(false));
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-evidence-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/75 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6"
    >
      <div className="bg-white rounded-3xl max-w-4xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-fade-in my-auto max-h-[94vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-navy-950 via-slate-900 to-hospital-950 text-white p-6 flex items-center justify-between shrink-0">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-white/20 text-xs font-mono font-bold tracking-wider">
                {complaint.id}
              </span>
              <span className="text-xs text-hospital-300 font-bold uppercase tracking-wider flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-amber-400" />
                Administrative Oversight & Human Review Gate
              </span>
            </div>
            <h2 id="review-evidence-title" className="text-xl sm:text-2xl font-black">
              Review Resolution Evidence
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 font-medium">
              Ward: {wardDisplay} • Department: {complaint.assignedDepartment}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 text-white transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white shrink-0 cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div className="p-6 sm:p-8 space-y-6 overflow-y-auto flex-1">
          {/* 1. Grievance Context */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">
                Patient Voice Grievance Details
              </span>
              <StatusBadge status={complaint.status} size="sm" showDot={true} />
            </div>
            <p className="text-base font-extrabold text-slate-900 leading-snug">
              "{complaint.summary}"
            </p>
            {complaint.transcript && (
              <p className="text-xs text-slate-600 italic bg-white p-2.5 rounded-xl border border-slate-200">
                Patient Voice Audio Transcript ({complaint.language}): "{complaint.transcript}"
              </p>
            )}
          </div>

          {/* 2. Distinct AI Multimodal Evidence Assessment Component */}
          <AiEvidenceAssessment complaint={complaint} evidence={evidence} />

          {/* 3. Staff Photographic Proof & Telemetry Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            {/* Left: Photographic Proof */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase text-slate-600 tracking-wider">
                  Submitted Photo Proof:
                </span>
                <span className="text-[11px] text-slate-400 font-medium">
                  {isImageExpanded ? 'Click to shrink' : 'Click to inspect full view'}
                </span>
              </div>

              <div
                onClick={() => setIsImageExpanded(!isImageExpanded)}
                className="relative rounded-2xl overflow-hidden border-2 border-slate-300 shadow-md group cursor-pointer bg-slate-950 transition-all"
              >
                <img
                  src={evidence.imageUrl}
                  alt={evidence.imageCaption}
                  className={`w-full object-cover group-hover:scale-102 transition-transform duration-300 ${
                    isImageExpanded ? 'h-96' : 'h-64'
                  }`}
                />
                <div className="absolute inset-0 bg-black/25 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white font-bold text-sm gap-2">
                  <ZoomIn className="w-5 h-5" />
                  <span>{isImageExpanded ? 'Click to shrink' : 'Click to expand'}</span>
                </div>
                <div className="absolute bottom-2 left-2 right-2 bg-black/80 backdrop-blur-sm text-white p-2.5 rounded-xl text-xs space-y-0.5">
                  <p className="font-bold truncate">{evidence.imageCaption}</p>
                  <p className="text-[10px] text-emerald-400 font-mono">
                    Stored in private hospital evidence storage
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Staff Notes & Telemetry */}
            <div className="space-y-4">
              <div className="space-y-1.5">
                <span className="text-xs font-black uppercase text-slate-600 tracking-wider">
                  Staff Corrective Action Note:
                </span>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-semibold text-slate-900 leading-relaxed min-h-[90px]">
                  "{evidence.resolutionNote}"
                </div>
              </div>

              {/* Submitter and recorded timestamp */}
              <div className="p-4 rounded-2xl bg-slate-100/90 border border-slate-200 space-y-2.5 text-xs">
                <div className="flex items-center gap-2 text-slate-900 font-bold">
                  <User className="w-4 h-4 text-hospital-600 shrink-0" />
                  <span className="truncate">
                    Submitted by: <strong>{evidence.staffName || 'Hospital staff'}</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2 text-slate-700 font-mono">
                  <Clock className="w-4 h-4 text-slate-500 shrink-0" />
                  <span className="truncate">
                    Uploaded: <strong>{evidence.submittedAt}</strong>
                  </span>
                </div>

              </div>
            </div>
          </div>

          {/* 4. Rework & Rejection Drawer (Visible when authority requests rework) */}
          {showRejectInput && (
            <div className="p-5 rounded-3xl bg-rose-50 border-2 border-rose-300 space-y-3.5 animate-fade-in shadow-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-black text-rose-950">
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                  <span>Tell staff what needs to be corrected. The complaint will return to in-progress work.</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowRejectInput(false)}
                  className="text-xs font-bold text-rose-700 hover:underline cursor-pointer"
                >
                  Cancel
                </button>
              </div>

              {/* Rework Reason Presets */}
              <div className="flex flex-wrap gap-1.5">
                {REWORK_PRESETS.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setRejectReason(preset)}
                    className="text-[11px] font-semibold bg-white border border-rose-200 text-rose-900 hover:bg-rose-100/70 px-2.5 py-1 rounded-lg transition cursor-pointer"
                  >
                    {preset}
                  </button>
                ))}
              </div>

              <textarea
                rows={2}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Explain what rectification is required before resolution can be accepted..."
                className="w-full rounded-2xl border-2 border-rose-300 p-3.5 text-sm text-slate-900 focus:outline-none focus:ring-4 focus:ring-rose-500/20 bg-white"
              />

              <div className="flex items-center justify-end gap-2.5 pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRejectInput(false)}
                >
                  Dismiss
                </Button>
                <Button
                  variant="danger"
                  size="md"
                  onClick={handleReject}
                  isLoading={isProcessing}
                  leftIcon={<RotateCcw className="w-4 h-4" />}
                  className="font-black shadow-md shadow-rose-900/20"
                >
                  Confirm Rejection & Request Rework
                </Button>
              </div>
            </div>
          )}

          {/* 5. Massive Primary Authority Decision Buttons */}
          <div className="pt-6 border-t border-slate-200 space-y-4 shrink-0">
            <div className="text-center space-y-1">
              <span className="text-xs font-black uppercase text-slate-600 tracking-wider">
                Human Authority Final Determination
              </span>
              <p className="text-xs text-slate-500 font-medium max-w-lg mx-auto">
                  The AI result is advisory. An authorized reviewer records the human decision.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              {/* Massive Primary "Approve Resolution" Button */}
              <Button
                variant="success"
                size="xl"
                onClick={handleApprove}
                isLoading={isProcessing}
                leftIcon={<CheckCircle2 className="w-8 h-8 text-emerald-200" />}
                className="h-20 text-xl font-bold shadow-sm active:scale-[0.98] cursor-pointer bg-emerald-900 hover:bg-emerald-800 text-stone-50 rounded-2xl flex items-center justify-center gap-3 transition-colors duration-300 border border-emerald-900"
              >
                <div className="text-left">
                  <div className="leading-tight">Approve Resolution</div>
                  <div className="text-xs text-emerald-200 font-normal">
                    Officially close ticket &amp; confirm rectification
                  </div>
                </div>
              </Button>

              {/* Massive Primary "Reject (Request Rework)" Button */}
              <Button
                variant="danger"
                size="xl"
                onClick={() => {
                  if (!showRejectInput) {
                    setShowRejectInput(true);
                  } else {
                    handleReject();
                  }
                }}
                isLoading={isProcessing}
                leftIcon={<XCircle className="w-8 h-8 text-rose-200" />}
                className="h-20 text-xl font-bold shadow-sm active:scale-[0.98] cursor-pointer bg-rose-900 hover:bg-rose-800 text-stone-50 rounded-2xl flex items-center justify-center gap-3 transition-colors duration-300 border border-rose-900"
              >
                <div className="text-left">
                  <div className="leading-tight">Reject (Request Rework)</div>
                  <div className="text-xs text-rose-200 font-normal">
                    Reopen ticket &amp; return to ward staff
                  </div>
                </div>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewEvidenceModal;
