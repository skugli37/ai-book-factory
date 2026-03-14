import asyncio
import sqlite3
import json
import sys
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import BookConfig, GROQ_API_KEY  # pyre-ignore[21]
from book_factory import BookFactory  # pyre-ignore[21]

DB_FILE = "batch_queue.db"

class BatchQueueDB:
    """SQLite Persistence for Batch Book Generation queue."""
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS books_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_name TEXT,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    error_log TEXT,
                    completed_path TEXT
                )
            ''')

    def add_book(self, config: BookConfig, series_name: str | None = None) -> int | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO books_queue (series_name, title, genre, config_json) VALUES (?, ?, ?, ?)",
                (series_name, config.title, config.genre, json.dumps(asdict(config)))
            )
            return cursor.lastrowid

    def get_pending_books(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM books_queue WHERE status = 'PENDING'")
            return [dict(row) for row in cursor.fetchall()]

    def update_status(self, book_id: int, status: str, error_log: str | None = None, path: str | None = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE books_queue SET status = ?, error_log = ?, completed_path = ? WHERE id = ?",
                (status, error_log, path, book_id)
            )

class BatchGenerator:
    """Async Semaphore controlled batch worker for BookFactory."""
    
    def __init__(self, max_concurrent: int = 5):
        # We limit max concurrent books overall. 
        # Note: Groq rate limits are internally managed inside BookFactory (20 RPM token bucket).
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_db = BatchQueueDB()
        self.factory = BookFactory(GROQ_API_KEY)

    async def _process_book(self, book_record: dict):
        book_id = book_record['id']
        config = BookConfig(**json.loads(book_record['config_json']))
        
        async with self.semaphore:
            self.queue_db.update_status(book_id, "PROCESSING")
            print(f"🔄 Starting job for: {config.title}")
            try:
                # Factory will handle internal limits and rate retries
                book_dir = await self.factory.generate_book(config)
                
                # Automatically format it to DOCX upon completion
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                from kdp_formatter import KDPFormatter  # pyre-ignore[21]
                try:
                    formatter = KDPFormatter(book_dir)
                    formatter.format_for_kdp()
                    formatter.create_upload_checklist(
                        formatter.metadata.get("kdp_details", formatter.metadata)
                    )
                except Exception as fmt_err:
                    print(f"⚠️ Book compiled but DOCX formatting failed: {fmt_err}")
                
                self.queue_db.update_status(book_id, "COMPLETED", path=str(book_dir))
                print(f"✅ Finished job for: {config.title}")
            except Exception as e:
                self.queue_db.update_status(book_id, "ERROR", error_log=str(e))
                print(f"❌ Failed job for {config.title}: {e}")

    async def run_queue(self):
        """Processes all pending items in the sqlite queue."""
        pending = self.queue_db.get_pending_books()
        if not pending:
            print("No pending books in queue.")
            return

        print(f"🚀 Starting batch processing of {len(pending)} books...")
        tasks = [self._process_book(record) for record in pending]
        
        # Run them all, bounded by semaphore
        await asyncio.gather(*tasks)
        print("🎉 Batch run finalized.")

    async def queue_series(self, series_name: str, genre: str, count: int = 3):
        """Generates dynamic config metadata for a unified series and queues them."""
        
        print(f"🌎 Worldbuilding Series: {series_name}...")
        
        # Build a shared lore premise using the first book factory call
        premise_prompt = f"""Create a cohesive worldbuilding premise for a {count}-book {genre} series called "{series_name}".
Include: Main protagonist name, the core setting, and the overarching plot spanning all books. Keep it to 250 words."""
        
        premise = await self.factory.writer.generate(premise_prompt)
        
        print(f"📜 Series Lore:\n{premise[:300]}...\n")

        for i in range(count):
            book_title = f"{series_name}: Book {i+1}"
            
            # Simple metadata building
            config = BookConfig(
                title=book_title,
                genre=genre,
                target_words=35000,
                chapters=14,
                description=f"Book {i+1} in the episodic {series_name} series.\n\nLore:\n{premise}"
            )
            self.queue_db.add_book(config, series_name=series_name)
            print(f"   📥 Queued: {book_title}")

async def main():
    bg = BatchGenerator(max_concurrent=3)
    
    # Example: seed the database and run
    # await bg.queue_series("The Starlit Chronicles", "fantasy", count=3)
    
    await bg.run_queue()

if __name__ == "__main__":
    asyncio.run(main())
