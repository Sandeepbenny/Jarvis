# backend/api.py

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.orchestrator import Orchestrator
import time
import os

app = FastAPI(
    title="Jarvis Assistant",
    version="1.0.0"
)

orchestrator = Orchestrator()

# ----------------------------------------
# Serve Frontend
# ----------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ----------------------------------------
# Request Models
# ----------------------------------------

class TextRequest(BaseModel):
    text: str


# ----------------------------------------
# Health
# ----------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "busy": orchestrator.is_busy()
    }


# ----------------------------------------
# Text Endpoint
# ----------------------------------------

@app.post("/text")
def process_text(request: TextRequest):

    start = time.time()

    result = orchestrator.process_text(request.text)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "input": result["input"],
        "response": result["response"],
        "state": result["state"],
        "execution_time_sec": round(time.time() - start, 3)
    }


# ----------------------------------------
# Voice Endpoint (kept for later)
# ----------------------------------------

@app.post("/voice")
def process_voice():

    start = time.time()

    result = orchestrator.process_voice()

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "input": result["input"],
        "response": result["response"],
        "state": result["state"],
        "execution_time_sec": round(time.time() - start, 3)
    }