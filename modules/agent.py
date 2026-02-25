# modules/agent.py
import yaml
from langchain_core.prompts import ChatPromptTemplate
from modules.llm_handler import LLMHandler
from modules.memory import MemoryManager
from modules.state_manager import StateManager, AgentState

class JarvisAgent:
    def __init__(self, backend="nvidia"):
        self.llm = LLMHandler(backend=backend)
        self.memory = MemoryManager()
        self.state_manager = StateManager()

        # Loading values from your YAML file
        try:
            with open("config/prompts.yaml", "r", encoding="utf-8") as f:
                prompts = yaml.safe_load(f)
        except FileNotFoundError:
            with open("prompts.yaml", "r", encoding="utf-8") as f:
                prompts = yaml.safe_load(f)

        # Build the full prompt using the keys from your YAML
        system_base = prompts.get("system_prompt", "")
        # personalization = prompts.get("personalization_prompt", "")
        # agentic_rules = prompts.get("agentic_instructions", "")
        
        full_system_prompt = f"{system_base}"

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            ("placeholder", "{history}"),
            ("human", "{input}")
        ])
        self.chain = self.prompt | self.llm

    def handle_input(self, user_input: str) -> str:
        if not user_input.strip():
            return "Sir, I require an input to proceed."

        # ReAct State Machine Logic
        self.state_manager.set_state(AgentState.LISTENING)
        self.state_manager.set_state(AgentState.ANALYZING)
        self.state_manager.set_state(AgentState.PLANNING)
        self.state_manager.set_state(AgentState.EXECUTING)
        
        # The Reasoning Loop
        response = self._get_llm_response(user_input)

        self.state_manager.set_state(AgentState.RESPONDING)
        self.state_manager.set_state(AgentState.IDLE)
        return response

    def _get_llm_response(self, user_input: str) -> str:
        try:
            response = self.chain.invoke({
                "input": user_input,
                "history": self.memory.get_messages()
            })
            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(response)
            return response
        except Exception as e:
            return f"I've encountered a glitch in my reasoning circuits, sir: {str(e)}"