# 📚 AI BOOK FACTORY

Automatski generiše knjige i priprema ih za Amazon KDP.

**100% BESPLATNO** - koristi besplatne API-je.

## 💰 Kako Zarađuješ

```
1 knjiga = $50-500/mjesec pasivno (prosječno $100)
10 knjiga = $500-5000/mjesec
100 knjiga = $5000-50000/mjesec
```

## 🚀 Quick Start

```bash
# 1. Kloniraj
git clone https://github.com/skugli37/ai-book-factory
cd ai-book-factory

# 2. Instaliraj
pip install -r requirements.txt

# 3. Dodaj Groq API key (besplatan)
export GROQ_API_KEY="gsk_your_key_here"
# Uzmi besplatno na: https://console.groq.com

# 4. Generiši prvu knjigu!
python book_factory.py
```

## 📁 Output

```
books/
└── Your-Book-Title/
    ├── book.md          # Markdown verzija
    ├── book.txt         # Plain text
    ├── book_kdp.docx    # KDP-ready Word dokument
    ├── cover.png        # AI-generisan cover
    ├── metadata.json    # Podaci o knjizi
    └── kdp_checklist.txt # Upload checklist
```

## 🏭 Masovna Proizvodnja

```bash
# Generiši 5 knjiga odjednom
python batch_generator.py 5

# Generiši seriju od 3 knjige
python -c "
import asyncio
from batch_generator import generate_series
asyncio.run(generate_series('The Dark Chronicles', 3))
"
```

## 📖 Profitabilne Niše

Factory automatski bira profitabilne niše:

| Niša | Prosječna zarada | Konkurencija |
|------|------------------|--------------|
| Self-help | $100-300/mj | Srednja |
| Romance | $200-500/mj | Visoka |
| Business | $150-400/mj | Srednja |
| Mystery | $100-250/mj | Srednja |

## 🎨 Cover Generacija

Koristi **Pollinations.ai** - potpuno besplatno, bez API ključa:
- Automatski generiše cover za svaki žanr
- 1600x2560px (KDP optimalno)
- Bez watermark-a

## 📤 Upload na KDP

1. Idi na [kdp.amazon.com](https://kdp.amazon.com)
2. "Create New Title" → "Kindle eBook" ili "Paperback"
3. Upload `book_kdp.docx` kao manuscript
4. Upload `cover.png` kao cover
5. Popuni detalje iz `kdp_checklist.txt`
6. Publish!

## 💡 Pro Tips

### Povećaj kvalitet:
```python
# U book_factory.py, povećaj target_words
config = BookConfig(
    title="My Book",
    genre="self-help", 
    target_words=30000,  # Više riječi = veća cijena
    chapters=15
)
```

### Custom prompt za specifičan stil:
```python
# Dodaj u system prompt
system = """You write like James Clear (Atomic Habits).
Short sentences. Actionable advice. Real examples."""
```

### A/B testiranje naslova:
```python
# Generiši istu knjigu sa različitim naslovima
titles = [
    "Morning Habits: Transform Your Life",
    "The 5AM Secret: What Successful People Know",
    "Rise & Thrive: Morning Routines That Work"
]
# Upload sve tri, vidi koja prodaje najbolje
```

## ⚠️ Važno

1. **UVIJEK pregledaj** generirani sadržaj prije objavljivanja
2. **Dodaj ljudski touch** - uredi, poboljšaj, personaliziraj
3. **Ne spamaj** - kvaliteta > kvantiteta
4. **Prati KDP pravila** - ne objavljuj AI-generated bez pregleda

## 🔧 Tehnički Stack

- **LLM**: Llama 70B via Groq (besplatno, 30 req/min)
- **Slike**: Pollinations.ai (besplatno, neograničeno)
- **Formatting**: python-docx

## 📊 ROI Kalkulacija

```
Troškovi:
- Groq API: $0
- Pollinations: $0
- KDP account: $0
- Vrijeme: ~30 min po knjizi (automated)
UKUPNO: $0

Prihod (konzervativno):
- 1 knjiga proda 10 kopija/mj × $5 = $50/mj
- 10 knjiga = $500/mj
- Za godinu: $6,000

Prihod (optimistično):
- 1 knjiga proda 50 kopija/mj × $5 = $250/mj
- 10 knjiga = $2,500/mj
- Za godinu: $30,000
```

## 🤝 Contributing

PR-ovi dobrodošli! Ideje:
- Više žanrova
- Bolji prompts
- EPUB export
- Automatski KDP upload (API)

## 📜 License

MIT - radi šta hoćeš s ovim.

---

Made with 🤖 by AI Book Factory
