export const STATUS_STATES = [
  'Received',
  'Needs review',
  'Assigned',
  'Acknowledged',
  'In progress',
  'Evidence submitted',
  'Under verification',
  'Resolved',
  'Reopened',
  'Escalated',
] as const;

export type GrievanceStatus = (typeof STATUS_STATES)[number];

export interface StatusConfig {
  label: GrievanceStatus;
  description: string;
  bgClass: string;
  textClass: string;
  borderClass: string;
  dotClass: string;
  iconName: 'inbox' | 'alert-circle' | 'user-check' | 'check-circle-2' | 'clock' | 'file-check' | 'search' | 'check-check' | 'rotate-ccw' | 'shield-alert';
}

export const STATUS_DEFINITIONS: Record<GrievanceStatus, StatusConfig> = {
  'Received': {
    label: 'Received',
    description: 'Complaint securely logged into hospital system',
    bgClass: 'bg-stone-100',
    textClass: 'text-stone-800',
    borderClass: 'border-stone-200',
    dotClass: 'bg-stone-500',
    iconName: 'inbox',
  },
  'Needs review': {
    label: 'Needs review',
    description: 'Action Required: Pending triage and classification',
    bgClass: 'bg-amber-50',
    textClass: 'text-amber-700',
    borderClass: 'border-amber-200/60',
    dotClass: 'bg-amber-500/60',
    iconName: 'alert-circle',
  },
  'Assigned': {
    label: 'Assigned',
    description: 'Directed to responsible department head or duty doctor',
    bgClass: 'bg-sky-50',
    textClass: 'text-sky-950',
    borderClass: 'border-sky-200',
    dotClass: 'bg-sky-600',
    iconName: 'user-check',
  },
  'Acknowledged': {
    label: 'Acknowledged',
    description: 'Department has confirmed receipt and begun investigation',
    bgClass: 'bg-blue-50',
    textClass: 'text-blue-950',
    borderClass: 'border-blue-200',
    dotClass: 'bg-blue-600',
    iconName: 'check-circle-2',
  },
  'In progress': {
    label: 'In progress',
    description: 'Corrective action or medical inquiry is underway',
    bgClass: 'bg-teal-50',
    textClass: 'text-teal-950',
    borderClass: 'border-teal-200',
    dotClass: 'bg-teal-600',
    iconName: 'clock',
  },
  'Evidence submitted': {
    label: 'Evidence submitted',
    description: 'Duty logs, photos, or medical records uploaded by staff',
    bgClass: 'bg-purple-50',
    textClass: 'text-purple-950',
    borderClass: 'border-purple-200',
    dotClass: 'bg-purple-600',
    iconName: 'file-check',
  },
  'Under verification': {
    label: 'Under verification',
    description: 'Quality assurance team validating the proposed resolution',
    bgClass: 'bg-violet-50',
    textClass: 'text-violet-950',
    borderClass: 'border-violet-200',
    dotClass: 'bg-violet-600',
    iconName: 'search',
  },
  'Resolved': {
    label: 'Resolved',
    description: 'Issue successfully addressed and confirmed resolved',
    bgClass: 'bg-emerald-50',
    textClass: 'text-emerald-950',
    borderClass: 'border-emerald-300',
    dotClass: 'bg-emerald-700',
    iconName: 'check-check',
  },
  'Reopened': {
    label: 'Reopened',
    description: 'Action Required: Returned for re-examination and rework',
    bgClass: 'bg-orange-50',
    textClass: 'text-orange-950',
    borderClass: 'border-orange-200',
    dotClass: 'bg-orange-600',
    iconName: 'rotate-ccw',
  },
  'Escalated': {
    label: 'Escalated',
    description: 'Overdue / Critical SLA Breach: Escalated directly to Superintendent',
    bgClass: 'bg-amber-50',
    textClass: 'text-amber-700',
    borderClass: 'border-amber-200/60',
    dotClass: 'bg-amber-500/60',
    iconName: 'shield-alert',
  },
};
