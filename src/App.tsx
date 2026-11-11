import React, { useState } from 'react';
import { Activity, Building2, HeartPulse } from 'lucide-react';
import TerminalPage from './pages/TerminalPage';
import PublicPortal from './pages/PublicPortal';
import StaffDashboard from './pages/StaffDashboard';

type Page = 'patient' | 'public' | 'staff';

export const App: React.FC = () => {
  const [page, setPage] = useState<Page>('patient');
  return <div className="min-h-screen bg-neutral-50 text-slate-800">
    <header className="fixed inset-x-0 top-0 z-40 border-b bg-white/95 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <a href="#home" onClick={(event) => { event.preventDefault(); setPage('patient'); }} className="flex items-center gap-3 text-emerald-950">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-900 text-amber-300"><HeartPulse aria-hidden="true"/></span>
          <span><strong className="block text-lg">4BIT VoiceCare</strong><small>Hospital service support</small></span>
        </a>
        <div className="flex flex-wrap gap-2" aria-label="Main navigation">
          <button aria-current={page === 'patient' ? 'page' : undefined} onClick={() => setPage('patient')} className={`rounded-lg px-3 py-2 text-sm font-semibold ${page === 'patient' ? 'bg-emerald-900 text-white' : 'border'}`}>Patient terminal</button>
          <button aria-current={page === 'public' ? 'page' : undefined} onClick={() => setPage('public')} className={`rounded-lg px-3 py-2 text-sm font-semibold ${page === 'public' ? 'bg-emerald-900 text-white' : 'border'}`}><Building2 className="mr-1 inline h-4 w-4"/>Public status</button>
          <button aria-current={page === 'staff' ? 'page' : undefined} onClick={() => setPage('staff')} className={`rounded-lg px-3 py-2 text-sm font-semibold ${page === 'staff' ? 'bg-emerald-900 text-white' : 'border'}`}><Activity className="mr-1 inline h-4 w-4"/>Staff dashboard</button>
        </div>
      </div>
    </header>
    {page === 'patient' ? <TerminalPage/> : page === 'public' ? <PublicPortal/> : <StaffDashboard/>}
  </div>;
};

export default App;
