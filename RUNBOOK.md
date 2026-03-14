# AI Book Factory 📚 - Production RUNBOOK (Premium)

This runbook provides troubleshooting steps and operational guidelines for the Premium Automated Publishing infrastructure.

---

## 🛠️ Environment & Configuration
Ensure you are using **Python 3.12+** to support `asyncio.to_thread` and modern async-IO operations.

**Mandatory Environmental Variables:**
```bash
export GROQ_API_KEY="your_groq_api_key"
export HF_TOKEN="your_huggingface_token" # Required for Premium LLMs & Elite Covers
```

**Config Settings (`config.py`):**
- `LLM_PROVIDER`: Set to `"huggingface"` for Qwen2.5/Llama-3.1 quality.
- `IMAGE_MODEL`: Set to `"black-forest-labs/FLUX.1-dev"` for elite covers.

---

## 🚀 Execution Guide

### 1. Premium Web Dashboard (Recommended)
The primary way to manage generations visually:
```bash
cd web/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- Access at: `http://localhost:8000`
- Monitor real-time logs via the WebSocket bridge.

### 2. CLI Batch Processing
For massive background generation tasks:
```bash
python batch_generator.py
```

---

## 🔍 Troubleshooting

### 1. "Tier 1" Visual Failure (FLUX.1-dev)
**Symptom:** Logs show `⚠️ [TIER 1] Failed or timed out`.
**Cause:** Hugging Face Inference API is at capacity or model is loading.
**Resolution:** This is handled **automatically**. The system will fallback to Tier 2 (`FLUX.1-schnell`). No manual intervention required.

### 2. Multi-Pass Text Gaps
**Symptom:** Chapter text contains "..." or stops abruptly.
**Cause:** LLM reached `max_tokens` before finishing logic.
**Resolution:** The `AIWriter.generate_long()` logic should detect this and perform a continuation burst. If it fails, check if your `HF_TOKEN` has the necessary permissions for larger models.

### 3. Pyre/Lint Diagnostics
**Symptom:** Static analysis reports `Expected a callable`, `Cannot index into str`, etc.
**Cause:** Type refinement issues in async callbacks or regex results.
**Resolution:** These have been largely resolved in `v2.4.0`. Ensure you are using the latest `writer.py` and `book_factory.py` from the `main` branch.

---

## 📦 KDP Verification Spec
Every book folder contains a `kdp_checklist.txt`. **Do not skip this.** 
Verify that the `book_kdp.docx` mirrors the 6"x9" trim size accurately in your Word processor before final upload. The gutter calculation in `kdp_formatter.py` is exact to Amazon's specifications.
