# modules/agent.py

from langchain_core.prompts import ChatPromptTemplate
from modules.llm_handler import LLMHandler
from modules.memory import MemoryManager
from modules.state_manager import StateManager, AgentState
import yaml



class JarvisAgent:
    def __init__(self, backend="openai"):
        self.llm = LLMHandler(backend=backend)
        self.memory = MemoryManager()
        self.state_manager = StateManager()

        with open("config/prompts.yaml", "r") as f:
            prompts = yaml.safe_load(f)

        system_prompt = prompts["system_prompt"]
        personalization_prompt = prompts["personalization_prompt"]

        full_system_prompt = system_prompt

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            ("placeholder", "{history}"),
            ("human", "{input}")
        ])
        self.chain = self.prompt | self.llm

    def handle_input(self, user_input: str) -> str:
        if not user_input.strip():
            return "Please enter a valid message."

        # Check if agent can accept input
        if not self.state_manager.can_accept_input():
            return "Agent is currently busy. Please wait."

        # State-driven execution pipeline
        self.state_manager.set_state(AgentState.LISTENING)
        self.state_manager.set_context("user_input", user_input)

        self.state_manager.set_state(AgentState.ANALYZING)
        intent = self._analyze_input(user_input)
        self.state_manager.set_context("intent", intent)

        self.state_manager.set_state(AgentState.PLANNING)
        action = self._plan_action(intent)
        self.state_manager.set_context("action", action)

        self.state_manager.set_state(AgentState.EXECUTING)
        if action == "chat":
            response = self._chat(user_input)
        elif action == "task":
            response = self._handle_task(user_input)
        else:
            response = "Unknown action."

        self.state_manager.set_state(AgentState.RESPONDING)
        self.state_manager.set_state(AgentState.LEARNING)
        self.state_manager.set_state(AgentState.IDLE)

        return response

    def _analyze_input(self, user_input: str) -> str:
        """Analyze user input to determine intent"""
        # Simple intent detection - can be enhanced with NLP
        if any(keyword in user_input.lower() for keyword in ["task", "do", "execute", "run"]):
            return "task_request"
        return "chat_request"

    def _plan_action(self, intent: str) -> str:
        """Plan the action based on intent"""
        if intent == "task_request":
            return "task"
        return "chat"

    def _chat(self, user_input: str) -> str:
        try:
            response = self.chain.invoke({
                "input": user_input,
                "history": self.memory.get_messages()
            })

            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(response)

            return response

        except Exception as e:
            return f"[Agent Error] {str(e)}"

    def _handle_task(self, user_input: str) -> str:
        return f"Executing task: {user_input}"