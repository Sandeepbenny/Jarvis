# Agent Module

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from modules.llm_handler import LLMHandler
from modules.state_manager import StateManager

class JarvisAgent:
    def __init__(self, backend="nvidia"):
        self.llm_handler = LLMHandler(backend=backend)
        self.memory = ConversationBufferMemory()
        self.state_manager = StateManager()
        self.conversation_chain = ConversationChain(memory=self.memory, llm=self.llm_handler)

    def handle_input(self, user_input: str) -> str:
        # Check the current state
        state = self.state_manager.get_state()

        # Process input based on state
        if state == "idle":
            return self.conversation_chain.run(user_input)
        elif state == "task_execution":
            return self._handle_task(user_input)
        else:
            return "Unknown state."

    def _handle_task(self, user_input: str) -> str:
        # Placeholder for task execution logic
        return f"Executing task: {user_input}"