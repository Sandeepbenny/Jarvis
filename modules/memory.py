# Memory Module

from langchain.memory import ConversationBufferMemory

class MemoryManager:
    def __init__(self):
        self.memory = ConversationBufferMemory()

    def add_message(self, role: str, content: str):
        self.memory.chat_memory.add_message(role=role, content=content)

    def get_memory(self):
        return self.memory.chat_memory.messages

    def clear_memory(self):
        self.memory.chat_memory.clear()