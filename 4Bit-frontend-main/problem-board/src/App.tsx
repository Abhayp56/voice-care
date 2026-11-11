import React from 'react';
import { HeartPulse, Building2, Activity } from 'lucide-react';
import TerminalPage from './pages/TerminalPage';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-neutral-50 text-slate-800 font-sans antialiased selection:bg-amber-100 selection:text-emerald-950 relative overflow-x-hidden">
      {/* Subtle Kiosk Background Pattern (Faint Dotted Matrix Grid in Muted Emerald/Gold) */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-30"
        style={{
          backgroundImage: `radial-gradient(rgba(6, 78, 59, 0.10) 1.5px, transparent 1.5px)`,
          backgroundSize: '24px 24px',
        }}
        aria-hidden="true"
      />

      {/* Large Transparent Hospital Cross Watermark */}
      <div
        className="fixed inset-0 flex items-center justify-center pointer-events-none z-0 select-none overflow-hidden"
        aria-hidden="true"
      >
        <svg
          className="w-[480px] h-[480px] sm:w-[650px] sm:h-[650px] text-emerald-900/[0.03] fill-current"
          viewBox="0 0 24 24"
        >
          <path d="M19 10.5h-5.5V5c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v5.5H5c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5h5.5V19c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5v-5.5H19c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5z" />
        </svg>
      </div>

      {/* 1. Dedicated Patient Terminal Header (Official Hospital Kiosk) */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-neutral-50/95 backdrop-blur-md border-b border-neutral-200/90 shadow-soft">
        {/* Prototype Context Banner */}
        <div className="bg-emerald-950 text-neutral-200 text-xs px-3 sm:px-4 py-1.5 flex items-center justify-between font-medium border-b border-emerald-900/40">
          <div className="flex items-center gap-2 truncate">
            <span className="flex h-2 w-2 relative shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400/50 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400/70"></span>
            </span>
            <span className="font-bold text-neutral-100 text-[11px] sm:text-xs truncate">
              Hospital • Patient Voice Terminal
            </span>
            <span className="hidden md:inline text-amber-200/80 font-medium">• Live Kiosk Mode</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-300 shrink-0 text-[11px]">
            <span className="hidden sm:inline">Voice Engine: Active</span>
            <span className="bg-emerald-900/90 px-2 py-0.5 rounded font-mono text-amber-200/90 border border-amber-400/25">
              Terminal Kiosk
            </span>
          </div>
        </div>

        {/* Main App Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Hospital Branding */}
            <div className="flex items-center gap-2.5 sm:gap-3">
              <div className="w-9 h-9 sm:w-11 sm:h-11 rounded-xl bg-gradient-to-br from-emerald-900 to-emerald-950 flex items-center justify-center text-amber-300/80 shadow-md shadow-emerald-950/20 border border-amber-400/25 shrink-0">
                <HeartPulse className="w-5 h-5 sm:w-6 sm:h-6" aria-hidden="true" />
              </div>

              <div className="flex flex-col justify-center">
                <div className="flex items-center gap-2 whitespace-nowrap shrink-0">
                  <span className="text-lg sm:text-xl md:text-2xl font-black tracking-tight text-emerald-900 leading-none flex items-center">
                    4BIT&nbsp;<span className="text-emerald-900 font-black">VoiceCare</span>
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-[11px] font-bold bg-amber-400/15 text-amber-700/80 border border-amber-300/35 shadow-2xs leading-none shrink-0 self-center">
                    Patient Terminal
                  </span>
                </div>
                <p className="text-[11px] text-neutral-500 font-medium hidden sm:flex items-center gap-1 mt-0.5 leading-tight">
                  <Building2 className="w-3 h-3 text-amber-700/80 shrink-0" />
                  <span className="truncate">Hospital • Voice Grievance Kiosk</span>
                </p>
              </div>
            </div>

            {/* Kiosk Status Indicator */}
            <div className="flex items-center gap-1.5 text-right shrink-0">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-emerald-900 bg-neutral-100/90 px-2.5 py-1 rounded-lg border border-neutral-200">
                <Activity className="w-3.5 h-3.5 text-amber-700/80" />
                <span>Kiosk Online</span>
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Isolated Terminal Page Container (Sole and Default Screen) */}
      <main className="flex-1 w-full overflow-x-hidden">
        <TerminalPage />
      </main>
    </div>
  );
};

export default App;
