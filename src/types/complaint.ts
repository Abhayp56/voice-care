import { GrievanceStatus } from './status';

export interface EvidenceData {
  imageUrl: string;
  imageCaption: string;
  resolutionNote: string;
  staffName: string;
  staffRole: string;
  submittedAt: string;
  gpsCoordinates: string;
  gpsLocationName: string;
  aiAssessment: {
    verdict: 'Appears Relevant' | 'Partially Relevant' | 'Inconclusive';
    confidence: number;
    details: string;
  };
}

export interface Complaint {
  id: string; // e.g. "#VOC-8291"
  timestamp: string;
  language: 'Kannada' | 'English';
  transcript: string;
  summary: string;
  category: string;
  wardArea: string;
  priority: 'Standard' | 'High';
  assignedDepartment: string;
  assignedStaff?: string;
  deadline: string;
  isOverdue: boolean;
  overdueDuration?: string;
  status: GrievanceStatus;
  evidence?: EvidenceData;
}

export type StaffRole = 'Ward Staff (Sanitation)' | 'Department Head' | 'Hospital Administrator';
