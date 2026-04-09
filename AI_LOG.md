# AI Log — Hardware Hub (stackgear-ai)

---

## Entry 001
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Stack review and recommendations for Hardware Hub
**What you provided:** Confirmed Vue.js + FastAPI + Neon/Postgres + SQLAlchemy + JWT + bcrypt + Vercel/Fly.io is solid; recommended adding Alembic, asyncpg, PyJWT, Pinia, Vue Router, Vite, Axios, pytest+httpx
**Problem/Correction:** None
**My takeaway:** Stack is production-ready; key additions are Alembic for migrations and asyncpg for async Postgres

---

## Entry 002
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Whether SQLModel is better than SQLAlchemy
**What you provided:** SQLModel is built on top of SQLAlchemy, not a replacement; recommended sticking with SQLAlchemy 2.0 due to SQLModel's immaturity, async bugs, and Alembic friction
**Problem/Correction:** None
**My takeaway:** SQLAlchemy 2.0 is the safer choice for a deliverable project — SQLModel's reduced boilerplate isn't worth the async and migration risks

---

## Entry 003
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Which package manager to use and confirmation all libraries are available
**What you provided:** Confirmed uv is the right modern choice; full availability check of all dependencies; recommended project folder structure with services/ layer for testable business logic
**Problem/Correction:** None
**My takeaway:** uv for package management; services/ layer keeps business logic separate from routers and independently testable

---

## Entry 004
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Help fixing uv install errors on Windows
**What you provided:** Two issues — wrong working directory (was in C:\) and PowerShell not supporting bash backslash line continuation; provided corrected Windows commands
**Problem/Correction:** Initial commands were written for bash, should have provided PowerShell alternatives from the start
**My takeaway:** On Windows/PowerShell use one long command or backtick for line continuation; always cd into project folder before uv add

---

## Entry 005
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** What --dev dependencies are and what the flag does
**What you provided:** Explanation of dev vs production dependency separation in pyproject.toml and why it matters for deployment size
**Problem/Correction:** None
**My takeaway:** --dev keeps testing tools out of production container; deploy with uv sync --no-dev

---

## Entry 006
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** What to initialize first to get the project in proper order
**What you provided:** Step-by-step scaffold — folder structure, __init__.py files, .env + .env.example, .gitignore, Alembic init, core file creation, git init
**Problem/Correction:** None
**My takeaway:** Scaffold and commit before writing any logic; __init__.py makes folders importable Python packages

---

## Entry 007
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Why .env.example is needed and what Alembic init actually created
**What you provided:** .env.example is a committed public template documenting what secrets the app needs; breakdown of every Alembic file and the revision → upgrade head workflow
**Problem/Correction:** None
**My takeaway:** .env.example documents required secrets without exposing values; Alembic versions/ folder is the migration history — treat it like source code

---

## Entry 008
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** How Alembic compares to DVC and what to commit from it
**What you provided:** Alembic is schema version control not data versioning like DVC; everything in alembic/ including versions/ should be committed; DB URL override in env.py keeps credentials safe
**Problem/Correction:** None
**My takeaway:** Commit all of Alembic; blank sqlalchemy.url in alembic.ini is intentional and correct

---

## Entry 009
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Alembic vs Prisma comparison, then continue building core files
**What you provided:** Side-by-side comparison; implementation of config.py, database.py, security.py, main.py with health check endpoint
**Problem/Correction:** None
**My takeaway:** Prisma is a complete integrated solution for JS/TS; SQLAlchemy + Alembic is the Python equivalent but requires more manual wiring

---

## Entry 010
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Deep explanation of Pydantic, database.py, security.py, main.py, and Uvicorn
**What you provided:** Line-by-line breakdown of all four files; Pydantic validation flow, JWT sign/verify cycle, bcrypt hashing, CORS, and Uvicorn as the network layer beneath FastAPI
**Problem/Correction:** None
**My takeaway:** Pydantic validates data shapes including env vars; JWTs are signed strings proving identity without DB lookups; Uvicorn is the network layer FastAPI sits behind

---

## Entry 011
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Whether Pydantic settings can leak env vars, whether jose does validation, SQLAlchemy + Neon connection details, and middleware deep dive
**What you provided:** Actual leak vectors are your own code and git hygiene not Pydantic itself; jose validates signature + expiry + algorithm on decode; Neon needs pool_pre_ping=True for cold starts; middleware pros/cons and rule that business logic doesn't belong there
**Problem/Correction:** None
**My takeaway:** Use direct Neon connection string with pool_pre_ping; middleware is for cross-cutting concerns only

---

## Entry 012
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Whether to enable Neon's connection pooling
**What you provided:** Use direct connection for Fly.io + SQLAlchemy; Neon's PgBouncer pooler is designed for serverless only; two competing pool managers causes bugs
**Problem/Correction:** None
**My takeaway:** Direct connection string for persistent servers; Neon pooler only for Lambda/Edge functions

---

## Entry 013
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Help fixing `sslmode` unexpected keyword argument error
**What you provided:** asyncpg uses connect_args={"ssl": "require"} not URL sslmode parameter; strip everything after ? from Neon connection string
**Problem/Correction:** Initial database.py didn't account for asyncpg's different SSL syntax vs psycopg2
**My takeaway:** Strip ?sslmode=require&channel_binding=require from Neon URL; handle SSL via connect_args in the engine

---

## Entry 014
**Date:** 2026-04-09
**Tool:** Claude
**What I asked for:** Whether sqlalchemy.url in alembic.ini needs a value and what to commit from Alembic
**What you provided:** Leave blank — env.py overrides it at runtime from .env via pydantic settings; commit everything in alembic/ including versions/
**Problem/Correction:** None
**My takeaway:** Blank sqlalchemy.url is correct and intentional; all Alembic files are safe to commit because secrets stay in .env