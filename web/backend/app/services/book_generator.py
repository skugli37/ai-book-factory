import sys
import os
from pathlib import Path

# Add the parent directory to sys.path so we can import the original BookFactory
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from book_factory import BookFactory # pyre-ignore[21]
from config import BookConfig # pyre-ignore[21]
from app.websocket.manager import manager # pyre-ignore[21]
import asyncio

class WebBookFactory(BookFactory):
    """Extends BookFactory to send real-time updates via WebSocket."""
    
    def __init__(self, job_id: str, *args, **kwargs): # pyre-ignore[2]
        # Pass send_progress as the callback to the base class
        super().__init__(*args, progress_callback=self.send_progress, **kwargs) # pyre-ignore[19]
        self.job_id = job_id

    async def send_progress(self, stage: str, percent: int, chapter: int = 0, text: str = "", extra_data: dict | None = None):
        update = {
            "stage": stage,
            "percent": percent,
            "chapter": chapter,
            "latest_text": text
        }
        if extra_data:
            update.update(extra_data)
            
        await manager.send_update(self.job_id, update)
        
        # Sync with database if we have the reference
        if hasattr(self, 'db_session') and hasattr(self, 'book_db_obj'):
            self.book_db_obj.progress = percent
            self.book_db_obj.status = stage
            if extra_data and "word_count" in extra_data:
                self.book_db_obj.word_count = extra_data["word_count"]
            self.db_session.commit()

    async def generate_web_book(self, config: BookConfig, db_session, book_db_obj):
        self.db_session = db_session
        self.book_db_obj = book_db_obj
        try:
            # Now generate_book handles everything: Idea -> Outline -> Chapter -> Formatting -> Marketing Kit
            book_dir = await self.generate_book(config)
            
            # Update DB with final results
            book_db_obj.status = "completed"
            
            # The directory name is the safe title slug used by book_factory
            rel_dir = book_dir.name
            
            # Map the standard outputs created by BookFactory
            book_db_obj.docx_path = f"{rel_dir}/book_kdp.docx"
            book_db_obj.marketing_kit_path = f"{rel_dir}/marketing_kit.md"
            db_session.commit()
            
        except Exception as e:
            await self.send_progress("failed", 0, text=str(e))
            book_db_obj.status = "failed"
            db_session.commit()
