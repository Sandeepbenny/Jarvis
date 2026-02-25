# Prompt Manager Module

from langchain_core.prompts import ChatPromptTemplate
import yaml

class PromptManager:
    def __init__(self, prompt_file="config/prompts.yaml"):
        self.prompt_file = prompt_file
        self.prompts = self._load_prompts()

    def _load_prompts(self):
        try:
            with open(self.prompt_file, "r") as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise RuntimeError(f"Failed to load prompts: {str(e)}")

    def get_prompt(self, prompt_type):
        return ChatPromptTemplate.from_template(self.prompts.get(prompt_type, ""))

# Example usage:
# prompt_manager = PromptManager()
# system_prompt = prompt_manager.get_prompt("system_prompt")