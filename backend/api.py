# backend/api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.orchestrator import Orchestrator
import time

app = FastAPI(
    title="Jarvis Assistant API",
    version="1.0.0"
)

# Single shared orchestrator instance
orchestrator = Orchestrator()


# ----------------------------------------
# Request Models
# ----------------------------------------

class TextRequest(BaseModel):
    text: str


# ----------------------------------------
# Health Check
# ----------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "busy": orchestrator.is_busy()
    }


# ----------------------------------------
# Text Endpoint
# ----------------------------------------

@app.post("/text")
def process_text(request: TextRequest):
    """
    Process text input.
    """

    start_time = time.time()

    result = orchestrator.process_text(request.text)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    execution_time = round(time.time() - start_time, 3)

    return {
        "input": result["input"],
        "response": result["response"],
        "state": result["state"],
        "execution_time_sec": execution_time
    }


# ----------------------------------------
# Voice Endpoint
# ----------------------------------------

@app.post("/voice")
def process_voice():
    """
    Trigger voice lifecycle:
    Listen -> Process -> Speak
    """

    start_time = time.time()

    result = orchestrator.process_voice()

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    execution_time = round(time.time() - start_time, 3)

    return {
        "input": result["input"],
        "response": result["response"],
        "state": result["state"],
        "execution_time_sec": execution_time
    }