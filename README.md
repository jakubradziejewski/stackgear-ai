# StackGear AI
**Hardware Hub — Full-Stack Inventory Management System**

---

## Overview
StackGear AI is a full-stack hardware inventory management system with:
- Real-time updates (Socket.IO)
- AI-powered inventory auditor and semantic search (Google Gemini)
- Role-based access control (admin / standard user)

---

## Live URLs
- **Frontend:** https://stackgear.vercel.app
- **Backend API:** https://stackgear-ai.onrender.com
- **Health Check:** https://stackgear-ai.onrender.com/health

> ⚠️ The backend runs on Render's free tier and spins down after 15 minutes of inactivity.
> The first request after sleep takes ~30–60 seconds. Open the health check URL before a demo to wake it up.

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
- Pinia
- Socket.IO Client
- Vercel

### AI
- Google Gemini API

### Infrastructure
- Render (free tier, single instance, 512MB RAM)
- Vercel (Hobby)
- Neon (free tier PostgreSQL)

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
└── pyproject.toml
```

---

## Environment Variables

### Backend (Render environment variables)
- `DATABASE_URL` — Neon PostgreSQL connection string
- `SECRET_KEY` — JWT signing secret
- `GEMINI_API_KEY` — Google Gemini API key

### Frontend
```env
VITE_API_URL=https://stackgear-ai.onrender.com
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

### Backend (Render)
Render auto-deploys on every push to `main`. No manual step needed.

To trigger a manual redeploy, go to the Render dashboard and click **Deploy**.

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

---

## Key Architecture Decisions
- CORS must wrap the **outer ASGI app (`socket_app`)**, not the inner FastAPI app — otherwise Socket.IO intercepts preflight OPTIONS requests before CORS can handle them
- Uvicorn must serve `app.main:socket_app`, not `app.main:app`
- Single Render instance prevents Socket.IO broadcast issues (no Redis needed at this scale)
- Neon PostgreSQL ensures shared state across deploys
- Fixed JWT secret ensures token validity across restarts

---

## Known Limits
- Gemini free tier: ~15 requests/minute
- Render free tier: spins down after 15 min inactivity, ~30–60s cold start
- Vercel Hobby: no WebSocket support (Socket.IO connects directly to the Render backend)

---

## Production Notes
- Fully cloud-hosted — no local terminal required after deployment
- Free-tier setup across all three services (Render, Vercel, Neon)
- Wake backend before demos: `https://stackgear-ai.onrender.com/health`

---

## Status
✅ Stable for small-scale usage (~3 concurrent users)  
⚠️ Scaling beyond a single instance requires Redis for Socket.IO broadcast