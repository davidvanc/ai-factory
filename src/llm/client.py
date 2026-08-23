import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# De "~"-ids zijn OpenRouter-aliassen die automatisch naar de nieuwste versie
# wijzen. Bijgewerkt 2026-08-23: opus-4.7 -> opus-5, sonnet-4.6 -> sonnet-5
# (nieuwer en een derde goedkoper), deepseek vastgezet -> latest.
MODEL_ROUTES = {
    "planner":   "~anthropic/claude-opus-latest",
    "developer": "~google/gemini-pro-latest",
    "developer_premium":  "~anthropic/claude-opus-latest",
    "builder":   "~deepseek/deepseek-v4-flash-latest",
    "tester":    "~deepseek/deepseek-v4-flash-latest",
    "judge":     "~anthropic/claude-sonnet-latest",
    "consultant_scientific": "~google/gemini-pro-latest",
}

# Timeout per rol in seconden
TIMEOUTS = {
    "planner":   180,   # 3 min
    "developer": 600,   # 15 min - grote code outputs
    "builder":   300,   # 5 min
    "developer_premium":  900,   # Opus is trager, geef meer tijd
    "tester":    300,   # 5 min
    "consultant_scientific": 120, #  2 min
    "judge":     180,   # 3 min
}

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY niet gevonden in .env")

    def generate(self, prompt: str, role: str = "planner", temperature: float = 0.7, stream: bool = True) -> str:
        model = MODEL_ROUTES.get(role, "~anthropic/claude-sonnet-latest")
        timeout = TIMEOUTS.get(role, 300)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Bepaal of dit model caching ondersteunt
        # Anthropic (Claude) en Google (Gemini) ondersteunen prompt caching via OpenRouter
        supports_caching = (
            model.startswith("anthropic/") or
            model.startswith("~anthropic/") or
            model.startswith("google/") or
            model.startswith("~google/")
        )

        if supports_caching and len(prompt) > 1024:
            # Cache het grootste deel van de prompt; alleen laatste 200 chars vers
            cache_split = max(0, len(prompt) - 200)
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt[:cache_split],
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": prompt[cache_split:]
                    }
                ]
            }]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": model,
            "temperature": temperature,
            "stream": stream,
            "max_tokens": 32000,
            "messages": messages
        }
        if not stream:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        # Streaming mode: live tonen wat binnenkomt
        print(f"[{role} via {model}] streaming...", flush=True)
        full_text = ""
        last_chunk_time = time.time()
        idle_timeout = 90  # max 90s zonder nieuwe data

        with requests.post(self.base_url, headers=headers, json=payload, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=False):
                # Idle timeout check
                if time.time() - last_chunk_time > idle_timeout:
                    print(f"\n[{role}] idle timeout: geen data voor {idle_timeout}s, abort")
                    raise TimeoutError(f"LLM stream stuck: no data for {idle_timeout}s")

                if not line:
                    continue
                last_chunk_time = time.time()

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
        print()
        return full_text
