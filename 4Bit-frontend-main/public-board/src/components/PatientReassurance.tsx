import React from 'react';
import { Info, ShieldCheck } from 'lucide-react';

export const PatientReassurance: React.FC = () => (
  <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 w-full" aria-label="Public portal information">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="rounded-2xl bg-white border border-emerald-100 p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 text-emerald-950 font-bold">
          <ShieldCheck className="w-5 h-5 text-emerald-700" />
          <h2>Privacy in public tracking</h2>
        </div>
        <p className="mt-2 text-sm text-slate-600 leading-relaxed">
          Public results show the complaint reference, category, department, date, and current status returned by the hospital system. Patient contact details and resolution photographs are not shown here.
        </p>
      </div>
      <div className="rounded-2xl bg-white border border-amber-100 p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 text-emerald-950 font-bold">
          <Info className="w-5 h-5 text-amber-700" />
          <h2>Urgent help</h2>
        </div>
        <p className="mt-2 text-sm text-slate-600 leading-relaxed">
          This portal tracks service complaints. It does not contact emergency staff or dispatch assistance. For an immediate medical emergency, contact hospital emergency staff directly.
        </p>
      </div>
    </div>
  </section>
);

export default PatientReassurance;
