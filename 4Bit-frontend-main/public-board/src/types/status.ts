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
    bgClass: 'bg-slate-100',
    textClass: 'text-slate-800',
    borderClass: 'border-slate-300',
    dotClass: 'bg-slate-500',
    iconName: 'inbox',
  },
  'Needs review': {
    label: 'Needs review',
    description: 'Pending triage and classification by hospital officer',
    bgClass: 'bg-amber-100',
    textClass: 'text-amber-900',
    borderClass: 'border-amber-300',
    dotClass: 'bg-amber-600',
    iconName: 'alert-circle',
  },
  'Assigned': {
    label: 'Assigned',
    description: 'Directed to responsible department head or duty doctor',
    bgClass: 'bg-sky-100',
    textClass: 'text-sky-900',
    borderClass: 'border-sky-300',
    dotClass: 'bg-sky-600',
    iconName: 'user-check',
  },
  'Acknowledged': {
    label: 'Acknowledged',
    description: 'Department has confirmed receipt and begun investigation',
    bgClass: 'bg-blue-100',
    textClass: 'text-blue-900',
    borderClass: 'border-blue-300',
    dotClass: 'bg-blue-600',
    iconName: 'check-circle-2',
  },
  'In progress': {
    label: 'In progress',
    description: 'Corrective action or medical inquiry is underway',
    bgClass: 'bg-teal-100',
    textClass: 'text-teal-900',
    borderClass: 'border-teal-300',
    dotClass: 'bg-teal-600',
    iconName: 'clock',
  },
  'Evidence submitted': {
    label: 'Evidence submitted',
    description: 'Duty logs, photos, or medical records uploaded by staff',
    bgClass: 'bg-purple-100',
    textClass: 'text-purple-900',
    borderClass: 'border-purple-300',
    dotClass: 'bg-purple-600',
    iconName: 'file-check',
  },
  'Under verification': {
    label: 'Under verification',
    description: 'Quality assurance team validating the proposed resolution',
    bgClass: 'bg-violet-100',
    textClass: 'text-violet-900',
    borderClass: 'border-violet-300',
    dotClass: 'bg-violet-600',
    iconName: 'search',
  },
  'Resolved': {
    label: 'Resolved',
    description: 'Issue successfully addressed and confirmed resolved',
    bgClass: 'bg-emerald-100',
    textClass: 'text-emerald-900',
    borderClass: 'border-emerald-300',
    dotClass: 'bg-emerald-600',
    iconName: 'check-check',
  },
  'Reopened': {
    label: 'Reopened',
    description: 'Patient requested re-examination after unsatisfying resolution',
    bgClass: 'bg-orange-100',
    textClass: 'text-orange-900',
    borderClass: 'border-orange-300',
    dotClass: 'bg-orange-600',
    iconName: 'rotate-ccw',
  },
  'Escalated': {
    label: 'Escalated',
    description: 'Urgent priority escalated directly to Hospital Medical Superintendent',
    bgClass: 'bg-rose-100',
    textClass: 'text-rose-950',
    borderClass: 'border-rose-300',
    dotClass: 'bg-rose-600',
    iconName: 'shield-alert',
  },
};
