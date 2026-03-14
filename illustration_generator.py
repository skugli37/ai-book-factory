import os
import aiohttp # pyre-ignore[21]
import asyncio
from pathlib import Path
from PIL import Image # pyre-ignore[21]
import io

class IllustrationGenerator:
    """Generates interior illustrations for chapters using Hugging Face."""
    
    def __init__(self, hf_token: str):
        self.hf_token = hf_token
        self.api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        self.headers = {"Authorization": f"Bearer {hf_token}"}

    async def generate_chapter_art(self, prompt: str, save_path: Path) -> bool:
        """Generates a black-and-white artistic sketch for a chapter."""
        # Force an artistic, interior-friendly style
        enhanced_prompt = f"Professional black and white minimalist line art illustration, {prompt}, vertical composition, high contrast, book interior style, white background"
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {"width": 1024, "height": 1024}
        }
        
        print(f"   🎨 Generating chapter art: {prompt}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        content = await response.read()
                        image = Image.open(io.BytesIO(content))
                        image.save(save_path)
                        return True
                    else:
                        print(f"   ⚠️ Art generation failed: {response.status}")
                        return False
        except Exception as e:
            print(f"   ⚠️ Illustration error: {e}")
            return False
            
        return False
