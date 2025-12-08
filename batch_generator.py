#!/usr/bin/env python3
"""
BATCH BOOK GENERATOR 📚📚📚
Generiše više knjiga odjednom - MASOVNA PROIZVODNJA
"""

import asyncio
import os
from book_factory import BookFactory, BookConfig

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


async def generate_batch(count: int = 5, genre: str = None):
    """Generiše batch knjiga"""
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║              📚 BATCH BOOK GENERATOR 📚                  ║
    ║                                                          ║
    ║  Generating {count} books...                               ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    factory = BookFactory(GROQ_API_KEY)
    
    results = []
    
    for i in range(count):
        print(f"\n{'='*60}")
        print(f"📚 BOOK {i+1}/{count}")
        print(f"{'='*60}")
        
        try:
            book_dir = await factory.generate_book()
            results.append({"success": True, "path": str(book_dir)})
            print(f"✅ Book {i+1} complete!")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"❌ Book {i+1} failed: {e}")
        
        # Pauza između knjiga (rate limiting)
        if i < count - 1:
            print("\n⏳ Waiting 30 seconds before next book...")
            await asyncio.sleep(30)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 BATCH COMPLETE!")
    print(f"{'='*60}")
    
    success = sum(1 for r in results if r["success"])
    print(f"✅ Successful: {success}/{count}")
    print(f"❌ Failed: {count - success}/{count}")
    
    print("\n📁 Generated books:")
    for i, r in enumerate(results):
        if r["success"]:
            print(f"   {i+1}. {r['path']}")
        else:
            print(f"   {i+1}. FAILED: {r['error']}")


async def generate_series(series_name: str, book_count: int = 3):
    """Generiše seriju povezanih knjiga"""
    
    print(f"\n📚 Generating series: {series_name}")
    print(f"   Books in series: {book_count}")
    
    factory = BookFactory(GROQ_API_KEY)
    
    # Generate series premise
    premise_prompt = f"""Create a premise for a {book_count}-book series called "{series_name}".
    
Include:
- Main character description
- World/setting
- Central conflict
- How it spans {book_count} books

Keep it to 200 words."""
    
    premise = await factory.writer.generate(premise_prompt, max_tokens=400)
    print(f"\n📜 Series premise:\n{premise}\n")
    
    for i in range(book_count):
        book_title = f"{series_name}: Book {i+1}"
        print(f"\n📖 Writing: {book_title}")
        
        config = BookConfig(
            title=book_title,
            genre="fantasy",
            target_words=30000,
            chapters=15,
            description=f"Book {i+1} of the {series_name} series.\n\n{premise}"
        )
        
        await factory.generate_book(config)
        
        if i < book_count - 1:
            await asyncio.sleep(30)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    else:
        count = 3
    
    asyncio.run(generate_batch(count))
