#!/usr/bin/env python3
"""
AMAZON KDP FORMATTER 📖
Formatira generirane knjige za Amazon KDP upload

Izlazni formati:
- DOCX (Word) - KDP preferred
- EPUB - za ebook
- PDF - za print
"""

import os
import json
from pathlib import Path
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class KDPFormatter:
    """Formatira knjige za Amazon KDP"""
    
    # KDP preporučene dimenzije
    TRIM_SIZES = {
        "5x8": (5, 8),          # Najpopularnija
        "5.5x8.5": (5.5, 8.5),  # Standardna
        "6x9": (6, 9),          # Veća
    }
    
    def __init__(self, book_dir: Path):
        self.book_dir = Path(book_dir)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> dict:
        """Učitaj metadata"""
        meta_path = self.book_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                return json.load(f)
        return {}
    
    def format_for_kdp(self, trim_size: str = "5.5x8.5") -> Path:
        """Kreiraj KDP-ready DOCX fajl"""
        
        if not HAS_DOCX:
            print("❌ python-docx not installed!")
            print("   Run: pip install python-docx")
            return None
        
        # Učitaj tekst
        txt_path = self.book_dir / "book.txt"
        md_path = self.book_dir / "book.md"
        
        if md_path.exists():
            with open(md_path, encoding="utf-8") as f:
                content = f.read()
        elif txt_path.exists():
            with open(txt_path, encoding="utf-8") as f:
                content = f.read()
        else:
            raise FileNotFoundError("No book content found!")
        
        # Kreiraj Word dokument
        doc = Document()
        
        # Postavi margine (KDP zahtijeva minimum 0.25")
        for section in doc.sections:
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
        
        # Naslovna strana
        title = self.metadata.get("title", "Untitled")
        author = self.metadata.get("author", "Unknown")
        
        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title_para.add_run(title)
        run.bold = True
        run.font.size = Pt(28)
        
        # Author
        doc.add_paragraph()
        author_para = doc.add_paragraph()
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = author_para.add_run(f"by {author}")
        run.font.size = Pt(16)
        
        # Page break
        doc.add_page_break()
        
        # Copyright page
        copyright_text = f"""Copyright © {datetime.now().year} {author}

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the publisher.

This is a work of fiction. Names, characters, businesses, places, events, locales, and incidents are either the products of the author's imagination or used in a fictitious manner.

First Edition: {datetime.now().strftime("%B %Y")}
"""
        
        copyright_para = doc.add_paragraph(copyright_text)
        copyright_para.style.font.size = Pt(10)
        
        doc.add_page_break()
        
        # Sadržaj knjige
        lines = content.split("\n")
        current_chapter = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Detekcija poglavlja
            if line.startswith("## Chapter") or line.startswith("CHAPTER"):
                doc.add_page_break()
                chapter_para = doc.add_heading(line.replace("## ", "").replace("#", ""), level=1)
                chapter_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif line.startswith("# ") and "Chapter" not in line:
                # Skip title, already added
                continue
            elif line.startswith("---"):
                continue
            elif line.startswith("*") and line.endswith("*"):
                # Italic (author line)
                continue
            else:
                # Regular paragraph
                para = doc.add_paragraph(line)
                para.style.font.size = Pt(11)
                # First line indent
                para.paragraph_format.first_line_indent = Inches(0.3)
        
        # Sačuvaj
        output_path = self.book_dir / "book_kdp.docx"
        doc.save(output_path)
        
        print(f"✅ KDP-ready DOCX saved: {output_path}")
        return output_path
    
    def generate_kdp_details(self) -> dict:
        """Generiši detalje za KDP upload"""
        
        details = {
            "title": self.metadata.get("title", ""),
            "subtitle": "",  # Extract from title if has ":"
            "author": self.metadata.get("author", ""),
            "description": self.metadata.get("description", ""),
            "keywords": self.metadata.get("keywords", [])[:7],  # KDP max 7
            "categories": self._suggest_categories(),
            "price_suggestions": {
                "ebook": {"min": 2.99, "recommended": 4.99, "max": 9.99},
                "paperback": {"min": 7.99, "recommended": 12.99, "max": 19.99},
            }
        }
        
        # Parse subtitle
        if ":" in details["title"]:
            parts = details["title"].split(":", 1)
            details["title"] = parts[0].strip()
            details["subtitle"] = parts[1].strip()
        
        return details
    
    def _suggest_categories(self) -> list:
        """Predloži KDP kategorije na osnovu žanra"""
        
        genre = self.metadata.get("genre", "").lower()
        
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
    
    def create_upload_checklist(self) -> str:
        """Kreiraj checklist za KDP upload"""
        
        details = self.generate_kdp_details()
        
        checklist = f"""
╔══════════════════════════════════════════════════════════════╗
║                📋 KDP UPLOAD CHECKLIST                       ║
╚══════════════════════════════════════════════════════════════╝

📖 BOOK DETAILS
   Title: {details['title']}
   Subtitle: {details['subtitle'] or 'N/A'}
   Author: {details['author']}
   
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
   ☐ book_kdp.docx (manuscript)
   ☐ cover.png (cover image)
   
✅ PRE-UPLOAD CHECKLIST:
   ☐ Proofread content
   ☐ Check formatting in Kindle Previewer
   ☐ Cover meets KDP requirements (min 1000x1600px)
   ☐ Description is compelling
   ☐ Keywords researched
   ☐ Price set competitively

🔗 UPLOAD AT:
   https://kdp.amazon.com
"""
        
        # Save checklist
        checklist_path = self.book_dir / "kdp_checklist.txt"
        with open(checklist_path, "w") as f:
            f.write(checklist)
        
        print(checklist)
        return checklist


def format_all_books():
    """Formatiraj sve generirane knjige"""
    
    books_dir = Path("./books")
    
    if not books_dir.exists():
        print("❌ No books directory found!")
        return
    
    for book_dir in books_dir.iterdir():
        if book_dir.is_dir():
            print(f"\n📖 Processing: {book_dir.name}")
            
            formatter = KDPFormatter(book_dir)
            
            try:
                formatter.format_for_kdp()
                formatter.create_upload_checklist()
            except Exception as e:
                print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    format_all_books()
