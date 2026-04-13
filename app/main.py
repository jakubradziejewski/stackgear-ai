import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.hardware import router as hardware_router
from app.routers.ai import router as ai_router
from app.sockets import sio

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Hardware Hub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(hardware_router)
app.include_router(ai_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Wrap FastAPI with Socket.io — this is what uvicorn actually serves
# ---------------------------------------------------------------------------

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)