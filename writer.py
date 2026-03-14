import asyncio
import aiohttp # pyre-ignore[21]
from typing import Optional, Callable
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type # pyre-ignore[21]
import config
from config import GROQ_MODELS # pyre-ignore[21]

class RateLimitError(Exception):
    pass

class AIWriter:
    """Generates text via Groq API, respecting free tier rate limits."""

    def __init__(self, api_key: str, on_rate_limit: Optional[Callable] = None): # pyre-ignore[2]
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.models = GROQ_MODELS
        self.current_model_idx = 0
        self.on_rate_limit = on_rate_limit
        self.request_lock = asyncio.Lock()
        self.last_request_time: float = 0.0

    @property
    def model(self):
        return self.models[self.current_model_idx]

    async def _rotate_model(self):
        old_model = self.model
        self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
        msg = f"🔄 {old_model} rate limited. Rotating to {self.model}..."
        print(msg)
        if self.on_rate_limit:
            await self.on_rate_limit(msg)

    @retry(
        wait=wait_exponential(multiplier=2, min=5, max=90),  # Increased max wait to 90s
        stop=stop_after_attempt(12),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True
    )
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000, temperature: float = 0.8) -> str:
        """Calls Groq API with retries and automatic model rotation."""
        
        async with self.request_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request_time
            delay = getattr(config, 'GROQ_REQUEST_DELAY', 3.2)
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            self.last_request_time = float(asyncio.get_event_loop().time())
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.base_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return str(data["choices"][0]["message"]["content"])
                    elif resp.status == 429:
                        await self._rotate_model()
                        raise RateLimitError(f"Groq API rate limit (429) for {self.model}")
                    else:
                        error_text = await resp.text()
                        # On any other error (404, 500), also rotate and retry
                        await self._rotate_model()
                        raise RateLimitError(f"Groq API error ({resp.status}): {error_text}")
            except aiohttp.ClientError as e:
                await self._rotate_model()
                raise RateLimitError(f"Network error: {str(e)}")
        
        raise Exception("Unhandled response state in AIWriter.generate")
