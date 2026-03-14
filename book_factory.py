import asyncio
import aiohttp  # pyre-ignore[21]
import random
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type  # pyre-ignore[21]

from config import BookConfig, PROFITABLE_NICHES, GROQ_API_KEY, GROQ_MODELS, OUTPUT_DIR, HF_TOKEN  # pyre-ignore[21]
from cover_generator import CoverGenerator  # pyre-ignore[21]
from metadata_generator import MetadataGenerator  # pyre-ignore[21]
from kdp_formatter import KDPFormatter  # pyre-ignore[21]
from research.orchestrator import ResearchOrchestrator  # pyre-ignore[21]
from proofreader import ProofreaderAgent  # pyre-ignore[21]
from illustration_generator import IllustrationGenerator  # pyre-ignore[21]
from marketing_kit import MarketingKitGenerator  # pyre-ignore[21]
from character_sheet import CharacterSheet  # pyre-ignore[21]
from writer import AIWriter, RateLimitError # pyre-ignore[21]

@dataclass
class Chapter:
    """A generated chapter"""
    number: int
    title: str
    content: str
    word_count: int

from writer import AIWriter, RateLimitError # pyre-ignore[21]

class BookFactory:
    """The central orchestration engine for generating books."""

    def __init__(self, api_key: str = GROQ_API_KEY, progress_callback=None):
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Please set the environment variable.")
        
        self.progress_callback = progress_callback
        
        async def on_rate_limit(msg: str):
            # Report rate limit to UI heartbeat
            await self.report_progress("writing", percent=-1, text=msg)

        self.writer = AIWriter(api_key, hf_token=HF_TOKEN, on_rate_limit=on_rate_limit)
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        # Initialize Research Orchestrator (handles DDG + Groq)
        self.research = ResearchOrchestrator(self.writer)
        # Initialize Proofreader Agent
        self.proofreader = ProofreaderAgent(self.writer)
        # Initialize Illustration Generator (uses HF Token)
        self.illustrator = IllustrationGenerator(HF_TOKEN)
        # Initialize Character Sheet (lazy loaded later)
        self.characters: Optional[CharacterSheet] = None

    async def report_progress(self, stage: str, percent: int, chapter: int = 0, text: str = "", extra_data: dict | None = None):
        if self.progress_callback:
            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(stage, percent, chapter, text, extra_data)
            else:
                self.progress_callback(stage, percent, chapter, text, extra_data)

    async def generate_book_idea(self, genre: str | None = None) -> BookConfig:
        """Generates a viable book idea."""
        
        if genre is None:
            niche = random.choice(PROFITABLE_NICHES)
        else:
            niche = next((n for n in PROFITABLE_NICHES if n["genre"].lower() == genre.lower()), PROFITABLE_NICHES[0])

        topic = random.choice(niche["topics"])

        prompt = f"""Generate a catchy, marketable book title for a '{niche['genre']}' book about: {topic}

Rules:
- Title should be 3-7 words
- Should be intriguing and sellable
- Include a subtitle after a colon
- Return ONLY the title, nothing else

Example format: "Main Title: Compelling Subtitle Here"
"""
        title = await self.writer.generate(prompt, max_tokens=100)
        title = self.clean_ai_title(title)

        desc_prompt = f"""Write a compelling Amazon book description for: "{title}"
Genre: {niche['genre']}
Topic: {topic}

Rules:
- 150-200 words
- Hook reader in first sentence
- Include bullet points of what they'll learn
- End with a call to action
- Make it sound professional and valuable
"""
        description = await self.writer.generate(desc_prompt, max_tokens=500)

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
            niche_keywords=[topic, niche["genre"], "bestseller", "2025"]
        )

    async def generate_outline(self, config: BookConfig) -> List[str]:
        """Generates the chapter outline structure."""
        
        prompt = f"""Create a detailed chapter outline for a {config.genre} book titled: "{config.title}"

Requirements:
- Exactly {config.chapters} chapters
- Each chapter title should be compelling
- Logical flow from beginning to end
- Format: One chapter title per line, numbered

Example:
1. The Awakening
2. First Steps
"""
        response = await self.writer.generate(prompt, max_tokens=1000)

        chapters: List[str] = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                title = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                title = self.clean_ai_title(title)
                if title:
                    chapters.append(title)

        limit = int(config.chapters)
        return chapters[0:limit]  # pyre-ignore[6]

    def clean_ai_title(self, text: str) -> str:
        """Strips common AI boilerplate and markdown from titles."""
        # Remove common "Here is your title:" intros
        text = re.sub(r'^(here is|your|catchy)?\s*(book|chapter)?\s*title:\s*', '', text, flags=re.IGNORECASE)
        # Remove quotes, asterisks, and newlines
        text = text.strip().strip('"*#\n ')
        # Capitalize properly
        return text

    async def generate_chapter(self, config: BookConfig, chapter_num: int, 
                              chapter_title: str, outline: List[str],
                              previous_summary: str = "") -> Chapter:
        """Generates the main text content for a single chapter with live research."""
        
        # Step 1: Perform live research for the chapter topic
        research = await self.research.research(chapter_title)
        
        # Step 1.5: Character Context (if fiction)
        char_context = ""
        mgr = self.characters
        if mgr is not None:
            char_context = mgr.get_all_characters()
        
        words_per_chapter = config.target_words // config.chapters

        system_prompt = f"""You are a prestigious, high-end {config.genre} author known for technical depth, unique insights, and a gripping narrative style. 
Your book is titled '{config.title}'. 

CRITICAL WRITING RULES:
1. NO AI SLANG: Avoid generic phrases like 'In today's digital age', 'ever-evolving landscape', 'a multi-faceted approach', or 'it is crucial to remember'.
2. BE SPECIFIC: Never use vague generalizations. Use the provided research as primary evidence. 
3. DEPTH OVER BREADTH: For every point you make, provide a detailed 'why' and a 'how'. 
4. VARY SENTENCE STRUCTURE: Use a mix of short, punchy sentences and complex, descriptive ones. 
5. NO REPETITION: Do not repeat concepts or key phrases (especially thematic ones like 'killer tech') across paragraphs.
6. NO INTRO/OUTRO FLUFF: Do not start chapters with "In this chapter, we will explore...". Dive straight into the meat of the content.
"""
        
        context = f"So far in the book: {previous_summary}\n" if previous_summary else "This is the opening of the volume.\n"

        prompt = f"""Write a massive and detailed Chapter {chapter_num}: "{chapter_title}"

Target Genre: {config.genre}
Context: {context}
{char_context}

Outline for reference:
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(outline))}

LIVE RESEARCH DATA (Use this to provide real-world value and authority):
{research.summary}

Top Sources to cite/integrate: {", ".join(r.url for r in research.results[:3])}

TECHNICAL REQUIREMENTS:
- TONE: {config.tone}, highly authoritative and premium.
- TARGET LENGTH: Aim for {words_per_chapter} words. Expand your arguments with examples.
- FORMAT: Raw narrative text. NO summaries, NO bullet points (unless part of a listicle section), NO intros.
- NO REPETITION: Ensure every paragraph brings a NEW insight or evidence piece.

STRETCH THE DEPTH: If you feel you are finishing too early, find a specific sub-topic from the Research Data and perform a 'Deep Dive' sidebar in the text.

BEGIN CHAPTER {chapter_num} IMMEDIATELY:
"""
        # Switching to generate_long to prevent cut-offs
        content = await self.writer.generate_long(prompt, system=system_prompt, temperature=0.8)
        
        # Step 2: Proofread and refine the content
        content = await self.proofreader.refined_proofread(chapter_title, content)
        
        # Step 3: Update Character Sheet
        mgr_update = self.characters
        if mgr_update is not None:
            await mgr_update.extract_characters_from_text(self.writer, content, chapter_num)
            
        word_count = len(content.split())

        return Chapter(
            number=chapter_num,
            title=chapter_title,
            content=content,
            word_count=word_count
        )

    async def _write_markdown_and_txt(self, config: BookConfig, chapters: List[Chapter], book_dir: Path):
        """Assembles and writes the plain text and markdown versions."""
        
        md_path = book_dir / "book.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {config.title}\n\n*By {config.author_name}*\n\n---\n\n")
            f.write(f"## Description\n\n{config.description}\n\n---\n\n")
            for chapter in chapters:
                f.write(f"## {chapter.title}\n\n{chapter.content}\n\n---\n\n")
        
        txt_path = book_dir / "book.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"{config.title}\nBy {config.author_name}\n\n")
            for chapter in chapters:
                f.write(f"\n{'='*40}\nCHAPTER {chapter.number}: {chapter.title}\n{'='*40}\n\n")
                f.write(f"{chapter.content}\n")

    async def generate_book(self, config: BookConfig | None = None) -> Path:
        """The main pipeline execution function."""
        
        num_retries: int = 3
        while num_retries > 0:
            if config is None:
                print("📚 Bootstrapping dynamic book idea...")
                try:
                    await self.report_progress("idea_generation", 5)
                    config = await self.generate_book_idea()
                except RateLimitError:
                    print("Hit rate limits during idea generation. Retrying...")
                    await asyncio.sleep(5)
                    num_retries = num_retries - 1  # pyre-ignore[58]
                    continue
            break
            break
            
        if config is None:
            raise Exception("Failed to generate book idea due to persistent rate limiting.")
        
        # Help type checker see config as non-None
        current_config: BookConfig = config
        assert current_config is not None

        print(f"\n============================================================")
        print(f"📖 TARGET: {current_config.title}")  # pyre-ignore[16]
        print(f"📚 GENRE: {current_config.genre} | 📝 TARGET: {current_config.target_words:,} words")  # pyre-ignore[16]
        print(f"============================================================\n")

        # Sanitize title for filesystem (strip newlines, replace spaces with underscores, limit length)
        clean_title = str(current_config.title).replace('\n', ' ').strip()
        safe_title = re.sub(r'[^\w\s-]', '', clean_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        # Use explicit slicing that Pyre likes
        safe_title = safe_title[0:50].strip('_')
        
        book_dir = self.output_dir / safe_title
        book_dir.mkdir(exist_ok=True, parents=True)

        # Initialize Character Sheet for this specific book
        self.characters = CharacterSheet(book_dir / "characters.db")

        await self.report_progress("planning", 15)
        print("📋 Planning outline structure...")
        outline = await self.generate_outline(current_config)  # pyre-ignore[16]
        
        print("🎨 Requesting Pollinations.ai cover...")
        await self.report_progress("cover", 20)
        try:
            await CoverGenerator.generate(current_config.title, current_config.genre, book_dir / "cover.png")  # pyre-ignore[16]
            print("   ✅ Cover downloaded")
        except Exception as e:
            print(f"   ⚠️ Cover fallback: {e}")

        chapters = []
        total_words = 0
        previous_summary = ""

        # We execute chapters sequentially to maintain storyline continuity via `previous_summary`
        # and to manage rate limits more smoothly.
        for i, chapter_title in enumerate(outline):
            progress_base = 25
            progress_step = 70 / len(outline)
            current_progress = int(progress_base + (i * progress_step))
            
            await self.report_progress("writing", current_progress, chapter=i+1, text=f"Starting: {chapter_title}", extra_data={"word_count": total_words})
            print(f"✍️  Generating Ch {i+1}/{len(outline)}: {chapter_title[:40]}...")  # pyre-ignore[16]
            
            chapter = await self.generate_chapter(current_config, i+1, chapter_title, outline, previous_summary)  # pyre-ignore[16]
            
            # Step 2: Generate Chapter Illustration
            illustration_path = book_dir / f"chapter_{i+1}.png"
            art_prompt = f"Illustration for chapter: {chapter_title}"
            await self.illustrator.generate_chapter_art(art_prompt, illustration_path)
            
            chapters.append(chapter)
            total_words += chapter.word_count
            print(f"   ✅ Authored {chapter.word_count:,} words")
            
            # Update progress with actual word count after chapter
            await self.report_progress("writing", current_progress, chapter=i+1, text=f"Finished: {chapter_title}", extra_data={"word_count": total_words})
            
            # Generate a fast summary for context window passing bounds
            summary_prompt = f"Summarize this chapter chunk in 1-2 concise sentences:\n{chapter.content[:2000]}"
            summary = await self.writer.generate(summary_prompt, max_tokens=100)
            previous_summary += f"\nCh {i+1}: " + summary
            previous_summary = previous_summary.strip()

        await self.report_progress("assembling", 95)
        print("\n📚 Executing content assembly pipeline...")
        await self._write_markdown_and_txt(current_config, chapters, book_dir)
        
        print("🗂️ Generating final staging metadata...")
        meta_gen = MetadataGenerator(book_dir)
        # Using industry heuristic 275 words per KDP paperback page
        estimated_pages = max(1, total_words // 275)
        
        kdp_details = meta_gen.generate_kdp_details(current_config.__dict__, total_words, estimated_pages)
        meta_gen.save_metadata_json(kdp_details)

        # NEW: Integrate KDP Formatting and Marketing Kit into core pipeline
        print("▶ Formatting KDP compliant DOCX...")
        await self.report_progress("formatting", 97, text="Polishing DOCX layout...")
        formatter = KDPFormatter(book_dir)
        formatter.format_for_kdp()
        
        print("▶ Generating final upload checklist...")
        meta_gen.create_upload_checklist(formatter.metadata)
        
        print("▶ Constructing Marketing Kit...")
        await self.report_progress("marketing", 99, text="Generating sales copies...")
        kit_gen = MarketingKitGenerator(self.writer)
        await kit_gen.generate_kit(book_dir, formatter.metadata)
        
        print(f"\n✅ Build SUCCESS for: {current_config.title}")
        print(f"📂 Location: {book_dir.absolute()}")
        await self.report_progress("complete", 100)
        return book_dir

async def main():
    print("▶ Starting AI Book Factory...")
    factory = BookFactory()
    # In CLI mode, we already integrated the formatting into generate_book
    book_dir = await factory.generate_book()
    print(f"▶ Full asset bundle ready at: {book_dir}")

if __name__ == "__main__":
    asyncio.run(main())
