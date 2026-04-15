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

---

## Implementation Status & Trade-offs

### ✅ Fully Implemented

- **Authentication** — JWT-based login, bcrypt password hashing, role-based access (admin / standard user), route guards on both frontend and backend
- **Hardware CRUD** — full create, read, update, delete with all business logic guards (cannot rent items in repair or already in use, cannot return available items, only renter or admin can return)
- **Rental engine** — rent/return flow with status transitions, tested with 7 automated pytest tests covering all guard conditions and happy paths
- **Admin panel** — hardware management (add, delete, toggle repair) and user management (list, create, delete) with self-delete guard to prevent admin lockout
- **Real-time updates** — Socket.IO via `python-socketio`; backend emits `hardware_updated` on every state change; all connected clients refresh instantly without polling
- **AI inventory auditor** — Gemini 2.0 Flash analyses full inventory and returns structured findings with severity levels (error / warning / info); correctly flagged all intentional seed anomalies (future date, brand typo, unknown device, safety hazard)
- **Semantic search** — plain-English query mapped to inventory matches via Gemini; integrated into the dashboard search bar
- **Seed data pipeline** — 11 hardware items loaded with intentional anomalies preserved for the auditor demo; validated through Pydantic schemas for consistency
- **Database migrations** — Alembic with autogenerate; migration history committed to the repo
- **Deployment** — backend on Render (Docker), frontend on Vercel, database on Neon PostgreSQL; auto-deploy on push to `main`

---

### ⚡ Shortcuts & Hacks

**1. JWT decoded client-side from localStorage**

The frontend decodes the JWT payload directly in `LoginView.vue` to extract `email`, `is_admin`, and `user_id`, then stores the result in a Pinia store backed by `localStorage`.

- **Why acceptable for MVP:** Eliminates the need for a `/me` endpoint and a round-trip on every page load. JWTs are designed to be readable by the client — the signature is validated server-side on every protected request.
- **Production fix:** Add a `/auth/me` endpoint, store only the raw token in an `httpOnly` cookie (not `localStorage`), and fetch user state server-side on load. `localStorage` is accessible to JavaScript and vulnerable to XSS; `httpOnly` cookies are not.

**2. Admin credentials seeded with a hardcoded fallback**

`seed_users.py` reads the admin password from the `ADMIN_PASSWORD` environment variable but falls back to `"admin123"` if the variable is not set.

- **Why acceptable for MVP:** Seeding runs once manually, not on every deploy. The fallback is only dangerous if the repo is public and the seed is run without setting the env var — both of which are avoidable.
- **Production fix:** Remove the fallback entirely. Fail loudly with a clear error if `ADMIN_PASSWORD` is not set. Enforce a minimum password complexity check before hashing.

**3. Single Render instance with no horizontal scaling**

The app runs on one Render instance. Socket.IO broadcast works correctly only because there is a single process — if a second instance were added, clients connected to different instances would not receive each other's events.

- **Why acceptable for MVP:** The spec targets ~3 concurrent users. One instance handles that comfortably, and free-tier infrastructure doesn't support multi-instance anyway.
- **Production fix:** Add Redis as a Socket.IO message broker (`AsyncRedisManager`). This was actually attempted during development (Entry 106) but caused OOM on 256 MB machines and was rolled back. The correct fix is to provision a Redis instance with adequate memory alongside a paid hosting tier.

**4. Gemini SDK still using the deprecated `google.generativeai` package**

The AI router uses `google.generativeai` which is deprecated in favour of `google.genai`.

- **Why acceptable for MVP:** The deprecated package still works and is not broken. The deprecation warning appears in startup logs but does not affect runtime behaviour.
- **Production fix:** Migrate to `google.genai` following Google's migration guide. This is a low-risk, low-effort refactor that should be done before the package is removed.

**5. No refresh token — JWT expires and forces re-login**

Access tokens expire (configured in `security.py`) with no refresh token flow. When the token expires the user is silently logged out and redirected to login.

- **Why acceptable for MVP:** Short sessions are acceptable for an internal tool demo. The spec does not require persistent sessions.
- **Production fix:** Implement a refresh token stored in an `httpOnly` cookie with a longer expiry. The access token remains short-lived; the refresh token silently issues a new one before expiry.

---

### ⚠️ Partial / Missing

- **No password change or reset flow** — users cannot change their own password; there is no forgot-password or email verification flow
- **No pagination on hardware list** — all items are fetched and rendered in a single request; this will not scale beyond a few hundred items
- **No input sanitisation beyond Pydantic** — Pydantic validates types and formats but there is no explicit XSS or injection protection layer on string fields like `notes`
- **Pydantic v2 deprecation warning** — `class Config` in `config.py` should be migrated to `model_config = ConfigDict(...)` (flagged in Entry 080, not yet fixed)
- **No audit history** — each audit run is stateless; findings are not persisted, so there is no way to compare inventory health over time
- **No rate limiting on AI endpoints** — a user can call `/ai/audit` or `/ai/search` repeatedly and exhaust the Gemini API quota; there is no per-user or per-minute throttle

---

### 🔮 Next Steps — The 24h Roadmap

If there were one more day, the three highest-priority fixes would be:

**1. Move auth tokens to `httpOnly` cookies**
The single biggest security improvement. Replace `localStorage` token storage with `httpOnly` cookies set by the backend on login. Update the frontend to rely on cookies instead of manually attaching `Authorization` headers. This closes the XSS attack surface on the auth layer entirely.

**2. Add rate limiting and Gemini quota handling on AI endpoints**
Add `slowapi` or a simple in-memory rate limiter to `/ai/audit` and `/ai/search`. The Gemini free tier quota is easy to exhaust. A per-user limit of a few requests per minute prevents accidental or malicious quota drain and keeps the feature working during a live demo with multiple evaluators. Also switching models to different ones, or allowing users to use paid models or provide their API keys from the application level would be more efficient.

**3. Persist audit findings to the database**
Currently every audit run is temporary — findings disappear on page reload. Adding an `AuditRun` model with stored audit messages would allow the admin panel to show audit history, trend severity over time, and mark AI findings as resolved. This transforms the auditor from a demo feature into a genuine operational tool. Also automatic Audit run when admin logs in would be beneficial.