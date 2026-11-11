# 4BIT VoiceCare — Supabase Database Architecture & Schema Documentation

> **Status:** Live & Active  
> **Supabase Project URL:** `https://kxmhrmgssjfpbsjbwlmi.supabase.co`  
> **Inspection Date:** November 7, 2026  
> **Author:** 4BIT VoiceCare Backend Engineering  

---

## 1. Architecture Overview

**4BIT VoiceCare** is an AI-powered, multilingual voice-based public grievance and hospital service monitoring system. The database architecture is built on PostgreSQL inside Supabase, featuring strict Row Level Security (RLS), automated audit logging, complaint numbering counters, relational routing between categories and departments, evidence verification pipelines, and privacy-preserving public views.

```
+-------------------------------------------------------------+
|                     4BIT VoiceCare Flow                     |
|                                                             |
|   [Patient Voice] --> [Voice Agent] --> [Orchestrator]     |
|                                                |            |
|                                                v            |
|             +---------------------------------------+       |
|             |          FastAPI Backend              |       |
|             |      (Service Role Client)            |       |
|             +---------------------------------------+       |
|                   |                      |                  |
|                   v                      v                  |
|        +--------------------+  +--------------------+       |
|        | PostgreSQL Tables  |  | Supabase Storage   |       |
|        | (Complaints, etc.) |  | ('evidence' bucket)|       |
|        +--------------------+  +--------------------+       |
|                   |                                         |
|                   v                                         |
|        +--------------------------------------------+       |
|        | Public Views (No PII: Patient Names/Phone) |       |
|        +--------------------------------------------+       |
+-------------------------------------------------------------+
```

---

## 2. Storage Buckets

| Bucket Name | Access | Max File Size | Allowed MIME Types | Purpose |
|:---|:---|:---|:---|:---|
| `evidence` | **Private** (`public: false`) | **5 MB** (5,242,880 bytes) | `image/jpeg`, `image/png`, `image/webp` | Resolution evidence photos uploaded by staff, reviewed by verification agent |

---

## 3. Database Tables & Schema Specifications

### 3.1. `departments`
Stores hospital operational departments responsible for resolving grievances.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique department identifier |
| `name` | `text` | No | - | Department name (e.g., 'Maintenance', 'Sanitation', 'Pharmacy', 'Administration') |
| `description` | `text` | Yes | - | Detailed scope of the department |
| `created_at` | `timestamptz` | No | `now()` | Record creation timestamp |
| `updated_at` | `timestamptz` | No | `now()` | Record update timestamp |

---

### 3.2. `complaint_categories`
Classification taxonomy for complaints, with predefined SLA priorities.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique category identifier |
| `name` | `text` | No | - | Category title ('Drinking Water', 'Washroom Cleanliness', 'Medicine Availability', 'Bed Availability', 'Electricity Problem', 'Staff Availability') |
| `default_priority` | `text` | No | `'medium'` | Default urgency ('low', 'medium', 'high', 'critical') |
| `created_at` | `timestamptz` | No | `now()` | Record creation timestamp |
| `updated_at` | `timestamptz` | No | `now()` | Record update timestamp |

---

### 3.3. `department_mapping`
Maps complaint categories to the responsible hospital department.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Constraints |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique mapping identifier |
| `category_id` | `uuid` | No | - | Foreign Key -> `complaint_categories(id)` |
| `department_id` | `uuid` | No | - | Foreign Key -> `departments(id)` |
| `created_at` | `timestamptz` | No | `now()` | Record creation timestamp |

---

### 3.4. `profiles`
User profiles for hospital staff, heads, and administrators, linked to Supabase Auth (`auth.users.id`).

- **Primary Key:** `id` (UUID, references `auth.users.id`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | - | Linked to Supabase Auth user ID |
| `full_name` | `text` | No | - | Staff / Officer full name |
| `role` | `text` | No | `'department_staff'` | Staff role (`department_staff`, `department_head`, `hospital_admin`, `higher_authority`) |
| `department_id` | `uuid` | Yes | `null` | Foreign Key -> `departments(id)` (null for hospital-wide admins) |
| `created_at` | `timestamptz` | No | `now()` | Profile creation timestamp |
| `updated_at` | `timestamptz` | No | `now()` | Profile update timestamp |

---

### 3.5. `complaints`
Central repository for all patient grievances. Contains sensitive patient PII protected by RLS.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes (Anon access denied; public access exclusively through `public_complaints_view`)

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Internal unique UUID |
| `complaint_number` | `text` | No | - | Human-readable tracking number (`VC-YYYY-NNNN`) |
| `patient_name` | `text` | Yes | - | Patient name (Confidential PII) |
| `patient_phone` | `text` | Yes | - | Patient contact number (Confidential PII) |
| `description` | `text` | No | - | Grievance description transcribed from voice conversation |
| `language` | `text` | No | `'en'` | Language code of the voice submission (e.g. `'en'`, `'kn'`, `'hi'`) |
| `category_id` | `uuid` | No | - | Foreign Key -> `complaint_categories(id)` |
| `department_id` | `uuid` | No | - | Foreign Key -> `departments(id)` |
| `priority` | `text` | No | `'medium'` | Priority level: `'low'`, `'medium'`, `'high'`, `'critical'` |
| `status` | `text` | No | `'received'` | Status: `'received'`, `'assigned'`, `'in_progress'`, `'needs_review'`, `'resolved'`, `'escalated'`, `'closed'` |
| `assigned_to` | `uuid` | Yes | `null` | Foreign Key -> `profiles(id)` |
| `resolved_at` | `timestamptz` | Yes | `null` | Timestamp when marked resolved |
| `created_at` | `timestamptz` | No | `now()` | Submission timestamp |
| `updated_at` | `timestamptz` | No | `now()` | Last modification timestamp |

---

### 3.6. `complaint_number_counter`
Atomic sequence tracker for human-readable complaint numbers formatted as `VC-YYYY-NNNN`.

- **Primary Key:** `year` (INT)

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `year` | `integer` | No | - | Calendar year (e.g. `2026`) |
| `last_number` | `integer` | No | `0` | Running sequential integer |

---

### 3.7. `status_history`
Audit trail of complaint status transitions and operational notes.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique log identifier |
| `complaint_id` | `uuid` | No | - | Foreign Key -> `complaints(id)` |
| `old_status` | `text` | Yes | - | Status before transition |
| `new_status` | `text` | No | - | Status after transition |
| `changed_by` | `uuid` | Yes | - | Foreign Key -> `profiles(id)` |
| `note` | `text` | Yes | - | Resolution or transition notes |
| `created_at` | `timestamptz` | No | `now()` | Transition timestamp |

---

### 3.8. `evidence`
Resolution proof records submitted by department staff and verified by AI and department heads.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique evidence record identifier |
| `complaint_id` | `uuid` | No | - | Foreign Key -> `complaints(id)` |
| `file_path` | `text` | No | - | Storage path in Supabase bucket (`evidence/<complaint_id>/...`) |
| `file_type` | `text` | No | `'image'` | Type of file (`'image'`, `'document'`, `'note'`) |
| `notes` | `text` | Yes | - | Description of resolution action |
| `submitted_by` | `uuid` | Yes | - | Foreign Key -> `profiles(id)` |
| `verified_by` | `uuid` | Yes | - | Foreign Key -> `profiles(id)` |
| `verified_at` | `timestamptz` | Yes | - | Verification timestamp |
| `created_at` | `timestamptz` | No | `now()` | Upload timestamp |

---

### 3.9. `escalations`
SLA breach escalation records for unattended or overdue grievances.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique escalation identifier |
| `complaint_id` | `uuid` | No | - | Foreign Key -> `complaints(id)` |
| `department_id` | `uuid` | No | - | Foreign Key -> `departments(id)` |
| `deadline` | `timestamptz` | No | - | Expected resolution deadline |
| `escalated_at` | `timestamptz` | No | `now()` | Escalation trigger timestamp |
| `reason` | `text` | Yes | - | Escalation trigger explanation |
| `resolved_at` | `timestamptz` | Yes | - | Escalation resolution timestamp |

---

### 3.10. `audit_logs`
System-wide immutable audit trail. Driven by PostgreSQL database triggers.

- **Primary Key:** `id` (UUID, Default: `gen_random_uuid()`)
- **RLS Enabled:** Yes

| Column | Type | Nullable | Default | Description |
|:---|:---|:---|:---|:---|
| `id` | `uuid` | No | `gen_random_uuid()` | Unique audit record identifier |
| `actor_id` | `uuid` | Yes | - | Foreign Key -> `profiles(id)` |
| `action` | `text` | No | - | Operation action (`INSERT`, `UPDATE`, `DELETE`) |
| `table_name` | `text` | No | - | Target table name |
| `record_id` | `uuid` | Yes | - | Modified record UUID |
| `details` | `jsonb` | Yes | - | Snapshot payload or field diff |
| `created_at` | `timestamptz` | No | `now()` | Trigger execution timestamp |

---

## 4. Database Views (Public & Transparency APIs)

### 4.1. `public_complaints_view`
Provides privacy-safe data for the public transparency portal. Zero patient PII exposed.

| Column | Type | Source Column |
|:---|:---|:---|
| `complaint_number` | `text` | `complaints.complaint_number` |
| `department_name` | `text` | `departments.name` |
| `category_name` | `text` | `complaint_categories.name` |
| `status` | `text` | `complaints.status` |
| `submission_date` | `date` | `DATE(complaints.created_at)` |

### 4.2. `public_department_statistics`
Aggregated department performance metrics for civic monitoring.

| Column | Type | Description |
|:---|:---|:---|
| `department_name` | `text` | Name of department |
| `total_complaints` | `int64` | Total grievances logged |
| `resolved_count` | `int64` | Total grievances resolved |
| `open_count` | `int64` | Total grievances currently unresolved |

---

## 5. Security & Access Control Matrix

1. **Row Level Security (RLS)**:
   - Direct anonymous access to `complaints`, `profiles`, `audit_logs`, and other operational tables is strictly restricted.
   - All backend client calls for business workflows use the verified backend with `SUPABASE_SERVICE_ROLE_KEY`.
2. **PII Protection**:
   - `patient_name`, `patient_phone`, and raw transcripts must never be returned through public APIs.
   - Public view endpoints strip all sensitive identifiers.
3. **Role-Based Access Control (RBAC)**:
   - `department_staff`: Can view complaints belonging to their own department, submit evidence, and update status.
   - `department_head`: Can view, reassign, approve evidence, and resolve complaints within their department.
   - `hospital_admin`: Hospital-wide visibility across all departments and audit logs.
   - `higher_authority`: Read-only oversight across all hospital performance and escalation logs.
4. **AI Agent Access Rules**:
   - AI agents (Patient Conversation Agent, Central Orchestrator, Evidence Verification Agent) **never** hold direct database credentials.
   - All interactions must go through structured FastAPI endpoints with input validation before database persistence.

