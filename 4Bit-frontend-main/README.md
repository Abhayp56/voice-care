# 4BIT VoiceCare Frontend Suite

This folder contains three separate React portals. Each runs on its own local port and calls the FastAPI backend at `http://127.0.0.1:8000`.

| Portal | Folder | Local URL | Purpose |
|---|---|---|---|
| Patient terminal | `problem-board` | `http://localhost:3001` | Microphone recording, speech-to-text, AI conversation, complaint confirmation and submission |
| Department and authority dashboards | `staff-board` | `http://localhost:3002` | Department heads see their department, administrators see all departments, and higher authority sees only cases unresolved for 11 days; photo/GPS evidence, AI advisory, human verification and public submission |
| Public portal | `public-board` | `http://localhost:3003` | Public complaint tracking, complaint feed and aggregate department statistics |

## Before starting

1. Apply the database migrations from `backend/migrations` in numeric order, including `004_gps_escalation_publication.sql`. The API cannot add GPS columns or change public visibility automatically.
2. In the backend `backend/.env`, set `ALLOWED_ORIGINS` to:

   ```env
   ALLOWED_ORIGINS=["http://localhost:3001","http://localhost:3002","http://localhost:3003"]
   ```

3. The staff app needs the project URL and **publishable/anon** Supabase key in `staff-board/.env`:

   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_PUBLISHABLE_KEY=your-publishable-key
   ```

   Never put the service-role/secret key in a frontend environment file. The patient and public apps only need `VITE_API_BASE_URL` and default to the local backend URL.

4. Create each management account in Supabase **Authentication → Users**, then add its matching row to `public.profiles`. Use the Auth user UUID as `id`, the actual name as `full_name`, and one of `department_head`, `hospital_admin`, or `higher_authority` as `role`. Department heads need their department UUID; hospital-wide roles can use a null department. The retired `department_staff` role cannot sign in to the operations dashboard.

## Start the backend

In one PowerShell window:

```powershell
cd D:\Asus\4Bit-voice-care-github\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Restart the backend after changing its `.env` so CORS settings are reloaded.

## Start each portal

Open three more PowerShell windows. If that portal's dependencies are not installed, run `npm install` once in its folder, then start the server:

```powershell
cd D:\Asus\4Bit-voice-care-github\4Bit-frontend-main\problem-board
npm run dev
```

```powershell
cd D:\Asus\4Bit-voice-care-github\4Bit-frontend-main\staff-board
npm run dev
```

```powershell
cd D:\Asus\4Bit-voice-care-github\4Bit-frontend-main\public-board
npm run dev
```

Keep all four terminals open while using the portals. The patient terminal needs browser microphone permission. The staff portal requires real Supabase Auth users and profile rows; it has no demo login or role switch.
