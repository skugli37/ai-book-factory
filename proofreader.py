from typing import List, Optional
from writer import AIWriter # pyre-ignore[21]

class ProofreaderAgent:
    """Uses a secondary LLM pass to refine and polish book content."""
    
    def __init__(self, ai_writer: AIWriter):
        self.writer = ai_writer

    async def refined_proofread(self, chapter_title: str, content: str) -> str:
        """Performs a comprehensive proofreading and styling pass."""
        print(f"   ✍️  Refining and proofreading: {chapter_title}...")
        
        prompt = f"""
        You are a world-class book editor and proofreader. 
        Your task is to refine the following book chapter: "{chapter_title}".

        STRICT RULES:
        1. Fix any grammar, punctuation, or spelling errors.
        2. Remove repetitive phrases or redundant sentences.
        3. Improve sentence flow and stylistic consistency.
        4. Maintain the original core information and facts.
        5. Keep the formatting (headers, bullet points) intact.
        6. DO NOT add any conversational filler (e.g., "Here is the proofread version").
        7. OUTPUT ONLY THE REFINED TEXT.

        Original Content:
        ---
        {content}
        ---
        """
        
        # Use a slightly lower temperature for proofreading to ensure stability
        refined_content = await self.writer.generate(prompt, temperature=0.3)
        
        if not refined_content or len(refined_content) < len(content) * 0.7:
            # Fallback to original if AI failed or truncated too much
            print(f"   ⚠️ Proofreading returned empty or too short, using original.")
            return str(content)
            
        return str(refined_content)
