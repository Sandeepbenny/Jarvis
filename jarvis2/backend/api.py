# backend/api.py
"""
FastAPI backend for Jarvis.

Endpoints:
  GET  /           → Frontend
  GET  /health     → Health check + stats
  POST /text       → Process text input
  POST /voice      → Trigger voice pipeline
  POST /remember   → Store user facts
  GET  /memory     → Get memory stats
  DELETE /memory   → Clear conversation history
"""

import os
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from backend.orchestrator import Orchestrator

app = FastAPI(
    title="Jarvis Personal Assistant",
    description="AI-powered personal assistant with tool use, memory, and voice",
    version="2.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()

# ─────────────────────────────────────────────────────────────────
# Frontend serving
# ─────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Jarvis API is running. Frontend not found."}


# ─────────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="User input text")
    session_id: Optional[str] = Field(None, description="Optional session ID for multi-user")


class RememberRequest(BaseModel):
    key: str = Field(..., description="Fact key (e.g., 'name', 'location')")
    value: str = Field(..., description="Fact value")


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check with system stats."""
    return {
        "status": "operational",
        **orchestrator.get_stats()
    }


@app.post("/text")
def process_text(request: TextRequest):
    """
    Send a text message to Jarvis and get a response.
    Jarvis will use tools if needed (web search, file ops, etc.)
    """
    result = orchestrator.process_text(request.text, session_id=request.session_id)

    if "error" in result:
        status_code = 503 if "busy" in result["error"].lower() else 400
        raise HTTPException(status_code=status_code, detail=result["error"])

    return result


@app.post("/voice")
def process_voice():
    """
    Trigger the voice input pipeline.
    Jarvis will listen via microphone, process, and speak the response.
    """
    result = orchestrator.process_voice()

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/remember")
def remember_fact(request: RememberRequest):
    """Store a user fact in Jarvis's long-term memory."""
    response = orchestrator.remember(request.key, request.value)
    return {"message": response, "key": request.key, "value": request.value}


@app.get("/memory")
def get_memory():
    """Get memory statistics and stored facts."""
    agent = orchestrator.agent
    return {
        "stats": agent.memory.get_stats(),
        "facts": agent.memory.get_all_facts(),
        "recent_episodes": agent.memory.get_episodes(limit=5),
    }


@app.delete("/memory/session")
def clear_session():
    """Clear the current conversation session history."""
    orchestrator.agent.memory.clear_session()
    return {"message": "Session cleared. Long-term memory preserved."}


@app.get("/tools")
def list_tools():
    """List all available tools Jarvis can use."""
    from modules.agent import ALL_TOOLS
    return {
        "tool_count": len(ALL_TOOLS),
        "tools": [
            {
                "name": t.name,
                "description": t.description[:120] + "..." if len(t.description) > 120 else t.description,
            }
            for t in ALL_TOOLS
        ]
    }
