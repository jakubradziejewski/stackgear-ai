"""
app/sockets.py

Socket.io server.
Import `sio` here and call `sio.emit("hardware_updated")` from any router
whenever hardware state changes (rent, return, repair toggle, add, delete).
"""

import socketio

# async_mode="asgi" means it runs inside uvicorn alongside FastAPI
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