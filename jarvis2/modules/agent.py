# modules/agent.py
"""
Jarvis Agent — LangGraph-powered ReAct agent.

Architecture:
    User Input
        │
        ▼
    [ROUTER] ─── simple query ──► [LLM] ──► Response
        │
        └── needs tools ──► [TOOL_AGENT] ─► [TOOLS] ─► [LLM] ──► Response
                                │                          │
                                └──────── loop ────────────┘
                                    (until done or max steps)
"""

import yaml
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict, Annotated
from pathlib import Path
from datetime import datetime

from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from modules.memory.persistent_memory import PersistentMemory
from modules.state_manager import StateManager, AgentState
from modules.llm_handler import LLMHandler

# Import all tools
from modules.tools.system_tools import (
    open_application, close_application, get_running_processes,
    take_screenshot, type_text, press_key,
    get_clipboard, set_clipboard, get_system_info,
    lock_screen, shutdown_system, restart_system,
)
from modules.tools.file_tools import (
    read_file, write_file, list_directory, create_directory,
    delete_file, move_file, copy_file, search_files,
    get_file_info, zip_files,
)
from modules.tools.web_tools import (
    web_search, fetch_webpage, get_weather, get_news,
)
from modules.tools.media_tools import (
    play_music, pause_music, stop_music, set_volume, get_volume,
)
from modules.tools.productivity_tools import (
    get_calendar_events, create_calendar_event,
    send_email, get_emails,
    create_note, get_notes,
    set_reminder, get_reminders,
)
from modules.tools.code_tools import (
    run_python_code, run_shell_command, install_package,
)

# ─────────────────────────────────────────────────────────────────
# All available tools
# ─────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    # System
    open_application, close_application, get_running_processes,
    take_screenshot, type_text, press_key,
    get_clipboard, set_clipboard, get_system_info,
    lock_screen, shutdown_system, restart_system,
    # Files
    read_file, write_file, list_directory, create_directory,
    delete_file, move_file, copy_file, search_files,
    get_file_info, zip_files,
    # Web
    web_search, fetch_webpage, get_weather, get_news,
    # Media
    play_music, pause_music, stop_music, set_volume, get_volume,
    # Productivity
    get_calendar_events, create_calendar_event,
    send_email, get_emails,
    create_note, get_notes,
    set_reminder, get_reminders,
    # Code
    run_python_code, run_shell_command, install_package,
]


# ─────────────────────────────────────────────────────────────────
# LangGraph State
# ─────────────────────────────────────────────────────────────────

class JarvisState(TypedDict):
    """The state that flows through the LangGraph graph."""
    messages: Annotated[List[BaseMessage], add_messages]  # Full message list
    user_input: str                                         # Raw user input
    response: str                                           # Final response
    tool_calls_made: int                                    # Safety counter
    error: Optional[str]                                    # Error if any


MAX_TOOL_ITERATIONS = 10  # Prevent infinite loops


# ─────────────────────────────────────────────────────────────────
# Jarvis Agent
# ─────────────────────────────────────────────────────────────────

class JarvisAgent:
    """
    Production-ready Jarvis agent using LangGraph's ReAct pattern.
    
    Graph:
        START → agent_node → [END | tools_node] → agent_node → ...
    
    The agent_node calls the LLM. If the LLM wants to call tools,
    we route to tools_node which executes them and adds results to messages.
    The loop continues until the LLM gives a final text response.
    """

    def __init__(self, backend: str = "nvidia"):
        self.backend = backend
        self.state_manager = StateManager()
        self.memory = PersistentMemory()
        
        # Load the LLM (returns raw string, we wrap it for tool calling)
        self.llm_handler = LLMHandler(backend=backend)
        
        # Get the LLM client with tool binding
        self._llm_with_tools = self._build_llm_with_tools()
        
        # Load prompts
        self.system_prompt = self._load_system_prompt()
        
        # Build the LangGraph graph
        self.graph = self._build_graph()

    def _build_llm_with_tools(self):
        """Create the LLM client with tools bound to it."""
        if self.backend == "openai":
            from langchain_openai import ChatOpenAI
            import os
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.7,
            )
        else:
            # NVIDIA via OpenAI-compatible endpoint
            from langchain_openai import ChatOpenAI
            import os
            llm = ChatOpenAI(
                model="meta/llama-3.1-70b-instruct",
                api_key=os.getenv("NVIDIA_API_KEY"),
                base_url="https://integrate.api.nvidia.com/v1",
                temperature=0.7,
            )
        
        return llm.bind_tools(ALL_TOOLS)

    def _load_system_prompt(self) -> str:
        """Load system prompt from YAML config."""
        for path in ["config/prompts.yaml", "prompts.yaml"]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    prompts = yaml.safe_load(f)
                    return prompts.get("system_prompt", self._default_system_prompt())
            except FileNotFoundError:
                continue
        return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return """You are Jarvis, a highly capable personal AI assistant running locally on the user's computer.

You have access to powerful tools to help the user:
- Control their computer (open/close apps, take screenshots, control keyboard)
- Manage files and folders
- Search the web and fetch information
- Control media playback and system volume
- Manage calendar events and emails
- Set reminders and take notes
- Execute code and shell commands

Personality:
- Professional, witty, and efficient — like Iron Man's Jarvis
- Proactive: suggest solutions the user didn't think of
- Concise in responses, but thorough in actions
- Always confirm before destructive operations (delete, shutdown, etc.)

When using tools:
- Choose the right tool for the task
- Chain multiple tools when needed (e.g., search then fetch, then summarize)
- Report what you did and what the result was
- If a tool fails, try an alternative approach

{memory_context}
"""

    def _build_graph(self) -> Any:
        """Build the LangGraph ReAct agent graph."""
        
        # Tool execution node (LangGraph built-in)
        tool_node = ToolNode(ALL_TOOLS)

        def agent_node(state: JarvisState) -> JarvisState:
            """
            The main LLM node. Decides whether to call tools or give final response.
            """
            # Build system message with memory context
            memory_ctx = self.memory.get_memory_context()
            sys_prompt = self.system_prompt.format(
                memory_context=f"\n{memory_ctx}" if memory_ctx else ""
            )
            
            messages = [SystemMessage(content=sys_prompt)] + state["messages"]
            
            response = self._llm_with_tools.invoke(messages)
            
            return {
                **state,
                "messages": [response],
                "tool_calls_made": state.get("tool_calls_made", 0),
            }

        def should_continue(state: JarvisState) -> Literal["tools", "end"]:
            """Router: did the LLM call tools, or give a final answer?"""
            last_message = state["messages"][-1]
            
            # Check tool call count to prevent infinite loops
            tool_calls_made = state.get("tool_calls_made", 0)
            if tool_calls_made >= MAX_TOOL_ITERATIONS:
                return "end"
            
            # If the last AI message has tool_calls, route to tools
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            
            return "end"

        def tool_node_with_counter(state: JarvisState) -> JarvisState:
            """Wrap tool node to count iterations."""
            result = tool_node.invoke(state)
            return {
                **result,
                "tool_calls_made": state.get("tool_calls_made", 0) + 1,
            }

        def extract_response(state: JarvisState) -> JarvisState:
            """Extract the final text response from the last message."""
            last_message = state["messages"][-1]
            response = getattr(last_message, "content", str(last_message))
            return {**state, "response": response}

        # Build the graph
        builder = StateGraph(JarvisState)
        
        builder.add_node("agent", agent_node)
        builder.add_node("tools", tool_node_with_counter)
        builder.add_node("extract", extract_response)
        
        builder.set_entry_point("agent")
        
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": "extract",
            }
        )
        
        builder.add_edge("tools", "agent")
        builder.add_edge("extract", END)
        
        return builder.compile()

    def handle_input(self, user_input: str) -> str:
        """
        Main entry point. Process user input through the LangGraph agent.
        
        Args:
            user_input: Raw text from the user
        
        Returns:
            Jarvis's response as a string
        """
        if not user_input.strip():
            return "I require an input to proceed, sir."

        # Update state machine
        self.state_manager.set_state(AgentState.LISTENING)
        self.state_manager.set_state(AgentState.ANALYZING)
        
        # Get conversation history from persistent memory
        history = self.memory.get_messages(limit=20)
        
        # Initial state for the graph
        initial_state: JarvisState = {
            "messages": history + [HumanMessage(content=user_input)],
            "user_input": user_input,
            "response": "",
            "tool_calls_made": 0,
            "error": None,
        }

        try:
            self.state_manager.set_state(AgentState.PLANNING)
            self.state_manager.set_state(AgentState.EXECUTING)
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            response = final_state.get("response", "I encountered an issue processing that.")
            
            # Persist the conversation turn
            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(response)
            
            self.state_manager.set_state(AgentState.RESPONDING)
            self.state_manager.set_state(AgentState.IDLE)
            
            return response

        except Exception as e:
            self.state_manager.current_state = AgentState.ERROR
            self.state_manager.set_state(AgentState.IDLE)
            return f"I've encountered an error in my systems, sir: {str(e)}"

    def remember(self, key: str, value: str) -> str:
        """Explicitly store a fact about the user."""
        self.memory.remember_fact(key, value)
        return f"Noted, sir. I'll remember that your {key} is {value}."

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self.memory.get_stats()
