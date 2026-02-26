# backend/orchestrator.py

from typing import Dict, Any
from modules.agent import JarvisAgent
from modules.voice_engine import VoiceEngine


class Orchestrator:
    """
    Central execution controller.

    Responsible for:
    - Enforcing single active request
    - Routing text / voice input
    - Managing execution lifecycle
    - Returning structured responses (UI-ready)
    """

    def __init__(self) -> None:
        self.agent = JarvisAgent(backend="nvidia")
        self.voice = VoiceEngine()

        self._busy: bool = False

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text input synchronously.
        Safe for terminal or future API usage.
        """

        if not text or not text.strip():
            return {"error": "Empty input."}

        if self._busy:
            return {"error": "Jarvis is currently busy."}

        try:
            self._busy = True

            response = self.agent.handle_input(text)

            return {
                "input": text,
                "response": response,
                "state": self.agent.state_manager.get_state().value,
                "history": self.agent.state_manager.get_state_history(),
            }

        finally:
            self._busy = False

    def process_voice(self) -> Dict[str, Any]:
        """
        Trigger voice lifecycle:
        Listen -> Process -> Speak
        """

        if self._busy:
            return {"error": "Jarvis is currently busy."}

        try:
            self._busy = True

            transcript = self.voice.listen()

            if not transcript:
                return {"error": "No speech detected."}

            response = self.agent.handle_input(transcript)

            # Speak response
            self.voice.speak(response)

            return {
                "input": transcript,
                "response": response,
                "state": self.agent.state_manager.get_state().value,
                "history": self.agent.state_manager.get_state_history(),
            }

        finally:
            self._busy = False

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def is_busy(self) -> bool:
        return self._busy