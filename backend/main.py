"""Mona AI Assistant - FastAPI backend.

Serves the React frontend and provides WebSocket/REST endpoints for
AI-powered business database queries using Claude with tool_use.
"""

import json
import mimetypes
import os
import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import unquote

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import asyncio

from chat import ChatManager
from location_cache import get_names
from db.query_log import init_db, get_recent_queries, get_stats

# Load .env from project root (parent of backend/)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# In-memory session store
sessions: dict[str, ChatManager] = {}


def get_or_create_session(session_id: str) -> ChatManager:
    """Get an existing session or create a new one."""
    if session_id not in sessions:
        sessions[session_id] = ChatManager(session_id)
    return sessions[session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()
    print("\n  Mona is running at http://0.0.0.0:8081\n")
    yield
    sessions.clear()


app = FastAPI(
    title="Mona AI Assistant",
    description="AI-powered business analyst for Monumental Markets",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST Endpoints ---


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Mona AI Assistant",
        "active_sessions": len(sessions),
    }


@app.get("/api/locations")
async def get_locations():
    """Return cached location and account names for frontend suggestions."""
    return get_names()


@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 50):
    """Recent tool calls with conversation context."""
    return await asyncio.to_thread(get_recent_queries, limit)


@app.get("/api/logs/stats")
async def get_log_stats():
    """Usage statistics: queries by database, daily usage, top questions."""
    return await asyncio.to_thread(get_stats)


# SharePoint file download
_SHAREPOINT_ROOT = os.getenv("SHAREPOINT_ROOT", "")
_ALLOWED_LIBRARIES = [
    "Business Intelligence - Documents",
    "Customer Operations - Documents",
    "Standards & Process - Documents",
]


@app.get("/api/files/{file_path:path}")
async def download_file(file_path: str):
    """Serve a file from the SharePoint-synced folder for download."""
    if not _SHAREPOINT_ROOT:
        raise HTTPException(status_code=500, detail="SharePoint not configured")

    decoded_path = unquote(file_path)
    root = Path(_SHAREPOINT_ROOT)
    full_path = (root / decoded_path).resolve()

    # Security: path must stay within SharePoint root
    if not str(full_path).startswith(str(root.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    # Must be within an allowed library
    rel_to_root = str(full_path.relative_to(root.resolve()))
    if not any(rel_to_root.startswith(lib) for lib in _ALLOWED_LIBRARIES):
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(full_path))

    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type=media_type or "application/octet-stream",
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint. Collects full response before returning."""
    session_id = request.session_id or str(uuid.uuid4())
    manager = get_or_create_session(session_id)

    try:
        chunks = []
        async for event in manager.send_message(request.message):
            if event.get("type") == "chunk":
                chunks.append(event["content"])

        return ChatResponse(
            response="".join(chunks),
            session_id=session_id,
        )
    except Exception as e:
        logger.exception("Error in chat endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    manager = sessions[session_id]
    return {
        "session_id": session_id,
        "history": manager.get_history(),
        "created_at": manager.created_at,
    }


# --- WebSocket Endpoint ---


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat.

    Protocol:
    - Client sends JSON: {"message": "user text", "session_id": "optional-id"}
    - Server streams JSON events:
      - {"type": "chunk", "content": "text chunk"}
      - {"type": "status", "content": "Querying database..."}
      - {"type": "done", "session_id": "id"}
      - {"type": "error", "content": "error message"}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue

            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue

            session_id = data.get("session_id") or str(uuid.uuid4())
            manager = get_or_create_session(session_id)

            try:
                async for event in manager.send_message(message):
                    # Forward structured events directly to client
                    await websocket.send_json(event)

                await websocket.send_json({
                    "type": "done",
                    "session_id": session_id,
                })

            except Exception as e:
                logger.exception("Error during chat streaming")
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.exception("WebSocket error")


# --- Static Files (React build) ---

# Serve React build if it exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA - all non-API routes return index.html."""
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )
