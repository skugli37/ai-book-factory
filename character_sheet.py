import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict

class CharacterSheet:
    """Manages character consistency for fiction books using SQLite."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    name TEXT PRIMARY KEY,
                    traits TEXT,  -- JSON string of traits
                    last_seen_chapter INTEGER,
                    role TEXT
                )
            """)

    def update_character(self, name: str, traits: Dict, chapter: int, role: str = "supporting"):
        """Updates or adds a character to the sheet."""
        traits_json = json.dumps(traits)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO characters (name, traits, last_seen_chapter, role)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    traits = excluded.traits,
                    last_seen_chapter = excluded.last_seen_chapter,
                    role = excluded.role
            """, (name, traits_json, chapter, role))

    def get_all_characters(self) -> str:
        """Returns a formatted string of all characters for LLM context."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name, traits, role FROM characters")
            rows = cursor.fetchall()
            
        if not rows:
            return "No characters defined yet."
            
        output = "CHARACTER SHEET (Consistency Guard):\n"
        for name, traits_json, role in rows:
            traits = json.loads(traits_json)
            traits_str = ", ".join([f"{k}: {v}" for k, v in traits.items()])
            output += f"- {name} ({role}): {traits_str}\n"
        return output

    async def extract_characters_from_text(self, ai_writer, text: str, chapter: int):
        """Uses AI to extract and update character traits from a chapter text."""
        # Ensure text is string and slice safely
        sample_text = str(text)[:4000] # pyre-ignore[6]
        prompt = f"""
        Analyze the following book chapter and extract character details for consistency.
        For each character mentioned, identify their Name, Physical Description (if any), and Personality Traits.
        
        Chapter Text:
        ---
        {sample_text}
        ---
        
        Return ONLY a JSON array of objects:
        [
          {{"name": "...", "role": "protagonist/supporting/antagonist", "traits": {{"hair": "...", "eyes": "...", "personality": "..."}}}}
        ]
        """
        response = await ai_writer.generate(prompt, max_tokens=1000)
        try:
            # Simple cleanup for JSON
            json_str = response.strip().strip('`').replace('json\n', '')
            characters = json.loads(json_str)
            for char in characters:
                self.update_character(char["name"], char["traits"], chapter, char["role"])
        except Exception as e:
            print(f"   ⚠️ Could not update character sheet: {e}")
