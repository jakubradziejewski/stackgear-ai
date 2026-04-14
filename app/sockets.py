import os
import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)

@sio.event
async def connect(sid, environ):
    print(f"[socket] client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[socket] client disconnected: {sid}")