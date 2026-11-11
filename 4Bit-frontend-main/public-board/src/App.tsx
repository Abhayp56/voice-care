import React from 'react';
import { HeartPulse, Building2, ShieldCheck, EyeOff, PhoneCall } from 'lucide-react';
import PublicPage from './pages/PublicPage';
import { PatientReassurance } from './components/PatientReassurance';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50 text-slate-800 font-sans antialiased selection:bg-emerald-200 selection:text-emerald-950 w-full overflow-x-hidden">
      {/* 1. Dedicated Public Transparency Portal Header (Clean, Civic, Read-Only) */}
      <header className="sticky top-0 z-40 bg-stone-50/95 backdrop-blur-md border-b border-stone-200/90 shadow-soft w-full">
        {/* Civic Transparency Top Notification Bar */}
        <div className="bg-emerald-950 text-emerald-200 text-xs px-3 sm:px-4 py-1.5 flex items-center justify-between font-medium w-full overflow-hidden">
          <div className="flex items-center gap-2 truncate min-w-0">
            <span className="flex h-2 w-2 relative shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
            </span>
            <span className="font-bold text-white text-[11px] sm:text-xs truncate">
              Hospital • Public Grievance Transparency Portal
            </span>
            <span className="hidden md:inline text-emerald-300">• Live Civic Accountability</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-300 shrink-0 text-[11px] ml-2">
            <span className="hidden sm:inline-flex items-center gap-1">
              <EyeOff className="w-3 h-3 text-emerald-400" />
              <span>Strict Privacy Guardrails Active</span>
            </span>
            <span className="bg-emerald-900/90 px-2 py-0.5 rounded font-mono text-emerald-100 border border-emerald-800 text-[10px] sm:text-xs">
              Read-Only Public Board
            </span>
          </div>
        </div>

        {/* Main App Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex items-center justify-between h-14 sm:h-16 gap-2">
            {/* Hospital & VoiceCare Branding */}
            <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
              <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-emerald-800 to-emerald-950 flex items-center justify-center text-white shadow-md shadow-emerald-950/20 shrink-0 border border-amber-400/30">
                <HeartPulse className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-200" aria-hidden="true" />
              </div>

              <div className="flex flex-col justify-center min-w-0">
                <div className="flex items-center gap-2 whitespace-nowrap shrink-0">
                  <span className="text-lg sm:text-xl md:text-2xl font-black tracking-tight text-emerald-950 leading-none flex items-center">
                    4BIT&nbsp;<span className="text-emerald-700 font-extrabold">VoiceCare</span>
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold bg-emerald-50 text-emerald-900 border border-emerald-200 shadow-2xs leading-none shrink-0 self-center">
                    Public Portal
                  </span>
                </div>
                <p className="text-[11px] text-stone-500 font-medium hidden sm:flex items-center gap-1 mt-0.5 leading-tight">
                  <Building2 className="w-3 h-3 text-stone-400 shrink-0" />
                  <span className="truncate">Hospital • Public Complaint Tracking</span>
                </p>
              </div>
            </div>

            {/* Public Portal Status Indicators */}
            <div className="flex items-center gap-2 text-right shrink-0">
              <span className="hidden md:inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-900 bg-emerald-50/80 px-3 py-1 rounded-lg border border-emerald-200">
                <ShieldCheck className="w-4 h-4 text-emerald-700" />
                <span>Zero PII Exposure</span>
              </span>

              {/* Direct-dial Emergency 108 button with PhoneCall icon */}
              <a
                href="tel:108"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-800 bg-rose-50 hover:bg-rose-100 active:bg-rose-200 px-2.5 sm:px-3 py-1.5 rounded-lg border border-rose-200 transition shadow-2xs group shrink-0"
                aria-label="Call emergency service 108"
                title="Tap to call Emergency Hotline 108"
              >
                <PhoneCall className="w-3.5 h-3.5 text-rose-700 group-hover:scale-110 transition-transform" />
                <span className="hidden sm:inline text-stone-700 font-semibold">Emergency:</span>
                <span className="font-mono font-extrabold text-rose-800">108</span>
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Main Public Page Container */}
      <main className="flex-1 w-full overflow-y-auto overflow-x-hidden">
        <PublicPage />
        {/* Alma-Inspired Patient Reassurance & Support Section (Task 1) */}
        <PatientReassurance />
      </main>

      {/* 3. Public Transparency Footer */}
      <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 text-xs py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
            {/* Column 1: Hospital Overview */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <HeartPulse className="w-4 h-4 text-hospital-400" />
                <span>Hospital Grievance Service</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                Dedicated to providing patient-centered healthcare with prompt civic redressal and
                complete operational transparency for all citizens.
              </p>
            </div>

            {/* Column 2: Privacy Guarantee */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Citizen Privacy Guarantee</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                All voice recordings, caller identifications, patient names, and medical details are
                cryptographically stripped prior to publication on this portal.
              </p>
            </div>

            {/* Column 3: Contact & Ombudsman */}
            <div className="space-y-2" id="emergency-notice">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <PhoneCall className="w-4 h-4 text-hospital-400" />
                <span>Civic Helpdesk &amp; Inquiries</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                Help Desk: (080) 2298-4400 &bull; Extension 412
                <br />
                Hospital Ombudsman: Room 104, Admin Wing
                <br />
                Casualty Emergency Code: <span className="text-rose-400 font-bold font-mono">108</span>
              </p>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
            <p>
              &copy; 4BIT VoiceCare Public Transparency Board. All
              rights reserved.
            </p>
            <div className="flex items-center gap-3 font-medium">
              <span>Section 4(1)(b) Compliant</span>
              <span>&bull;</span>
              <span>Zero-PII Token Tracking</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
