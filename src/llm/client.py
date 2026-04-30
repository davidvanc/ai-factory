import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL_ROUTES = {
    "planner":   "anthropic/claude-opus-4-7",
    "developer": "deepseek/deepseek-v4-flash",
    "developer_premium":  "anthropic/claude-opus-4-7",
    "builder":   "deepseek/deepseek-v4-flash",
    "tester":    "deepseek/deepseek-v4-flash",
    "judge":     "anthropic/claude-sonnet-4-6",
}

# Timeout per rol in seconden
TIMEOUTS = {
    "planner":   180,   # 3 min
    "developer": 600,   # 10 min - grote code outputs
    "builder":   300,   # 5 min
    "developer_premium":  900,   # Opus is trager, geef meer tijd
    "tester":    300,   # 5 min
    "judge":     180,   # 3 min
}

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY niet gevonden in .env")

    def generate(self, prompt: str, role: str = "planner", temperature: float = 0.7, stream: bool = True) -> str:
        model = MODEL_ROUTES.get(role, "anthropic/claude-sonnet-4-6")
        timeout = TIMEOUTS.get(role, 300)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "temperature": temperature,
            "stream": stream,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if not stream:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        # Streaming mode: live tonen wat binnenkomt
        print(f"[{role} via {model}] streaming...", flush=True)
        full_text = ""
        with requests.post(self.base_url, headers=headers, json=payload, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        print(delta, end="", flush=True)
                        full_text += delta
                except (json.JSONDecodeError, KeyError):
                    continue
        print()  # nieuwe regel na streaming
        return full_text
