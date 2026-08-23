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
    # De developer werkt in twee fasen. De designer denkt het project een keer
    # helemaal door en legt per bestand vast wat erin moet; de writer zet die
    # specificatie om in code zonder zelf te redeneren.
    #
    # Gemeten 2026-08-23, waarom deze modellen:
    #   ~deepseek/deepseek-v4-flash-latest  95% van de output is reasoning
    #   google/gemini-3.7-flash             73%
    #   deepseek/deepseek-v3.2               0%  <- schrijft alleen uit
    #   anthropic/claude-haiku-4.5           0%
    # Een schrijver die zelf redeneert maakt de opsplitsing zinloos: dan betaal
    # je het denkwerk alsnog per bestand.
    "designer":         "~anthropic/claude-opus-latest",
    "designer_premium": "~anthropic/claude-opus-latest",
    "writer":           "deepseek/deepseek-v3.2",
    "writer_premium":   "anthropic/claude-haiku-4.5",
    # Blijft staan zodat oude aanroepen met role="developer" niet omvallen.
    "developer": "~google/gemini-pro-latest",
    "developer_premium":  "~anthropic/claude-opus-latest",
    "builder":   "deepseek/deepseek-v3.2",
    "tester":    "deepseek/deepseek-v3.2",
    "judge":     "~anthropic/claude-sonnet-latest",
    # Controleert de contractbestanden tegen het plan voor de rest erop
    # gebouwd wordt. Kleine input, klein antwoord, dus goedkoop.
    "contract_review": "~anthropic/claude-sonnet-latest",
    # Destilleert lessen uit de mislukte pogingen van een run.
    "lesson_extractor": "~anthropic/claude-sonnet-latest",
    "consultant_scientific": "~google/gemini-pro-latest",
}

# max_tokens per rol. Let op: reasoning-modellen rekenen hun interne
# redeneertokens hierin mee. De developer levert de grootste output en liep
# op 32000 stelselmatig vast: Gemini 3.1 Pro verbruikte daar 24824 tokens
# (78%) aan reasoning en werd afgekapt midden in de JSON, wat verderop opdook
# als een onbegrijpelijke "kon geen JSON extraheren". 64000 is wat alle
# gebruikte modellen aankunnen - Gemini 3.1 Pro stopt bij 65536.
MAX_TOKENS = {
    "developer":          64000,
    "developer_premium":  64000,
    # De designer levert de specificatie van het hele project in een antwoord.
    "designer":           64000,
    "designer_premium":   64000,
    # De writer levert een bestand; meer dan dit betekent dat er iets misgaat.
    "writer":             16000,
    "writer_premium":     16000,
}
DEFAULT_MAX_TOKENS = 32000

# Timeout per rol in seconden
TIMEOUTS = {
    "planner":   180,   # 3 min
    "developer": 600,   # 15 min - grote code outputs
    "designer":         900,   # denkt het hele project door
    "designer_premium": 900,
    "writer":           300,
    "writer_premium":   300,
    "builder":   300,   # 5 min
    "developer_premium":  900,   # Opus is trager, geef meer tijd
    "tester":    300,   # 5 min
    "consultant_scientific": 120, #  2 min
    "judge":     180,   # 3 min
    "contract_review": 180,   # 3 min
    "lesson_extractor": 180,   # 3 min
}

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY niet gevonden in .env")

    def generate(self, prompt: str, role: str = "planner",
                 temperature: float = 0.7, stream: bool = True,
                 cache_prefix_len: int = None) -> str:
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

        # cache_prefix_len: de aanroeper weet waar het herbruikbare deel eindigt.
        # Dat is essentieel bij per-bestand generatie: alleen een prefix die bij
        # elke aanroep byte-identiek is levert een cache-hit op. Zonder opgave
        # valt hij terug op het oude gedrag (alles behalve de laatste 200 chars).
        if cache_prefix_len is not None:
            cache_split = max(0, min(cache_prefix_len, len(prompt)))
        else:
            cache_split = max(0, len(prompt) - 200)

        if supports_caching and cache_split > 1024:
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
            "max_tokens": MAX_TOKENS.get(role, DEFAULT_MAX_TOKENS),
            "messages": messages
        }
        if not stream:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        # Streaming mode: live tonen wat binnenkomt
        print(f"[{role} via {model}] streaming...", flush=True)
        full_text = ""
        finish_reason = None
        usage_info = None
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
                    if chunk.get("usage"):
                        usage_info = chunk["usage"]
                    choice = (chunk.get("choices") or [{}])[0]
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
                    delta = (choice.get("delta") or {}).get("content", "")
                    if delta:
                        print(delta, end="", flush=True)
                        full_text += delta
                except (json.JSONDecodeError, KeyError):
                    continue
        print()
        det = (usage_info or {}).get("completion_tokens_details") or {}
        gebruikt = (usage_info or {}).get("completion_tokens")
        redeneer = det.get("reasoning_tokens")
        gecached = ((usage_info or {}).get("prompt_tokens_details") or {}).get("cached_tokens")
        invoer = (usage_info or {}).get("prompt_tokens")
        print(f"[{role}] finish_reason={finish_reason} prompt_tokens={invoer} "
              f"completion_tokens={gebruikt} reasoning_tokens={redeneer} "
              f"cached_prompt_tokens={gecached} content_chars={len(full_text)}", flush=True)

        # Half afgeleverde JSON is nooit bruikbaar. Zonder deze check komt dat
        # verderop naar boven als "kon geen JSON extraheren", wat de echte
        # oorzaak verbergt.
        if finish_reason == "length":
            raise ValueError(
                f"{role}: antwoord afgekapt op de max_tokens-grens "
                f"({MAX_TOKENS.get(role, DEFAULT_MAX_TOKENS)}). Verbruikt: {gebruikt} tokens, "
                f"waarvan {redeneer} aan reasoning. Verhoog MAX_TOKENS voor deze rol "
                f"of kies een model dat minder redeneert."
            )
        return full_text
