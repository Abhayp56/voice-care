import React from 'react';
import { Inbox, CheckCircle2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'All caught up! No pending grievances here.',
  description = 'Everything has been addressed or no tickets match the current criteria.',
  icon,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-8 sm:p-12 rounded-3xl bg-white border border-slate-200/80 shadow-soft text-center flex flex-col items-center justify-center space-y-3 transition-all',
        className
      )}
    >
      <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-hospital-50 border border-hospital-200/80 text-hospital-600 shadow-2xs">
        {icon || (
          <>
            <Inbox className="w-8 h-8 text-hospital-600/90" strokeWidth={1.75} aria-hidden="true" />
            <span className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs">
              <CheckCircle2 className="w-4 h-4" strokeWidth={2.5} />
            </span>
          </>
        )}
      </div>

      <div className="space-y-1 max-w-sm mx-auto">
        <h4 className="text-base sm:text-lg font-bold text-slate-800 tracking-tight">
          {title}
        </h4>
        <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
          {description}
        </p>
      </div>

      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

export default EmptyState;
