# AI Book Factory 📚 - Production RUNBOOK

This runbook provides troubleshooting steps and operational guidelines for running the backend batch-generation infrastructure.

## Environment Setup
Ensure you are using Python 3.11+. The system requires `aiohttp`, `python-docx`, and other dependencies explicitly pinned in `requirements.txt`.

**Mandatory Environmental Variable:**
```bash
export GROQ_API_KEY="your_groq_api_key"
```

## System Execution Commands

**Single Iterative Book Generation**
Executes end-to-end for one random niche category.
```bash
python book_factory.py
```

**Batch Generator & SQLite Queue**
Pulls pending metadata templates from internal database and executes within rate limits.
```bash
python batch_generator.py
```

## Known Issues and Troubleshooting

### 1. Rate Limit Exhaustion (Groq 429 Errors)
**Symptom:** Terminal output loops `⚠️ Rate limited. Retrying in Xs...` 
**Cause:** The 20 RPM Free Tier limits have been breached or IP flagged.
**Resolution:** 
- `AIWriter` has a built-in locking mechanism that throttles generation requests to ~19 RPM (once every 3.1 seconds). 
- If errors persist, pause the execution via `CTRL+C`. Pending batch generations are persisted in `batch_queue.db`. You can restart `python batch_generator.py` after an hour safely without losing full progress.

### 2. Formatting Errors: `ValueError: <Style 'Heading 1'> not found`
**Symptom:** `kdp_formatter.py` fails during compilation.
**Cause:** Installed `python-docx` template has deviated. 
**Resolution:** Ensure your environment is clean and default. You can bypass this by editing the fallback in `kdp_formatter.py` to use generic string assignments rather than `<Style>` injection.

### 3. Missing `python-docx` Module Memory Errors
**Symptom:** Document instantiation hangs.
**Cause:** Not running in 64-bit Python 3.11+ for incredibly large books.
**Resolution:** Ensure that your generated books top-out around ~80,000 words maximum for this Python pipeline footprint to be stable locally. 

## KDP Formatting Spec Verification
Before deploying to Amazon, double-check that your Word application renders the docx exactly 6"x9" with the mirrored/left-aligned margins defined in `formatter._calculate_gutter()`. This algorithm calculates precisely to the Amazon Trim specification standards.
