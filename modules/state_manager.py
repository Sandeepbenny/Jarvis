# State Manager Module
from enum import Enum
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from abc import ABC, abstractmethod


class StateHandler(ABC):
    """Abstract base class for state-specific behavior handlers"""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute state-specific logic and return updated context"""
        pass


class AgentState(Enum):
    """Enumeration of possible agent states"""
    IDLE = "idle"                          # Waiting for user input
    LISTENING = "listening"                # Receiving user input
    ANALYZING = "analyzing"                # Analyzing the input
    PLANNING = "planning"                  # Planning actions/tasks
    EXECUTING = "executing"                # Executing tasks
    TOOL_CALLING = "tool_calling"          # Calling external tools/APIs
    RESPONDING = "responding"              # Generating response
    ERROR = "error"                        # Error state
    LEARNING = "learning"                  # Learning from interaction


class StateManager:
    """
    Manages the state transitions and context of the Jarvis Agent.
    Enables agentic behavior through state-driven execution.
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS = {
        AgentState.IDLE: [AgentState.LISTENING, AgentState.ERROR],
        AgentState.LISTENING: [AgentState.ANALYZING, AgentState.ERROR],
        AgentState.ANALYZING: [AgentState.PLANNING, AgentState.RESPONDING, AgentState.ERROR],
        AgentState.PLANNING: [AgentState.EXECUTING, AgentState.RESPONDING, AgentState.ERROR],
        AgentState.EXECUTING: [AgentState.RESPONDING, AgentState.TOOL_CALLING, AgentState.ERROR],
        AgentState.TOOL_CALLING: [AgentState.EXECUTING, AgentState.RESPONDING, AgentState.ERROR],
        AgentState.RESPONDING: [AgentState.LEARNING, AgentState.IDLE, AgentState.ERROR],
        AgentState.LEARNING: [AgentState.IDLE, AgentState.ERROR],
        AgentState.ERROR: [AgentState.IDLE, AgentState.ANALYZING],
    }

    def __init__(self):
        self.current_state = AgentState.IDLE
        self.previous_state = None
        self.state_history = []
        self.context = {}  # Stores state-specific context
        self.timestamp = datetime.now()

    def get_state(self) -> AgentState:
        """Get the current state"""
        return self.current_state

    def set_state(self, new_state: AgentState) -> bool:
        """
        Set the state with validation of valid transitions.
        Returns True if transition is valid, False otherwise.
        """
        if new_state not in self.VALID_TRANSITIONS.get(self.current_state, []):
            print(f"Invalid transition: {self.current_state.value} -> {new_state.value}")
            return False

        self.previous_state = self.current_state
        self.current_state = new_state
        self.timestamp = datetime.now()
        
        # Record state history
        self.state_history.append({
            "state": new_state.value,
            "timestamp": self.timestamp,
            "context": self.context.copy()
        })
        
        # print(f"[State Transition] {self.previous_state.value} -> {self.current_state.value}")
        return True

    def set_context(self, key: str, value: Any) -> None:
        """Store context information for the current state"""
        self.context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve context information"""
        return self.context.get(key)

    def clear_context(self) -> None:
        """Clear all context"""
        self.context = {}

    def get_state_history(self) -> list:
        """Get the history of state transitions"""
        return self.state_history

    def is_busy(self) -> bool:
        """Check if the agent is actively processing"""
        busy_states = [
            AgentState.LISTENING, AgentState.ANALYZING, 
            AgentState.PLANNING, AgentState.EXECUTING, 
            AgentState.TOOL_CALLING, AgentState.RESPONDING
        ]
        return self.current_state in busy_states

    def can_accept_input(self) -> bool:
        """Check if the agent can accept new input"""
        return self.current_state in [AgentState.IDLE, AgentState.RESPONDING]

    def reset(self) -> None:
        """Reset the state manager to initial state"""
        self.current_state = AgentState.IDLE
        self.previous_state = None
        self.context = {}
        self.timestamp = datetime.now()