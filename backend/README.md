# 4BIT VoiceCare — Supabase Database Backend Integration

![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL%20&%20Storage-3ECF8E?logo=supabase&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-Pytest-blue)

4BIT VoiceCare is an AI-powered, multilingual voice-based public grievance and hospital service monitoring system. This module forms the secure, production-grade database backend that connects existing Supabase PostgreSQL tables and Storage to the application's Python FastAPI backend and AI agents.

---

## 1. Project Overview & Architecture

```
   +---------------------------------------------------------------------------------+
   |                                 4BIT VoiceCare                                  |
   |                                                                                 |
   |   [Patient Voice] ---> [Patient Conversation Agent] ---> [Central Orchestrator] |
   |                                                                 |               |
   |                                                                 v               |
   |                                                      +---------------------+    |
   |                                                      |   FastAPI Backend   |    |
   |                                                      |  (Repositories &    |    |
   |                                                      |   Service Layer)    |    |
   |                                                      +---------------------+    |
   |                                                              |     |            |
   |                                      +-----------------------+     +-------+    |
   |                                      v                                     v    |
   |                         +-------------------------+            +---------------+|
   |                         |   Supabase PostgreSQL   |            |  Supabase     ||
   |                         |  (Complaints, History,  |            |  Storage      ||
   |                         |   Categories, Profiles) |            |  ('evidence') ||
   |                         +-------------------------+            +---------------+|
   |                                      |                                          |
   |                                      v                                          |
   |                         +-------------------------+                             |
   |                         |  Public Views (Zero PII)|                             |
   |                         |  - public_complaints    |                             |
   |                         |  - public_dept_stats    |                             |
   |                         +-------------------------+                             |
   +---------------------------------------------------------------------------------+
```

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point & middleware
│   ├── config.py                        # Pydantic Settings & environment validation
│   ├── dependencies.py                  # Injected repository & service providers
│   ├── database/
│   │   ├── __init__.py
│   │   └── supabase_client.py           # Supabase connection & health check module
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── complaint_repository.py      # Complaints CRUD & sequential counter
│   │   ├── department_repository.py     # Departments, categories & routing
│   │   ├── evidence_repository.py       # Evidence metadata management
│   │   ├── status_history_repository.py # Lifecycle transitions & notes trail
│   │   └── user_repository.py           # Staff/admin profiles
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── authentication.py            # Supabase Auth JWT & context resolver
│   │   └── permissions.py               # Department isolation & role enforcement
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage_service.py           # 5MB image validator & signed URL generator
│   │   ├── dashboard_service.py         # Real-time metrics & SLA computations
│   │   └── publication_service.py       # Privacy-safe zero-PII public gateway
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── complaints.py                # Complaint management endpoints
│   │   ├── departments.py               # Department & category endpoints
│   │   ├── dashboard.py                 # Real-time operational analytics
│   │   ├── evidence.py                  # Evidence upload & verification
│   │   └── public.py                   # Civic transparency portal APIs
│   └── models/
│       ├── __init__.py
│       ├── complaint.py                 # Pydantic schemas for complaints
│       ├── department.py                # Department, category & mapping schemas
│       ├── evidence.py                  # Evidence upload & verification schemas
│       ├── user.py                      # User profiles & role definitions
│       ├── status_history.py            # Status history schemas
│       └── dashboard.py                 # Dashboard metrics & public stats
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Fixtures, test client & mocks
│   ├── test_auth_permissions.py         # Role & department isolation tests
│   ├── test_complaints.py               # Complaint CRUD & numbering tests
│   ├── test_connection.py               # Supabase connection & config tests
│   ├── test_dashboard.py                # Operational metrics calculation tests
│   ├── test_departments.py              # Department routing & isolation tests
│   ├── test_evidence.py                 # Storage limits & upload validation tests
│   └── test_public.py                   # Strict Zero-PII public privacy tests
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. Setup & Installation

### 3.1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Existing Supabase project credentials

### 3.2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3.3. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Ensure the `.env` file contains your credentials:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=replace-with-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=replace-with-rotated-service-role-key
SUPABASE_STORAGE_BUCKET=evidence
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development
ALLOW_DEV_AUTH_HEADERS=false
ALLOWED_ORIGINS=["http://localhost:3001"]
```
The identity-header development shortcut is disabled by default and is rejected unless the environment is exactly `development`. Never enable it in a deployed environment. Configure `ALLOWED_ORIGINS` as a JSON array of exact browser origins.

Before starting the API against a fresh Supabase project, open **SQL Editor** in the Supabase dashboard and run the migration files in this order:

1. `migrations/000_initial_schema.sql` — creates the base tables, privacy-safe views, starter categories/departments and their routing, and the private `evidence` storage bucket.
2. `migrations/001_atomic_complaint_number.sql`
3. `migrations/002_lifecycle_notifications.sql`
4. `migrations/003_ai_evidence_reviews.sql`
5. `migrations/004_gps_escalation_publication.sql` — stores upload GPS snapshots and restricts public complaint feeds/statistics to submitted resolutions.

The SQL files are not run automatically by the application. Review the starter hospital departments and category-to-department routing in `000_initial_schema.sql` and adjust them for your hospital before applying. The seeded defaults are examples. Add approved rows to `complaint_sla_policies` after migration 002 if lifecycle deadlines are needed; the project does not assume hospital SLA durations.

### 3.4. Run the Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive Swagger API documentation will be available at:
`http://localhost:8000/docs`

---

## 4. Running Tests

Run the complete automated test suite (26 tests covering connection, complaint lifecycle, department isolation, storage limits, and public privacy):
```powershell
pytest tests/ -v
```

---

## 5. Guide for AI Backend Developers

Our application features three AI agents:
1. **Central Orchestrator Agent** (OpenRouter)
2. **Patient Conversation Agent**
3. **Evidence Verification Agent**

### Crucial Security Principles:
- **No Direct Database Access**: AI agents **never** interact directly with Supabase or hold service role credentials.
- **Structured Validation**: All agent payloads pass through Pydantic validators in FastAPI before reaching the database.
- **Automatic Routing**: AI agents do not need to guess department IDs; the backend automatically routes complaints based on category mappings.

### 5.1. Creating Complaints from Patient Conversation Agent
When the Patient Conversation Agent gathers grievance details, send a `POST /api/complaints` request:

```python
import httpx

payload = {
    "description": "Ward 3B ventilator power plug is loose and sparking.",
    "language": "en",
    "category_id": "292fa3f4-0d9e-4b06-a272-ce23eaeaf808", # 'Electricity Problem'
    "patient_name": "Ramesh Kumar",                         # Stored securely; never public
    "patient_phone": "+91-9876543210"
    # Department and priority are derived by the backend from its trusted category mapping.
}

response = httpx.post("http://localhost:8000/api/complaints", json=payload)
data = response.json()
print("Lodged tracking number:", data["complaint_number"]) # e.g. VC-2026-0006
```

### 5.2. Querying Department Mappings (Central Orchestrator)
The Orchestrator can retrieve all categories and their mapped departments to help patients categorize complaints:
```python
response = httpx.get("http://localhost:8000/api/department-mappings")
mappings = response.json()
```

### 5.3. Verifying Resolution Evidence (Authorized Human Reviewer)
An authenticated department head or hospital administrator submits the review decision using a verified Supabase access token:
```python
headers = {
    "Authorization": "Bearer <SUPABASE_ACCESS_TOKEN>"
}

verdict = {
    "verified": True,
    "notes": "Visual inspection confirms replacement of outlet with certified industrial socket."
}

response = httpx.post(
    f"http://localhost:8000/api/evidence/{evidence_id}/verify",
    json=verdict,
    headers=headers
)
```

---

## 6. API Reference Summary

| Method | Endpoint | Auth Required | Description |
|:---|:---|:---|:---|
| **GET** | `/health` | No | Verifies Supabase connection and database reachability |
| **POST** | `/api/complaints` | Optional/Service | Lodges a new complaint; auto-assigns sequential tracking number & department |
| **GET** | `/api/complaints` | Yes | Paginated complaint query with department isolation |
| **GET** | `/api/complaints/{id}` | Yes | Retrieves full complaint record |
| **PATCH** | `/api/complaints/{id}/status` | Yes | Updates status (`in_progress`, `resolved`), adds resolution note |
| **GET** | `/api/complaints/{id}/history` | Yes | Retrieves full lifecycle status history |
| **POST** | `/api/complaints/{id}/evidence` | Yes | Uploads evidence photo (max 5MB, JPEG/PNG/WebP) to Supabase Storage |
| **GET** | `/api/complaints/{id}/evidence` | Yes | Returns complaint evidence with temporary signed URLs |
| **POST** | `/api/evidence/{id}/verify` | Yes | Submits verification approval from AI or department head |
| **GET** | `/api/departments` | No | Lists all hospital operational departments |
| **GET** | `/api/departments/{id}/complaints` | Yes | Complaints for specific department (department isolation enforced) |
| **GET** | `/api/categories` | No | Lists complaint categories and default priorities |
| **GET** | `/api/dashboard/stats` | Yes | Real-time computed metrics, SLA overdue counts, distributions |
| **GET** | `/api/public/complaints` | **No** | **Privacy-safe** civic complaints feed (strictly zero PII) |
| **GET** | `/api/public/complaints/{number}` | **No** | Public tracking by `VC-YYYY-NNNN` |
| **GET** | `/api/public/department-statistics` | **No** | Aggregated civic accountability metrics per department |

---

## 7. Security, Privacy & Department Isolation

1. **Service Role Security**: The `SUPABASE_SERVICE_ROLE_KEY` is loaded securely on the backend server and never sent to clients or AI agents.
2. **Department Isolation**: Staff with role `department_staff` or `department_head` are strictly blocked (403 Forbidden) from viewing or updating complaints assigned to other departments.
3. **Zero-PII Public Guarantee**: The public endpoints query PostgreSQL views (`public_complaints_view` and `public_department_statistics`) which omit `patient_name`, `patient_phone`, descriptions, and staff IDs by database design.
4. **Private Storage**: Storage bucket `evidence` is private. Photographs are only accessible via short-lived signed URLs generated for authenticated staff.

## 8. Current AI, voice, lifecycle, and frontend integration

The patient terminal calls the backend at `/api/conversation` and `/api/voice`. Voice recording is captured in the browser and sent to Sarvam STT; spoken replies use Sarvam TTS. Complaint submission remains gated by patient confirmation and the server returns the real complaint number. The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

Gemini and Groq are configured independently by role. Set each role's model to a model enabled for the corresponding account. For separate billing/accounts, set `GEMINI_CONVERSATION_API_KEY`, `GROQ_CONVERSATION_API_KEY`, `GEMINI_ORCHESTRATOR_API_KEY`, `GROQ_ORCHESTRATOR_API_KEY`, `GEMINI_VERIFICATION_API_KEY`, and `GROQ_VERIFICATION_API_KEY`. Blank role-specific keys fall back to `GEMINI_API_KEY` and `GROQ_API_KEY`. Provider order is configurable with `AI_CONVERSATION_PROVIDERS`, `AI_ORCHESTRATOR_PROVIDERS`, and `AI_VERIFICATION_PROVIDERS`.

The orchestrator endpoint (`POST /api/orchestrator/assess`) requires a hospital administrator or higher authority and returns advice only. Evidence advice is available at `POST /api/evidence/{evidence_id}/analyze`; it is stored separately and always requires human review. AI advice never sets the human `verified` field or resolves a complaint.

Apply migrations in order as described in Setup above. The API does not apply migrations automatically. The lifecycle trigger creates persisted status events and queues notification outbox records in the same transaction. It does not send SMS/email. Add hospital-approved rows to `complaint_sla_policies` before expecting deadlines; no default SLA durations are assumed. A notification delivery provider/worker and an outbox operations screen still need configuration before queued notifications can be reported as delivered.

