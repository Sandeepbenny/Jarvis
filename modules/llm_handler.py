# LLMHandler Module

import requests
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMHandler:
    def __init__(self, backend="openai"):
        self.backend = backend
        self.api_key = os.getenv("OPENAI_API_KEY") if backend == "openai" else os.getenv("NVIDIA_API_KEY")

    def process(self, prompt: str) -> str:
        if self.backend == "openai":
            return self._process_openai(prompt)
        elif self.backend == "nvidia":
            return self._process_nvidia(prompt)
        else:
            return "Unsupported backend."

    def _process_openai(self, prompt: str) -> str:
        try:
            openai.api_key = self.api_key
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"OpenAI error: {str(e)}"

    def _process_nvidia(self, prompt: str) -> str:
        try:
            invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            payload = {
                "model": "mistralai/mistral-large-3-675b-instruct-2512",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
                "temperature": 0.15,
                "top_p": 1.00,
                "frequency_penalty": 0.00,
                "presence_penalty": 0.00,
                "stream": False
            }

            response = requests.post(invoke_url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response text.")
            else:
                return f"NVIDIA API error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"NVIDIA API error: {str(e)}"