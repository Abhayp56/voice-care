import { GrievanceStatus } from './status';

/**
 * ============================================================================
 * CRUCIAL PRIVACY GUARDRAILS: PUBLIC TRANSPARENCY DATA MODEL
 * ============================================================================
 * Under the Hospital Citizen Privacy & Transparency Charter:
 * - NO patient names, phone numbers, or government IDs are ever stored or exposed.
 * - NO raw audio recordings or voice biometric data are made publicly accessible.
 * - NO personal medical diagnoses, prescriptions, or bed assignments are exposed.
 * - All complaints are tracked strictly by cryptographic, non-identifying tokens
 *   (for example, the reference issued after submission).
 * ============================================================================
 */

export interface PublicComplaintRecord {
  /** Publicly trackable backend complaint number. */
  id: string;
  /** High-level operational service category */
  category: string;
  /** Responsible hospital department */
  department: string;
  /** High-level campus zone (non-identifying) */
  zone: string;
  /** Current verified grievance lifecycle status */
  status: GrievanceStatus;
  /** Public timestamp when the grievance token was registered */
  loggedDate: string;
  /** Non-identifying operational audit milestone */
  operationalMilestone: string;
}

export interface DepartmentMetric {
  id: string;
  departmentName: string;
  category: string;
  resolutionRate: number; // e.g. 98.2%
  totalComplaints: number;
  resolvedComplaints: number;
  iconName: 'sparkles' | 'wrench' | 'pill' | 'activity' | 'file-text' | 'utensils';
}
