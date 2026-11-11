import React from 'react';
import {
  Inbox,
  AlertCircle,
  UserCheck,
  CheckCircle2,
  Clock,
  FileCheck,
  Search,
  CheckCheck,
  RotateCcw,
  ShieldAlert,
} from 'lucide-react';
import { type GrievanceStatus, STATUS_DEFINITIONS } from '../types/status';
import { cn } from '../utils/cn';

export interface StatusBadgeProps {
  /** The strictly typed grievance status */
  status: GrievanceStatus;
  /** Size variant for different contexts */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to show the status icon */
  showIcon?: boolean;
  /** Whether to show a pulse dot for active states */
  showDot?: boolean;
  /** Optional custom class names */
  className?: string;
  /** Optional ID for aria description */
  id?: string;
}

const ICONS = {
  'inbox': Inbox,
  'alert-circle': AlertCircle,
  'user-check': UserCheck,
  'check-circle-2': CheckCircle2,
  'clock': Clock,
  'file-check': FileCheck,
  'search': Search,
  'check-check': CheckCheck,
  'rotate-ccw': RotateCcw,
  'shield-alert': ShieldAlert,
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
  showDot = false,
  className,
  id,
}) => {
  const config = STATUS_DEFINITIONS[status];

  if (!config) {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-slate-100 text-slate-700">
        Unknown ({status})
      </span>
    );
  }

  const IconComponent = ICONS[config.iconName];

  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5 gap-1.5 font-medium',
    md: 'text-sm px-3.5 py-1 gap-2 font-semibold',
    lg: 'text-base px-4 py-1.5 gap-2.5 font-bold',
  }[size];

  const iconSizes = {
    sm: 13,
    md: 16,
    lg: 18,
  }[size];

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  }[size];

  const isUrgent = status === 'Escalated' || status === 'Needs review';

  return (
    <span
      id={id}
      role="status"
      aria-label={`Status: ${status} - ${config.description}`}
      title={config.description}
      className={cn(
        'inline-flex items-center rounded-full border shadow-sm transition-colors select-none tracking-tight',
        config.bgClass,
        config.textClass,
        config.borderClass,
        sizeClasses,
        className
      )}
    >
      {showDot && (
        <span className="relative flex items-center justify-center">
          {isUrgent && (
            <span
              className={cn(
                'absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping',
                config.dotClass
              )}
            />
          )}
          <span className={cn('relative inline-flex rounded-full', dotSizes, config.dotClass)} />
        </span>
      )}

      {showIcon && IconComponent && (
        <IconComponent
          size={iconSizes}
          aria-hidden="true"
          className="shrink-0 opacity-85"
        />
      )}

      <span>{status}</span>
    </span>
  );
};

export default StatusBadge;
