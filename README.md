# AI Book Factory 📚

An automated content generation system for Amazon KDP (Kindle Direct Publishing), functioning entirely on 100% free-tier APIs.

## Architecture & Features

This tool leverages massive LLM generation via **Groq** and professional AI image generation through **Hugging Face**, plus real-time fact-checking via **DuckDuckGo**, to produce production-ready, KDP-compliant documents.

- **Zero Cost**: End-to-end publishing pipeline using 100% free-tier APIs (Groq, Hugging Face, DDG).
- **Live Research**: Integrated DuckDuckGo search engine with Groq summarization for up-to-date facts in every chapter.
- **Docx Formatting**: Directly emits Amazon KDP-ready `6x9` print and Kindle ebook formats with dynamic gutter sizing.
- **Batch Processing**: Squeeze 5-10 books through a resilient local SQLite job queue with rate limit backoffs.
- **Hands-off Operations**: Asynchronous pipeline that automatically develops ideas, generates cover art, authors chapter content, formats `.docx` binaries, and delivers deployment checklists.

## Output Structure

The system deposits successful runs into `./books/`:
```text
books/{title_slug}/
├── book.md                 # Unformatted Markdown version
├── book.txt                # Plain text version
├── book_kdp.docx           # KDP-formatted 6x9 manuscript ready for print/Kindle upload 
├── cover.png               # AI-generated Flux.1-schnell cover (1600x2560px)
├── metadata.json           # Title, author, genre, keywords, pages
└── kdp_checklist.txt       # Pre-upload validation instruction log & checklist
```

## Setup Instructions

**Prerequisites:** Python 3.11+ 

1. **Clone & Install**
   ```bash
   git clone https://github.com/skugli37/ai-book-factory
   cd ai-book-factory
   pip install -r requirements.txt
   ```

2. **Supply your API Keys**
   The project uses Groq for text and Hugging Face for covers. 

   ```bash
   export GROQ_API_KEY="gsk_your_key_here"
   export HF_TOKEN="hf_your_token_here"
   ```

3. **Validate the Configuration**
   Review `config.py` against your specific use case. You can manually adjust the `BookConfig` defaults, edit the available profitable niches, or set explicit target words limits.

## How to Usage

### Single Random Book Generation

```bash
python book_factory.py
```
This single execution command will select a random, viable Amazon niche category (e.g. self-help, romance) and automatically spin up a full ~20k-50k word book, saving the `.docx` and `.png` cover output.

### Batch & Series Generation

To generate multiple related or random books utilizing the internal batch throttle queue (which respects Groq's 20 RPM bucket):

```bash
python batch_generator.py
```
*(By default, this will run pending books queued in the sqlite database. See `batch_generator.py` implementation if you want to dynamically inject specific titles.)*

## KDP Upload

You will receive a copy of `kdp_checklist.txt` inside your resultant book folder.
Access [kdp.amazon.com](https://kdp.amazon.com), start a new Kindle eBook or Paperback project, and follow your customized checklist to plug your book in and publish perfectly.

## License

MIT - See [LICENSE](LICENSE)

*Created for educational automation paradigms around KDP pipelines.*
