# AI Book Factory: Premium Publishing Mastery 📚🚀

AI Book Factory is an elite, automated publishing engine designed for **Amazon KDP (Kindle Direct Publishing)**. Gone are the days of generic AI filler—this system uses a multi-tier SOTA architecture to produce authoritative, high-depth books ready for the global market.

---

## 💎 Premium Features

### 🧠 High-Depth Authoring Engine
Utilizes the world's most powerful LLMs via **Hugging Face Inference API** (and Groq as a high-speed fallback).
- **Primary Models**: Qwen 2.5 72B-Instruct & Llama 3.1 70B-Instruct.
- **Multi-Pass Generation**: Intelligent logic that detects truncated text and continues seamlessly, ensuring complete, structured chapters.
- **Authoritative Tone**: Custom prompt layering that forbids "AI boilerplate" and mandates deep research integration.

### 🎨 Elite Visual Mastery
A tiered visual engine that creates professional-grade book covers.
- **SOTA Model**: `FLUX.1-dev` (28 steps / 4.5 guidance) for extreme detail.
- **Tiered Reliability**: Automatic failover system (Tier 1: `dev` → Tier 2: `schnell` → Tier 3: `Pillow`).
- **Visual Archetypes**: Genre-specific art direction (Serious Business, Atmospheric Noir, Ethereal Self-Help).

### 🖥️ Glassmorphism Web Dashboard
A stunning, modern interface for managing your publishing empire.
- **Live Progress**: WebSocket-powered real-time generation logs.
- **Digital Library**: A structured "Storefront" view to manage and download your assets.
- **Global Settings**: Easy management of API keys and provider toggles.

### 📦 Automated KDP Asset Bundle
Every generation produces a complete, professional asset pack in `./books/`:
- `book_kdp.docx`: 6x9 formatted manuscript (Garamond/Serif typography).
- `cover.png`: Ultra-HD 1600x2560px cinematic cover.
- `marketing_kit.md`: Sales copy, social posts, and launch emails.
- `metadata.json`: KDP-optimized keywords and categories.
- `kdp_checklist.txt`: Step-by-step upload verification.

---

## 🛠️ Setup & Installation

**Prerequisites**: Python 3.12+ (Optimized for `asyncio.to_thread`).

1. **Clone & Install**
   ```bash
   git clone https://github.com/skugli37/ai-book-factory
   cd ai-book-factory
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   Copy `config.py.example` to `config.py` and supply your credentials:
   - `GROQ_API_KEY`: For high-speed generation.
   - `HF_TOKEN`: For Premium LLMs and Elite covers.

3. **Toggle Providers**
   In `config.py`, you can set your preferred engines:
   ```python
   LLM_PROVIDER = "huggingface" # or "groq"
   IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"
   ```

---

## 🚀 Usage

### Launch the Premium Dashboard
```bash
cd web/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Access the UI at `http://localhost:8000` to start building your library visually.

### CLI Operation (Batch)
To run the factory in automated batch mode:
```bash
python batch_generator.py
```

---

## ⚖️ License
MIT - Created for professional KDP automation paradigms.
