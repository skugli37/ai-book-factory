import os
import asyncio
import aiohttp # pyre-ignore[21]
from typing import Optional, Callable
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type # pyre-ignore[21]
import config
from huggingface_hub import InferenceClient # pyre-ignore[21]

class RateLimitError(Exception):
    pass

class AIWriter:
    """Generates text via Groq or Hugging Face API, respecting rate limits."""

    def __init__(self, api_key: str, hf_token: Optional[str] = None, on_rate_limit: Optional[Callable] = None): # pyre-ignore[2]
        self.api_key = api_key
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.provider = getattr(config, "LLM_PROVIDER", "groq")
        
        # Groq Setup
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_models = getattr(config, "GROQ_MODELS", ["llama-3.1-70b-versatile"])
        
        # HF Setup
        self.hf_models = getattr(config, "HF_LLM_MODELS", ["Qwen/Qwen2.5-72B-Instruct"])
        
        self.current_model_idx = 0
        self.on_rate_limit = on_rate_limit
        self.request_lock = asyncio.Lock()
        self.last_request_time: float = 0.0

    @property
    def models(self):
        return self.hf_models if self.provider == "huggingface" else self.groq_models

    @property
    def model(self):
        return self.models[self.current_model_idx]

    async def _rotate_model(self):
        old_model = self.model
        self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
        msg = f"🔄 {old_model} rate limited. Rotating to {self.model}..."
        print(msg)
        callback = self.on_rate_limit
        if callback:
            await callback(msg)

    @retry(
        wait=wait_exponential(multiplier=2, min=5, max=90),
        stop=stop_after_attempt(12),
        retry=retry_if_exception_type(RateLimitError),
        reraise=True
    )
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000, temperature: float = 0.8) -> str:
        """Calls the configured provider (Groq or HF) with retries and rotation."""
        
        if self.provider == "huggingface":
            return await self._generate_hf(prompt, system, max_tokens, temperature)
        return await self._generate_groq(prompt, system, max_tokens, temperature)

    async def _generate_hf(self, prompt: str, system: str, max_tokens: int, temperature: float) -> str:
        """HF-specific generation using InferenceClient."""
        if not self.hf_token:
            print("   ⚠️ No HF_TOKEN found. Falling back to Groq...")
            self.provider = "groq"
            return await self._generate_groq(prompt, system, max_tokens, temperature)

        client = InferenceClient(model=self.model, token=self.hf_token)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            # We use chat_completion for structured dialogue/instruct models
            response = await asyncio.to_thread(
                client.chat_completion,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content or "" # pyre-ignore[16]
        except Exception as e:
            print(f"   ❌ HF Error for {self.model}: {str(e)}")
            await self._rotate_model()
            raise RateLimitError(f"HF API failure: {str(e)}")

    async def _generate_groq(self, prompt: str, system: str, max_tokens: int, temperature: float) -> str:
        """Original Groq-specific generation."""
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
                async with session.post(self.groq_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return str(data["choices"][0]["message"]["content"])
                    elif resp.status == 429:
                        await self._rotate_model()
                        raise RateLimitError(f"Groq API rate limit (429) for {self.model}")
                    else:
                        error_text = await resp.text()
                        await self._rotate_model()
                        raise RateLimitError(f"Groq API error ({resp.status}): {error_text}")
            except aiohttp.ClientError as e:
                await self._rotate_model()
                raise RateLimitError(f"Network error: {str(e)}")
        
        raise Exception("Unhandled response state in AIWriter.generate")

    async def generate_long(self, prompt: str, system: str = "", target_tokens: int = 4000, temperature: float = 0.8) -> str:
        """
        Generates text that can exceed the single-pass limit by detecting truncation
        and automatically prompting for continuation. Works for both Groq and HF.
        """
        full_text = ""
        current_prompt = prompt
        
        for burst in range(3):
            section = await self.generate(current_prompt, system=system, max_tokens=4000, temperature=temperature)
            full_text += " " + section
            
            trimmed = section.strip()
            if trimmed and trimmed[-1] in ".!?:}\"]":
                break
            
            system = "Continue the narrative exactly from the last character. Do not repeat anything. Dive straight into the next sentence."
            current_prompt = "Continue the following text, starting from the very next character. Maintain tone and style:\n\n" + full_text[-1000:]
            print(f"   ↪ Detected truncation in burst {burst+1} ({self.provider}). Requesting continuation...")
            
        return full_text.strip()
