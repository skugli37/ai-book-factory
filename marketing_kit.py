from pathlib import Path
from typing import List, Optional
from writer import AIWriter # pyre-ignore[21]

class MarketingKitGenerator:
    """Generates promotional content for the finished book."""
    
    def __init__(self, ai_writer: AIWriter):
        self.writer = ai_writer

    async def generate_kit(self, book_dir: Path, metadata: dict) -> Path:
        """Generates a comprehensive marketing suite."""
        print(f"   📣 Generating Social Media & Marketing Kit...")
        
        title = metadata.get("title", "this book")
        genre = metadata.get("genre", "non-fiction")
        description = metadata.get("description", "")
        
        prompt = f"""
        Create a professional social media marketing kit for the following book:
        
        Title: {title}
        Genre: {genre}
        Description: {description}
        
        Please generate:
        1. THREE Instagram/Facebook posts (Image description + Caption + Hashtags).
        2. ONE TikTok/Reels Script (Hook, Body, Call to Action).
        3. ONE Newsletter Email for subscribers announcing the launch.
        
        Tone: Enthusiastic, professional, and persuasive.
        OUTPUT ONLY THE KIT CONTENT IN CLEAN MARKDOWN.
        """
        
        kit_content = await self.writer.generate(prompt, max_tokens=2000)
        
        kit_path = book_dir / "marketing_kit.md"
        with open(kit_path, "w", encoding="utf-8") as f:
            f.write(f"# Marketing Kit: {title}\n\n")
            f.write(kit_content)
            
        print(f"   ✅ Marketing kit saved: {kit_path}")
        return kit_path
