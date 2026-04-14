# StackGear AI

**Hardware Hub — Full-Stack Inventory Management System**

---

## Overview

StackGear AI is a full-stack hardware inventory management system with:

- Real-time updates (Socket.IO)
- AI-powered semantic search (Google Gemini)
- Role-based access control

---

## Live URLs

- **Frontend:** https://stackgear.vercel.app  
- **Backend API:** https://stackgear-ai.fly.dev  
- **Health Check:** https://stackgear-ai.fly.dev/health  

---

## Tech Stack

### Backend
- Python 3.12
- FastAPI
- Socket.IO
- SQLAlchemy
- Neon PostgreSQL

### Frontend
- Vue 3
- Vite
- Socket.IO Client
- Vercel

### AI
- Google Gemini API

### Infrastructure
- Fly.io (shared-cpu-1x, 256MB RAM)
- Vercel (Hobby)

---

## Project Structure

```text
stackgear-ai/
├── app/
│   ├── main.py          # FastAPI app + Socket.IO ASGI wrapper
│   ├── sockets.py       # Socket.IO server
│   ├── routers/         # auth, users, hardware, ai
│   └── database.py      # SQLAlchemy + Neon Postgres
├── frontend/
│   ├── src/
│   │   ├── views/       # Login, Dashboard, Admin
│   │   ├── stores/      # Pinia auth store
│   │   └── api/         # hardware.js, users.js
│   ├── .env.production  # VITE_API_URL
│   └── vercel.json
├── Dockerfile
├── fly.toml
└── pyproject.toml
```

---

## Environment Variables

### Backend (Fly.io secrets)

- `DATABASE_URL` — Neon PostgreSQL connection string  
- `SECRET_KEY` — JWT signing secret  
- `GEMINI_API_KEY` — Google Gemini API key  

### Frontend

```env
VITE_API_URL=https://stackgear-ai.fly.dev
```

---

## Local Development

### Backend

```bash
uv sync
uv run uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Deployment

### Backend (Fly.io)

```bash
flyctl deploy
```

### Frontend (Vercel)

```bash
cd frontend
vercel --prod
```

---

## Key Architecture Decisions

- CORS must wrap the **outer ASGI app (`socket_app`)**
- Uvicorn must serve `app.main:socket_app`
- Single Fly.io machine prevents OOM issues
- Neon PostgreSQL ensures shared state
- Fixed JWT secret ensures token validity across instances

---

## Known Limits

- Gemini free tier: ~20 requests/day  
- Fly.io: cold starts (~3–5s after inactivity)  
- Vercel Hobby: no WebSocket support (Socket.IO connects directly to backend)

---

## Production Notes

- Fully cloud-hosted (no terminal required)
- Free-tier friendly setup
- Fly.io requires a credit card on file

---

## Status

✅ Stable for small-scale usage (~3 concurrent users)  
⚠️ Scaling requires Redis or sticky sessions  
