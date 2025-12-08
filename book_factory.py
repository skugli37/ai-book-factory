#!/usr/bin/env python3
"""
AI BOOK FACTORY 📚
Automatski generiše knjige i objavljuje na Amazon KDP

Besplatni resursi:
- Groq API (Llama 70B) - pisanje teksta
- Pollinations.ai - cover slike (besplatno, bez API key)
- Amazon KDP - objavljivanje (besplatno)
"""

import asyncio
import aiohttp
import json
import os
import random
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

# Konfiguracija
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OUTPUT_DIR = Path("./books")
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class BookConfig:
    """Konfiguracija za generisanje knjige"""
    title: str
    genre: str
    target_words: int
    chapters: int
    language: str = "english"
    author_name: str = "AI Publishing House"
    description: str = ""
    keywords: List[str] = None


@dataclass
class Chapter:
    """Jedno poglavlje"""
    number: int
    title: str
    content: str
    word_count: int


class AIWriter:
    """Generiše tekst koristeći Groq (Llama 70B) - BESPLATNO"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
    
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4000) -> str:
        """Generiše tekst"""
        
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
            "temperature": 0.8,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    raise Exception(f"Groq API error: {error}")


class CoverGenerator:
    """Generiše book cover koristeći Pollinations.ai - BESPLATNO, BEZ API KEY"""
    
    @staticmethod
    async def generate(title: str, genre: str, output_path: Path) -> Path:
        """Generiše cover sliku"""
        
        # Prompt za cover
        style_map = {
            "romance": "romantic couple silhouette, sunset, soft colors, elegant typography",
            "thriller": "dark mysterious atmosphere, suspenseful, noir style",
            "self-help": "minimalist, inspiring, clean design, motivational",
            "fantasy": "magical landscape, epic, dragons, castles",
            "sci-fi": "futuristic cityscape, space, neon lights, cyberpunk",
            "mystery": "foggy street, detective noir, vintage",
            "horror": "dark forest, creepy atmosphere, gothic",
            "business": "professional, corporate, success imagery",
        }
        
        style = style_map.get(genre.lower(), "professional book cover design")
        
        prompt = f"Book cover for '{title}', {style}, high quality, no text, cinematic"
        prompt_encoded = prompt.replace(" ", "%20")
        
        # Pollinations.ai - besplatno, bez registracije
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1600&height=2560&nologo=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    with open(output_path, "wb") as f:
                        f.write(image_data)
                    print(f"✅ Cover saved: {output_path}")
                    return output_path
                else:
                    raise Exception(f"Cover generation failed: {resp.status}")


class BookFactory:
    """Glavna fabrika za generisanje knjiga"""
    
    # Profitable niše na Amazon KDP
    PROFITABLE_NICHES = [
        {
            "genre": "self-help",
            "topics": [
                "Morning routines for success",
                "Overcoming anxiety naturally",
                "Building confidence in 30 days",
                "Mindfulness for beginners",
                "Breaking bad habits",
                "Emotional intelligence mastery",
                "Stoicism for modern life",
                "Digital detox guide",
            ]
        },
        {
            "genre": "romance",
            "topics": [
                "Second chance romance",
                "Small town love story",
                "Enemies to lovers",
                "Boss and employee romance",
                "Summer beach romance",
                "Christmas love story",
                "Fake dating becomes real",
                "Best friend's brother",
            ]
        },
        {
            "genre": "business",
            "topics": [
                "Passive income strategies",
                "Freelancing for beginners",
                "Starting online business",
                "Real estate investing basics",
                "Cryptocurrency for beginners",
                "Side hustle ideas",
                "Negotiation tactics",
                "Remote work productivity",
            ]
        },
        {
            "genre": "mystery",
            "topics": [
                "Small town murder mystery",
                "Cozy mystery with cats",
                "Amateur detective story",
                "Cold case investigation",
                "Locked room mystery",
            ]
        },
    ]
    
    def __init__(self, groq_api_key: str):
        self.writer = AIWriter(groq_api_key)
        self.cover_gen = CoverGenerator()
    
    async def generate_book_idea(self, genre: str = None) -> BookConfig:
        """Generiše ideju za knjigu"""
        
        if genre is None:
            niche = random.choice(self.PROFITABLE_NICHES)
        else:
            niche = next((n for n in self.PROFITABLE_NICHES if n["genre"] == genre), 
                        self.PROFITABLE_NICHES[0])
        
        topic = random.choice(niche["topics"])
        
        # Generiši naslov
        prompt = f"""Generate a catchy, marketable book title for a {niche['genre']} book about: {topic}

Rules:
- Title should be 3-7 words
- Should be intriguing and sellable
- Include a subtitle after a colon
- Return ONLY the title, nothing else

Example format: "Main Title: Compelling Subtitle Here"
"""
        
        title = await self.writer.generate(prompt, max_tokens=100)
        title = title.strip().strip('"')
        
        # Generiši opis
        desc_prompt = f"""Write a compelling Amazon book description for: "{title}"
Genre: {niche['genre']}
Topic: {topic}

Rules:
- 150-200 words
- Hook reader in first sentence
- Include bullet points of what they'll learn
- End with call to action
- Make it sound professional and valuable
"""
        
        description = await self.writer.generate(desc_prompt, max_tokens=500)
        
        # Konfiguracija knjige
        word_targets = {
            "self-help": 15000,
            "romance": 40000,
            "business": 20000,
            "mystery": 50000,
        }
        
        chapter_counts = {
            "self-help": 10,
            "romance": 20,
            "business": 12,
            "mystery": 25,
        }
        
        return BookConfig(
            title=title,
            genre=niche["genre"],
            target_words=word_targets.get(niche["genre"], 20000),
            chapters=chapter_counts.get(niche["genre"], 12),
            description=description,
            keywords=[topic, niche["genre"], "bestseller", "2025"]
        )
    
    async def generate_outline(self, config: BookConfig) -> List[str]:
        """Generiše outline knjige"""
        
        prompt = f"""Create a detailed chapter outline for a {config.genre} book titled: "{config.title}"

Requirements:
- Exactly {config.chapters} chapters
- Each chapter title should be compelling
- Logical flow from beginning to end
- Format: One chapter title per line, numbered

Example:
1. The Awakening
2. First Steps
...
"""
        
        response = await self.writer.generate(prompt, max_tokens=1000)
        
        # Parse chapter titles
        chapters = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove number and dot
                title = re.sub(r'^\d+[\.\)]\s*', '', line)
                if title:
                    chapters.append(title)
        
        # Ensure we have enough chapters
        while len(chapters) < config.chapters:
            chapters.append(f"Chapter {len(chapters) + 1}")
        
        return chapters[:config.chapters]
    
    async def generate_chapter(self, config: BookConfig, chapter_num: int, 
                              chapter_title: str, outline: List[str],
                              previous_summary: str = "") -> Chapter:
        """Generiše jedno poglavlje"""
        
        words_per_chapter = config.target_words // config.chapters
        
        system_prompt = f"""You are a professional {config.genre} author writing a book titled "{config.title}".
Write engaging, well-crafted prose. Maintain consistent tone and style throughout.
This is chapter {chapter_num} of {config.chapters}."""
        
        context = f"Previous chapters summary: {previous_summary}" if previous_summary else "This is the beginning of the book."
        
        prompt = f"""Write Chapter {chapter_num}: "{chapter_title}"

Book: "{config.title}"
Genre: {config.genre}
{context}

Full chapter outline for context:
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(outline))}

Requirements:
- Write approximately {words_per_chapter} words
- Start with a hook
- Include dialogue where appropriate
- End with something that makes reader want to continue
- Write the FULL chapter content, not an outline

Begin writing the chapter now:
"""
        
        content = await self.writer.generate(prompt, max_tokens=4000)
        
        # Count words
        word_count = len(content.split())
        
        return Chapter(
            number=chapter_num,
            title=chapter_title,
            content=content,
            word_count=word_count
        )
    
    async def generate_book(self, config: BookConfig = None) -> Path:
        """Generiše kompletnu knjigu"""
        
        if config is None:
            print("📚 Generating book idea...")
            config = await self.generate_book_idea()
        
        print(f"\n{'='*60}")
        print(f"📖 GENERATING: {config.title}")
        print(f"📚 Genre: {config.genre}")
        print(f"📝 Target: {config.target_words:,} words in {config.chapters} chapters")
        print(f"{'='*60}\n")
        
        # Create book directory
        safe_title = re.sub(r'[^\w\s-]', '', config.title)[:50].strip()
        book_dir = OUTPUT_DIR / safe_title
        book_dir.mkdir(exist_ok=True)
        
        # Generate outline
        print("📋 Generating outline...")
        outline = await self.generate_outline(config)
        print(f"   ✅ {len(outline)} chapters planned")
        
        # Generate cover
        print("🎨 Generating cover...")
        cover_path = book_dir / "cover.png"
        try:
            await self.cover_gen.generate(config.title, config.genre, cover_path)
        except Exception as e:
            print(f"   ⚠️ Cover generation failed: {e}")
        
        # Generate chapters
        chapters = []
        total_words = 0
        previous_summary = ""
        
        for i, chapter_title in enumerate(outline):
            print(f"✍️  Writing Chapter {i+1}/{len(outline)}: {chapter_title}...")
            
            chapter = await self.generate_chapter(
                config, i+1, chapter_title, outline, previous_summary
            )
            chapters.append(chapter)
            total_words += chapter.word_count
            
            # Update summary for context
            summary_prompt = f"Summarize this chapter in 2-3 sentences:\n{chapter.content[:2000]}"
            previous_summary += f"\nChapter {i+1}: " + await self.writer.generate(
                summary_prompt, max_tokens=100
            )
            
            print(f"   ✅ {chapter.word_count:,} words")
            
            # Rate limiting - Groq has limits
            await asyncio.sleep(2)
        
        # Compile book
        print("\n📚 Compiling book...")
        
        # Save as Markdown
        md_path = book_dir / "book.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {config.title}\n\n")
            f.write(f"*By {config.author_name}*\n\n")
            f.write(f"---\n\n")
            f.write(f"## Description\n\n{config.description}\n\n")
            f.write(f"---\n\n")
            
            for chapter in chapters:
                f.write(f"## Chapter {chapter.number}: {chapter.title}\n\n")
                f.write(f"{chapter.content}\n\n")
                f.write(f"---\n\n")
        
        # Save as plain text (for KDP)
        txt_path = book_dir / "book.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"{config.title}\n")
            f.write(f"By {config.author_name}\n\n")
            
            for chapter in chapters:
                f.write(f"\n{'='*40}\n")
                f.write(f"CHAPTER {chapter.number}: {chapter.title}\n")
                f.write(f"{'='*40}\n\n")
                f.write(f"{chapter.content}\n")
        
        # Save metadata
        metadata = {
            "title": config.title,
            "author": config.author_name,
            "genre": config.genre,
            "description": config.description,
            "keywords": config.keywords,
            "total_words": total_words,
            "chapters": len(chapters),
            "generated_at": datetime.now().isoformat(),
        }
        
        meta_path = book_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✅ BOOK COMPLETE!")
        print(f"📖 Title: {config.title}")
        print(f"📊 Total words: {total_words:,}")
        print(f"📁 Location: {book_dir}")
        print(f"{'='*60}")
        
        return book_dir


async def main():
    """Main entry point"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                 📚 AI BOOK FACTORY 📚                    ║
    ║                                                          ║
    ║  Automatski generiše knjige za Amazon KDP               ║
    ║  Besplatno: Groq API + Pollinations.ai                  ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not set!")
        print("   Get free key at: https://console.groq.com")
        print("   Then: export GROQ_API_KEY=your_key_here")
        return
    
    factory = BookFactory(api_key)
    
    # Generate a book
    book_dir = await factory.generate_book()
    
    print(f"\n📚 Your book is ready at: {book_dir}")
    print("\n📋 Next steps:")
    print("   1. Review and edit the content")
    print("   2. Format for KDP (use book.txt)")
    print("   3. Upload cover.png to KDP")
    print("   4. Publish and profit! 💰")


if __name__ == "__main__":
    asyncio.run(main())
