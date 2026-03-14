import asyncio
from typing import List
from research.interfaces import Summariser  # pyre-ignore[21]

class GroqSummariser(Summariser):
    """Summariser using the already configured Groq API (High quality & Free)."""
    
    def __init__(self, ai_writer):
        self.ai_writer = ai_writer

    async def summarise(self, texts: List[str], max_length: int = 300) -> str:
        if not texts:
            return "No data available."

        combined = " ".join(texts)
        # Limit input size for context window
        combined = combined[:6000]  # pyre-ignore[16]
        
        prompt = f"""Summarize the following search result snippets into a single, cohesive research paragraph for a book chapter. 
Focus on facts, dates, and key concepts.
Max length: {max_length} characters.

Snippets:
{combined}

Summary:"""

        try:
            # We use the existing AIWriter which handles rate limits (3s pause)
            summary = await self.ai_writer.generate(prompt, max_tokens=max_length)
            return summary.strip()
        except Exception as e:
            print(f"   ⚠️ Groq Summariser failed: {e}")
            return combined[:500]
