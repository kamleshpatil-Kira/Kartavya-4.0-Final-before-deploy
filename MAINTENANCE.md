# Maintenance & Run Guide

This document tracks all manual changes, provides instructions for running the application, and troubleshooting tips.

## 🚀 How to Run

### Option 1: Docker (Recommended)
```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

### Option 2: Manual Start
```bash
# 1. Add local bin to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run backend
cd backend
uvicorn main:app --reload --port 8000

# 4. Run frontend (new terminal)
cd frontend
npm run dev
```

---

## 📂 File Locations

| File Type | Location | Description |
|-----------|----------|-------------|
| **xAPI Zips** | `output/` inside project folder | Generated scorm packages |
| **Images** | `uploads/` | User uploaded images |
| **Logs** | `logs/` | Application error logs |
| **Config** | `config.py` & `.env` | API Keys and settings |

**Note:** When you click "Download" in the app, files go to your browser's default **Downloads** folder.
The "Generate" button creates files in the project's **`output/`** folder.

---

## 🛠️ Manual Changes & Fixes (Log)

If you need to revert or apply these changes to another version, follow these steps:

### 1. Fix: Missing `utils` folder
**Issue:** App crashed with `ModuleNotFoundError: No module named 'utils'`.
**Fix:** Verify the `utils/` folder exists in the project root. It must contain:
- `logger.py`
- `document_processor.py`
- `course_loader.py`
- `qa_validator.py`

### 2. Fix: `pyaudioop` Dependency
**Issue:** Installation failed because `pyaudioop` is not available for Python 3.10+.
**Fix:** Removed `pyaudioop>=0.2.0` from `requirements.txt`.

### 3. Fix: JSON Error in Quiz Generation
**Issue:** "Unterminated string" error when generating quizzes.
**Fix:** Updated `services/gemini_service.py`:
- In `_generate_content_with_timeout`, added support for `generation_config`.
- In `generate_quiz`, set `max_output_tokens` to `8192` and `response_mime_type` to `"application/json"`.

---

## ❓ Troubleshooting

### "Invalid JSON response"
- **Cause:** AI response was cut off (too long).
- **Solution:** We increased the token limit in `gemini_service.py`. If it persists, try reducing the number of quiz questions in `config.py`.

### "Module not found"
- **Solution:** Ensure you are running the app from the root project directory and all folders (`utils`, `services`, `generators`) are present.
