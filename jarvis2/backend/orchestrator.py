# backend/orchestrator.py
"""
Central execution controller with thread safety.

Improvements over original:
- Thread-safe lock instead of boolean flag
- Structured error handling
- Datetime-serializable state history
- Session management
"""

import threading
from typing import Dict, Any, Optional
from datetime import datetime
from modules.agent import JarvisAgent
from modules.voice_engine import VoiceEngine


class Orchestrator:
    """
    Thread-safe execution controller.
    Manages the lifecycle of each request from input to response.
    """

    def __init__(self, backend: str = "nvidia") -> None:
        self.agent = JarvisAgent(backend=backend)
        self.voice = VoiceEngine()
        self._lock = threading.Lock()
        self._request_count = 0

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    def process_text(self, text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process text input. Thread-safe.
        
        Args:
            text: User input text
            session_id: Optional session identifier for multi-user support
        
        Returns:
            Structured result dict.
        """
        if not text or not text.strip():
            return {"error": "Empty input received."}

        if not self._lock.acquire(blocking=False):
            return {"error": "Jarvis is currently busy. Please wait."}

        try:
            self._request_count += 1
            start = datetime.now()

            # Update memory session if provided
            if session_id:
                self.agent.memory.session_id = session_id

            response = self.agent.handle_input(text)
            elapsed = (datetime.now() - start).total_seconds()

            return {
                "input": text,
                "response": response,
                "state": self.agent.state_manager.get_state().value,
                "elapsed_sec": round(elapsed, 3),
                "request_number": self._request_count,
            }

        except Exception as e:
            return {"error": f"Internal error: {str(e)}"}

        finally:
            self._lock.release()

    def process_voice(self) -> Dict[str, Any]:
        """
        Full voice pipeline: Listen → Process → Speak.
        Thread-safe.
        """
        if not self._lock.acquire(blocking=False):
            return {"error": "Jarvis is currently busy."}

        try:
            start = datetime.now()

            transcript = self.voice.listen()
            if not transcript:
                return {"error": "No speech detected. Please try again."}

            response = self.agent.handle_input(transcript)
            self.voice.speak(response)

            elapsed = (datetime.now() - start).total_seconds()

            return {
                "input": transcript,
                "response": response,
                "state": self.agent.state_manager.get_state().value,
                "elapsed_sec": round(elapsed, 3),
            }

        except Exception as e:
            return {"error": f"Voice processing error: {str(e)}"}

        finally:
            self._lock.release()

    # ─────────────────────────────────────────────────────────
    # Status & Stats
    # ─────────────────────────────────────────────────────────

    def is_busy(self) -> bool:
        """Check if currently processing a request."""
        # Try to acquire without blocking
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self._lock.release()
            return False
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        memory_stats = self.agent.get_memory_stats()
        return {
            "requests_handled": self._request_count,
            "busy": self.is_busy(),
            "current_state": self.agent.state_manager.get_state().value,
            "memory": memory_stats,
        }

    def remember(self, key: str, value: str) -> str:
        """Directly store a user fact in memory."""
        return self.agent.remember(key, value)
