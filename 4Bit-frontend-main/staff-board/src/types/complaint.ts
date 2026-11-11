import { GrievanceStatus } from './status';

export type StaffRole = 'Department Head' | 'Hospital Administrator' | 'Higher Authority';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: StaffRole;
  department: string;
  departmentId?: string;
  staffId: string;
  shift?: string;
  avatar?: string;
  loggedInAt: string;
}

export interface AiAssessmentData {
  verdict: 'Appears Relevant' | 'Partially Relevant' | 'Inconclusive' | 'Highly Relevant';
  confidence: number;
  matchHeadline: string; // e.g. "AI Match: 94% Relevant - Fixed water leak detected"
  details: string;
  detectedObjects?: string[];
  tamperCheck?: string;
  geofenceStatus?: string;
}

export interface EvidenceData {
  id?: string;
  imageUrl: string;
  imageCaption: string;
  resolutionNote: string;
  staffName: string;
  staffRole: string;
  submittedAt: string;
  isoTimestamp?: string;
  gpsCoordinates?: string;
  gpsLocationName?: string;
  aiAssessment?: AiAssessmentData;
  gpsLatitude?: number;
  gpsLongitude?: number;
  gpsAccuracyMeters?: number;
}

export interface Complaint {
  id: string; // Backend complaint number (VC-YYYY-NNNN)
  timestamp: string;
  language: 'Kannada' | 'English';
  transcript: string;
  summary: string;
  category: string;
  ward: string; // ward name / location
  wardArea?: string; // backwards compatibility alias
  priority: 'Standard' | 'High';
  assignedDepartment: string;
  assignedStaff?: string;
  assignedToId?: string;
  deadline: string;
  isOverdue: boolean;
  overdueDuration?: string;
  status: GrievanceStatus;
  evidence?: EvidenceData;
  reworkReason?: string; // Reason provided when an authority requests rework
}
