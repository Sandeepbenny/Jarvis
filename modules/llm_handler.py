# modules/llm_handler.py

from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage
from langchain_core.prompt_values import PromptValue
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.messages import BaseMessage

import requests
import os
from dotenv import load_dotenv

load_dotenv()


class LLMHandler(Runnable):
    def __init__(self, backend: str = "openai", model: str = None):
        self.backend = backend.lower()
        self.api_key = (
            os.getenv("OPENAI_API_KEY")
            if self.backend == "openai"
            else os.getenv("NVIDIA_API_KEY")
        )

        if not self.api_key:
            raise ValueError(f"API key not found for backend: {self.backend}")

        self.model = model or (
            "gpt-4o-mini" if self.backend == "openai" else "meta/llama3-70b-instruct"
        )

        if self.backend == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)


    def invoke(self, input, config=None):

        # Convert ChatPromptValue → messages
        if isinstance(input, ChatPromptValue):
            messages = input.to_messages()

        elif isinstance(input, list) and all(isinstance(m, BaseMessage) for m in input):
            messages = input

        elif isinstance(input, str):
            messages = [{"role": "user", "content": input}]

        else:
            raise ValueError(f"Unsupported input type: {type(input)}")

        # Convert BaseMessage → JSON serializable dict
        formatted_messages = []
        for m in messages:
            if hasattr(m, "type"):
                role_map = {
                    "human": "user",
                    "ai": "assistant",
                    "system": "system"
                }

                formatted_messages.append({
                    "role": role_map.get(m.type, "user"),
                    "content": m.content
                })
            else:
                formatted_messages.append(m)


        if self.backend == "openai":
            return self._call_openai(formatted_messages)
        elif self.backend == "nvidia":
            return self._call_nvidia(formatted_messages)

    def _call_openai(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": m.type if hasattr(m, "type") else m["role"],
                 "content": m.content if hasattr(m, "content") else m["content"]}
                for m in messages
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def _call_nvidia(self, messages):
        invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": m.type if hasattr(m, "type") else m["role"],
                 "content": m.content if hasattr(m, "content") else m["content"]}
                for m in messages
            ],
            "temperature": 0.7,
        }

        response = requests.post(invoke_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"NVIDIA API error: {response.text}")

        return response.json()["choices"][0]["message"]["content"].strip()