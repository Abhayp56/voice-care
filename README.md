# 4BIT VoiceCare

AI-powered, multilingual voice-based public grievance and hospital service monitoring system.

## Documentation Links
- [Supabase Database Schema & Architecture](DATABASE_SCHEMA.md)
- [FastAPI Backend Documentation](backend/README.md)

## Quick Start

### 1. Backend (FastAPI & Supabase)
```powershell
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
API Documentation: `http://localhost:8000/docs`

### 2. Frontend (Patient Voice Terminal / Problem Board)
```powershell
npm install
npm run dev
```
Kiosk / Web App: `http://localhost:5173`
