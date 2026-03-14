import json
from pathlib import Path

class MetadataGenerator:
    """Generates KDP-compliant metadata and prep checklist"""

    def __init__(self, book_dir: Path):
        self.book_dir = book_dir

    def generate_kdp_details(self, config_dict: dict, total_words: int, pages: int) -> dict:
        """Generates detailed metadata for KDP upload based on BookConfig"""

        details = {
            "title": config_dict.get("title", ""),
            "subtitle": "",  # Extracted below if exists
            "author_name": config_dict.get("author_name", "AI Publishing House"),
            "description": config_dict.get("description", ""),
            "keywords": config_dict.get("keywords", [])[:7],  # KDP allows max 7 backend keywords
            "categories": self._suggest_categories(config_dict.get("genre", "")),
            "estimated_pages": pages,
            "total_words": total_words,
            "price_suggestions": {
                "ebook": {"min": 2.99, "recommended": 4.99, "max": 9.99},
                "paperback": {"min": 7.99, "recommended": 12.99, "max": 19.99},
            }
        }

        # Parse subtitle
        title_str = str(details.get("title", ""))
        if ":" in title_str:
            parts = title_str.split(":", 1)
            details["title"] = parts[0].strip()
            details["subtitle"] = parts[1].strip()

        return details

    def _suggest_categories(self, genre: str) -> list:
        """Suggests basic BISAC/KDP categories based on genre."""
        genre = genre.lower()
        category_map = {
            "self-help": [
                "Self-Help > Personal Growth > Success",
                "Self-Help > Motivational",
            ],
            "romance": [
                "Romance > Contemporary",
                "Romance > New Adult & College",
            ],
            "business": [
                "Business & Money > Small Business & Entrepreneurship",
                "Business & Money > Personal Finance",
            ],
            "mystery": [
                "Mystery, Thriller & Suspense > Mystery",
                "Mystery, Thriller & Suspense > Cozy Mystery",
            ],
            "fantasy": [
                "Science Fiction & Fantasy > Fantasy",
                "Science Fiction & Fantasy > Epic Fantasy",
            ],
        }
        return category_map.get(genre, ["Fiction > General"])

    def create_upload_checklist(self, details: dict):
        """Creates a text checklist for the KDP upload process."""
        checklist = f"""
======================================================================
                   📋 KDP UPLOAD CHECKLIST
======================================================================

📖 BOOK DETAILS
   Title: {details['title']}
   Subtitle: {details['subtitle'] or 'N/A'}
   Author: {details['author_name']}
   Estimated Pages: {details['estimated_pages']}

📝 DESCRIPTION
{details['description'][:500]}...

🏷️ KEYWORDS (max 7):
{chr(10).join(f'   • {kw}' for kw in details['keywords'])}

📂 CATEGORIES:
{chr(10).join(f'   • {cat}' for cat in details['categories'])}

💰 PRICING SUGGESTIONS:
   Ebook:     ${details['price_suggestions']['ebook']['recommended']:.2f}
   Paperback: ${details['price_suggestions']['paperback']['recommended']:.2f}

📁 FILES TO UPLOAD:
   [ ] book_kdp.docx (manuscript)
   [ ] cover.png (cover image)

✅ PRE-UPLOAD CHECKLIST:
   [ ] Proofread content
   [ ] Check formatting in Kindle Print Previewer
   [ ] Cover meets KDP requirements
   [ ] Description is compelling (HTML bold/italic added if desired)
   [ ] Keywords and categories matched

🔗 UPLOAD AT: https://kdp.amazon.com
"""
        checklist_path = self.book_dir / "kdp_checklist.txt"
        with open(checklist_path, "w", encoding="utf-8") as f:
            f.write(checklist)

        return checklist_path

    def save_metadata_json(self, details: dict):
        """Saves metadata locally"""
        meta_path = self.book_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(details, f, indent=2)
        return meta_path
