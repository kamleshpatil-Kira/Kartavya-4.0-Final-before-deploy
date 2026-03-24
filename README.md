# 📚 Kartavya-4.0 — AI Course Generation System

**Full-Access Developer & User Guidebook**

An AI-powered platform that generates complete, interactive e-learning courses — with text, images, audio narration, knowledge checks, quizzes, flashcards, and certificates — then packages everything into an **xAPI/TinCan-compliant ZIP** ready for upload to any LMS (Learning Management System).

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI%20%2B%20Next.js-red)
![Tracking](https://img.shields.io/badge/xAPI-v1.0.3-green)
![LMS](https://img.shields.io/badge/LMS-Compatible-orange)

---

## Table of Contents

1. [What Does This Project Do?](#what-does-this-project-do)
2. [Prerequisites](#prerequisites)
3. [Setup (Step by Step)](#setup-step-by-step)
4. [How to Run](#how-to-run)
5. [Using the App — The 4-Step Wizard](#using-the-app--the-4-step-wizard)
6. [Generation Pipeline (What Happens Behind the Scenes)](#generation-pipeline-what-happens-behind-the-scenes)
7. [Output — What You Get](#output--what-you-get)
8. [Project Structure & File-by-File Reference](#project-structure--file-by-file-reference)
9. [xAPI Tracking & LMS Integration (Deep Dive)](#xapi-tracking--lms-integration-deep-dive)
10. [Bug Fix Log — Missing LMS Field Injection](#bug-fix-log--missing-lms-field-injection)
11. [Configuration Reference](#configuration-reference)
12. [Troubleshooting](#troubleshooting)

---

## What Does This Project Do?

You provide a **course title**, **target audience**, and some context — the system then:

1. **Generates a course outline** (4–5 modules by default) using Google Gemini AI
2. **Writes detailed content** for each module with real-world scenarios
3. **Creates knowledge checks** (quiz questions per module)
4. **Generates images** for each module using Gemini image generation
5. **Produces audio narration** (American/British/Indian accents, male/female voices)
6. **Builds a final quiz** (10 questions, 80% passing score, 3 attempts)
7. **Auto-generates a certificate** upon quiz pass
8. **Packages everything** into an xAPI ZIP file you can upload to your LMS

The entire process runs through a simple web interface — no coding required from the end user.

---

## Prerequisites

| Requirement | Minimum Version    | How to Check        |
| ----------- | ------------------ | ------------------- |
| **Python**  | 3.8+               | `python3 --version` |
| **pip**     | Any recent version | `pip --version`     |

### API Keys Required

| API Key          | What It's Used For                                   | Where to Get It                                        |
| ---------------- | ---------------------------------------------------- | ------------------------------------------------------ |
| `GEMINI_API_KEY` | AI content generation + TTS audio + image generation | [Google AI Studio](https://aistudio.google.com/apikey) |


---

## Setup (Step by Step)

### Step 1 — Download/Clone the Project

```bash
git clone <repository-url>
cd "Kartavya-3.0"
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages: FastAPI, Google Generative AI SDK, Pillow, ReportLab (PDF generation), python-docx/PyPDF2/python-pptx (document parsing), and more.

### Step 3 — Set Up Your API Keys

You can set up your API keys in two ways:

#### Option 1: System-wide (Recommended for Deployment/Seniors)
Add the key to your system's environment file:
```bash
sudo vi /etc/environment
# Add this line at the bottom:
GEMINI_API_KEY=your_actual_gemini_key_here

# Export it properly so Docker can read it:
set -a; source /etc/environment; set +a
```

#### Option 2: Local `.env` file (For Local Development)
Create a `.env` file in the project root:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-3-pro-preview
```

> **⚠️ Important:** Never commit your `.env` file to Git. It is already in `.gitignore`.

### Step 4 — Verify Folder Structure

These folders are created automatically on first run, but verify they exist:

```
Kartavya-3.0/
├── services/       ← AI service integrations (must exist)
├── generators/     ← xAPI package builder (must exist)
├── utils/          ← Logging, document processing (must exist)
├── uploads/        ← Created automatically
├── output/         ← Created automatically
├── temp/           ← Created automatically
└── logs/           ← Created automatically
```

✅ **Setup complete!** You're ready to run.

---

## How to Run

### Option A — Full Stack with Docker (Recommended)

Ensure `GEMINI_API_KEY` is set in your system environment (see Step 3) or a `.env` file, then:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Open:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/health`

> **Note:** Docker Compose is configured to automatically pass `GEMINI_API_KEY` from your host system to the containers.
> The Docker backend image installs `fonts-dejavu-core`, `fonts-lohit-devanagari`, and `fonts-droid-fallback` automatically for multi-language PDF support.

### Option B — Local Dev (without Docker)

Backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Frontend (new terminal):
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

---

## Using the App — The 4-Step Wizard

The web UI walks you through a 4-step wizard:

### Step 1 — Choose Generation Mode

| Mode                   | When to Use                                      |
| ---------------------- | ------------------------------------------------ |
| **Start from Scratch** | Create a brand new course from your inputs       |
| **Regenerate**         | Regenerate a previously created course           |
| **Edit**               | Modify specific parts of an existing course      |
| **Duplicate**          | Create a copy of an existing course with changes |

Click the card for your chosen mode, then click **Next →**.

### Step 2 — Course Information & Content Options

| Field               | Description                        | Example                                |
| ------------------- | ---------------------------------- | -------------------------------------- |
| **Course Title**    | Name of the course                 | "Food Safety and Hygiene Practices"    |
| **Target Audience** | Who will take this course          | "Restaurant staff and food handlers"   |
| **Institute**       | Organization name (optional)       | "Hygiena LLC"                          |
| **Relevant Laws**   | Guidelines the content must follow | "FDA Food Code 2022, OSHA Standards"   |
| **Tone**            | Select one or more                 | Professional, Friendly, Academic, etc. |
| **Number of Modules** | How many modules (1–10)          | 4                                      |
| **Course Level**    | Beginner, Intermediate, Advanced   | Intermediate                           |
| **Flashcards**      | Add recall cards (On/Off)          | Off                                    |
| **Final Quiz**      | Add comprehensive quiz (On/Off)    | Off                                    |
| **Generate Outline Only** | Outline without full content | No                                     |

You can also upload reference documents (`.docx`, `.pdf`, `.pptx`, `.zip`) — the AI uses them to generate more relevant content.

> **Note:** When "Generate Outline Only" is set to Yes, the Flashcards and Final Quiz options are automatically disabled (not applicable for outline-only generation).

### Step 3 — Audio & Media

| Option            | Choices                     |
| ----------------- | --------------------------- |
| **Include Audio** | Yes / No                    |
| **Accent**        | American, British, Indian   |
| **Voice Gender**  | Male, Female                |
| **Speech Speed**  | 0.5× to 2.0× (default 1.0×) |

### Step 4 — Review & Confirm

Review all your selections. Check the confirmation box and click **🚀 Generate Course**.

Generation takes **2–10 minutes** depending on the number of modules. A progress bar shows the current status.

---

## Generation Pipeline (What Happens Behind the Scenes)

```
User Input
    ↓
1. Course Outline         →  Gemini AI generates module titles & descriptions
    ↓
2. Module Content         →  Detailed text content for each module
    ↓
3. Knowledge Checks       →  1 quiz question per module (inline)
    ↓
4. Flashcards (optional)  →  Key concept flip cards per section
    ↓
5. Image Generation       →  Gemini creates realistic images per module
    ↓
6. Audio Generation       →  Google TTS generates narration (per section, auto-chunked)
    ↓
7. Final Quiz             →  10-question quiz (80% to pass, 3 attempts)
    ↓
8. QA Validation          →  Content validated for quality, compliance, hallucinations
    ↓
9. xAPI Packaging         →  Bundles everything into an LMS-ready ZIP
    ↓
Download ZIP
```

| Pipeline Step        | Service Used     | File Responsible                  |
| -------------------- | ---------------- | --------------------------------- |
| Orchestration        | —                | `services/course_generator.py`    |
| Content generation   | Google Gemini AI | `services/gemini_service.py`      |
| Audio generation     | Google Cloud TTS | `services/google_tts_service.py`  |
| Flashcard generation | Google Gemini AI | `services/flashcard_generator.py` |
| QA validation        | —                | `utils/qa_validator.py`           |
| xAPI package builder | —                | `generators/xapi_generator.py`    |
| PDF export           | ReportLab        | `generators/pdf_generator.py`     |

---

## Output — What You Get

After generation, click **Download** to get a `.zip` file:

```
YourCourse.zip/
├── index.html              ← Complete interactive course (open in any browser)
├── tincan.xml              ← xAPI/TinCan manifest for LMS compliance
├── course.json             ← Course data and metadata
└── assets/
    ├── styles.css          ← Course styling (responsive, modern design)
    ├── script.js           ← Course interactivity & xAPI tracking logic
    ├── xapiwrapper.min.js  ← ADL xAPI Wrapper library (v1.11.0)
    ├── module-1.png        ← Generated images
    ├── module-2.png
    ├── audio-m1-s1.mp3     ← Generated audio (per section, auto-chunked)
    ├── audio-m1-s2.mp3
    └── ...
```

### How to use the output:

- **Preview locally:** Open `index.html` in a browser
- **LMS deployment:** Upload the `.zip` directly to your LMS (SCORM Cloud, emPower, Moodle, TalentLMS, etc.)
- **Files are also saved** in the project's `output/` folder

### Course Features in the Output:

- ✅ Home screen with course overview and learning objectives
- ✅ Course Instructions page with audio narration
- ✅ Module-by-module navigation with sidebar progress tracking
- ✅ Audio narration per section (seekbar locked — no skipping forward)
- ✅ Knowledge checks per module (must answer correctly to proceed)
- ✅ Interactive flashcards per section (if enabled)
- ✅ Final quiz with 80% passing score and 3 retry attempts
- ✅ Certificate of completion on quiz pass
- ✅ xAPI statement tracking (reports progress to LMS)
- ✅ LMS field injection (portalId, studentID, subscriptionId, identifier)
- ✅ State API integration for progress persistence
- ✅ Responsive design (desktop, tablet, mobile)

---

## Project Structure & File-by-File Reference

```
Kartavya-3.0/
│
├── backend/                             ← FastAPI backend
│   └── main.py                          ← API entry point
├── frontend/                            ← Next.js frontend
│   └── app/                             ← UI pages and components
├── config.py                            ← Configuration & Environment Variables
├── requirements.txt                     ← Python dependencies
├── .env                                 ← API keys (do NOT commit to Git)
├── .env.example                         ← Template for .env
├── xapiwrapper.min.js                   ← ADL xAPI Wrapper v1.11.0 source
│
├── Dockerfile.backend                   ← Docker image for FastAPI backend
├── Dockerfile.frontend                  ← Docker image for Next.js frontend
├── docker-compose.prod.yml              ← Production Docker Compose
├── Jenkinsfile                          ← Jenkins CI/CD pipeline
│
├── services/                            ← AI Service Integrations
│   ├── __init__.py
│   ├── course_generator.py              ← Orchestrates the full generation pipeline
│   ├── gemini_service.py                ← Google Gemini AI (content & outlines)
│   ├── google_tts_service.py            ← Google TTS (audio narration)
│   └── flashcard_generator.py           ← Flashcard content generation
│
├── generators/                          ← Output Generators
│   ├── __init__.py
│   ├── xapi_generator.py               ← CORE: Builds the xAPI HTML/JS/CSS/ZIP package
│   └── pdf_generator.py                 ← PDF export via ReportLab (multi-language)
│
├── utils/                               ← Utilities
│   ├── __init__.py
│   ├── document_processor.py            ← Parses uploaded .docx/.pdf/.pptx/.zip files
│   ├── course_loader.py                 ← Loads existing course data (JSON, ZIP, docs)
│   ├── qa_validator.py                  ← Validates content quality & compliance
│   └── logger.py                        ← Structured JSON logging
│
├── deploy/                              ← Deployment guides
│   ├── DEPLOY_JENKINS.md                ← Jenkins CI/CD setup guide
│   └── DEPLOY_FULLSTACK.md              ← Manual full-stack deploy guide
│
├── uploads/                             ← User-uploaded reference documents
├── output/                              ← Generated course ZIP files
├── temp/                                ← Temporary files during generation
├── logs/                                ← Application logs
│   ├── course_generator.log             ← All logs (JSON format)
│   └── error.log                        ← Error logs only
│
├── MAINTENANCE.md                       ← Troubleshooting & manual fixes log
├── DEPLOYMENT.md                        ← Cloud deployment guide
└── CHANGELOG.md                         ← Version history
```

---

### Detailed File Functionality Guide

#### Entry Points

| File                       | Purpose                                                                                                                                                                                                                                                                        |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`backend/main.py`**      | FastAPI API entry point used by the frontend. Exposes generation, audio, history, download, image mapping, and health endpoints.                                                                                                                                             |
| **`frontend/app/*`**       | Next.js app router UI for generation wizard, history, view/edit flow, settings, and image mapping.                                                                                                                                                                           |
| **`config.py`** (59 lines) | Loads environment variables from `.env`, defines all paths (`uploads/`, `output/`, `temp/`, `logs/`), sets generation defaults (4–5 modules, 10 quiz questions, 140–160 WPM audio), and selects the Gemini model. Auto-creates missing directories on import.                  |

---

#### `services/` — AI Service Integrations

| File                         | Lines | What It Does                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`course_generator.py`**    | 828   | **The orchestrator.** Coordinates the entire pipeline: calls Gemini for outlines → content → knowledge checks, calls TTS for audio, calls flashcard generator, runs QA validation, then packages via xAPI generator. Handles all 4 modes: Scratch, Regenerate, Edit, Duplicate. Has `_generate_full_course()` (main flow) and `_edit_course()` (partial updates).                                      |
| **`gemini_service.py`**      | 1,117 | **AI content engine.** Interfaces with Google Gemini API. Has functions for: generating course outlines (`generate_course_outline`), module content (`generate_module_content`), knowledge checks (`generate_knowledge_check`), quizzes (`generate_quiz`), and quiz scrambling. Includes auto-fallback between Gemini models (e.g., pro → flash) on quota errors, timeout handling, JSON response parsing, and symbol cleanup. |
| **`google_tts_service.py`**  | 773   | **Audio narration.** Generates speech from text using Google Cloud TTS. Supports 3 accents (American/British/Indian), male/female voices, configurable speed. Auto-chunks long text into 4,000-byte segments (Google's limit), generates each chunk separately, returns paths for sequential playback. Includes per-section audio generation.                                                                                  |
| **`flashcard_generator.py`** | 174   | **Flashcard content.** Generates interactive flip-card content for each module section using Gemini AI. Creates front (question/term) and back (answer/definition) pairs. Truncates text to keep cards crisp.                                                                                                                                                                                                                  |

---

#### `generators/` — Output Package Generators

| File                    | Lines | What It Does                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`xapi_generator.py`** | 5,768 | **The core engine.** This single file generates the entire course output package. It contains: (1) Python class `xAPIGenerator` that builds `index.html`, `tincan.xml`, `course.json`, copies assets; (2) The complete CSS (~1,400 lines) for the responsive course UI; (3) The complete JavaScript (~2,300 lines) for all interactivity — module navigation, sidebar, audio player controls (seekbar locking), knowledge check validation, quiz logic (80% pass, 3 attempts), flashcard flip animations, certificate generation, xAPI statement sending, LMS field injection, State API persistence, and SCORM Cloud actor normalization. |
| **`pdf_generator.py`**  | 325   | **PDF export.** Uses ReportLab to generate a PDF version of the course content (text + images, no audio). Used for offline/printable course materials.                                                                                                                                                                                                                                                                                                                                                                                                                     |

---

#### `utils/` — Utility Modules

| File                        | Lines | What It Does                                                                                                                                                                                                                                                                                     |
| --------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`document_processor.py`** | 301   | **File parser.** Processes uploaded reference documents. Supports `.docx` (python-docx), `.pdf` (PyPDF2), `.pptx` (python-pptx), `.zip` (recursive extraction), audio files (Whisper transcription), and video files (extract audio → transcribe). Returns extracted text content for AI to use. |
| **`course_loader.py`**      | 155   | **Course data loader.** Loads existing course data for Edit/Regenerate/Duplicate modes. Supports JSON files, xAPI ZIP packages (extracts `course.json`), and document files. Extracts course titles from filenames or document headings.                                                         |
| **`qa_validator.py`**       | 237   | **Quality assurance.** Validates generated content for: correct module/section structure, knowledge check format (question + 4 options + correct answer + feedback), quiz format, hallucination indicators, word count adequacy, and compliance with source material. Returns list of issues.    |
| **`logger.py`**             | 118   | **Structured logging.** Sets up JSON-formatted logging to `logs/course_generator.log` (all events) and `logs/error.log` (errors only). Console output with timestamps. Helper functions for logging activities, errors, API calls, and generation progress.                                      |

---

## xAPI Tracking & LMS Integration (Deep Dive)

This section explains how xAPI tracking works in the generated courses, critical for understanding LMS compatibility.

### How xAPI Works in This Project

The generated `index.html` includes the **ADL xAPI Wrapper** (`xapiwrapper.min.js`) which communicates with the LMS's Learning Record Store (LRS).

When a course is launched from an LMS, the LMS passes parameters via URL query string:

```
index.html?endpoint=https://lrs.example.com/xapi/&auth=Basic+xxx&actor={...}&registration=uuid&activity_id=http://...
```

The JavaScript in `script.js` (generated by `xapi_generator.py`) does the following on page load:

1. **Parses URL parameters** — extracts `endpoint`, `auth`, `actor`, `registration`, `activity_id`
2. **Parses LMS-specific parameters** — extracts `portalId`, `studentID`, `subscriptionId`, `identifier`
3. **Normalizes the actor** — SCORM Cloud sends non-standard field names (`accountServiceHomePage` → `homePage`, `accountName` → `name`) and arrays instead of single values. The code fixes these automatically.
4. **Initializes xAPI connection** — sets up the ADL wrapper with endpoint and auth

### What xAPI Statements Are Sent

The course sends statements to the LRS at these key moments:

| Event                    | Verb                | When                        |
| ------------------------ | ------------------- | --------------------------- |
| Course started           | `experienced`       | User starts the course      |
| Module viewed            | `experienced`       | User navigates to a module  |
| Image viewed             | `viewed`            | Module image loads          |
| Audio listened           | `listened`          | Audio playback completes    |
| Audio paused             | `paused`            | User pauses audio           |
| Knowledge check answered | `answered`          | User answers a KC question  |
| Quiz completed           | `passed` / `failed` | User submits the final quiz |
| Course completed         | `completed`         | User passes the quiz        |

### Dual Statement Functions

The generated JavaScript contains **two** statement-sending functions:

1. **`sendStatement(verb, objectId, objectName, ...)`** — The primary function used for most events (module views, audio, images). It builds statements with the LMS launch parameters (actor, registration, context).

2. **`sendXAPIStatement(verb, objectType, objectId, options)`** — An enhanced version used for course-level events (quiz completion, course completion). Provides more flexible options for result data and context.

**Both functions** inject the LMS-specific fields (`portalId`, `studentID`, `subscriptionId`, `identifier`) into every statement.

### SCORM Cloud vs emPower LMS Compatibility

| Feature       | SCORM Cloud           | emPower LMS                                             |
| ------------- | --------------------- | ------------------------------------------------------- |
| Launch params | Standard xAPI         | Standard + custom fields                                |
| Actor format  | Arrays (non-standard) | Standard                                                |
| Custom fields | Not needed            | `portalId`, `studentID`, `subscriptionId`, `identifier` |
| State API     | Supported             | Supported                                               |

The code **auto-detects** the environment:

- If custom URL params exist (emPower), it adds them to every statement
- If they don't exist (SCORM Cloud), it sends standard statements
- Actor normalization fixes SCORM Cloud's non-standard format automatically

### State API (Progress Persistence)

The course uses the xAPI State API to save and restore learner progress:

- **Saves:** Current module, completed modules, quiz attempts, audio progress
- **Restores:** On re-launch, the learner continues where they left off
- **State resource ID:** Based on course URI + registration ID

---

## Bug Fix Log — Missing LMS Field Injection

### The Problem

The file `generators/xapiGenerator.js` (the **legacy JavaScript generator**) contained a `sendXAPIStatement` function that:

1. ✅ Correctly parsed LMS parameters from the URL (`portalId`, `studentID`, `subscriptionId`, `identifier`)
2. ✅ Correctly added them to the xAPI statement object
3. ❌ **Never actually sent the statement** — the `ADL.XAPIWrapper.sendStatement(statement)` call was **commented out**

```javascript
// BEFORE (buggy):
// Send statement (configure endpoint as needed)
// ADL.XAPIWrapper.sendStatement(statement);
```

### The Impact

If any part of the pipeline used the `xapiGenerator.js` output instead of `xapi_generator.py`, **all xAPI statements** would be built but never transmitted to the LRS — making them completely invisible in the emPower LMS xAPI Report.

### The Fix

The commented-out line was replaced with an active send call wrapped in error handling:

```javascript
// AFTER (fixed):
// Send statement to LRS
try {
  ADL.XAPIWrapper.sendStatement(statement, function (resp, obj) {
    console.log("xAPI statement sent:", verb, objectType, resp.status);
  });
} catch (e) {
  console.error("Failed to send xAPI statement:", e);
}
```

### Files Affected

| File                                     | Status                                                                             |
| ---------------------------------------- | ---------------------------------------------------------------------------------- |
| `generators/xapiGenerator.js` line ~1032 | ✅ Fixed — `sendStatement` now active                                              |
| `generators/xapi_generator.py`           | ✅ No issue — both `sendStatement()` and `sendXAPIStatement()` were already active |

### How to Verify

After deploying a course generated by the fixed code:

1. Open browser DevTools → Console
2. Interact with the course (view modules, answer quizzes)
3. You should see: `xAPI statement sent: completed quiz 200`
4. Check the LMS xAPI Report — statements should now appear with `portalId`, `studentID`, etc.

---

## Configuration Reference

All settings are in `config.py` and can be overridden via `.env` file or system environment variables.

### API Keys & Server

| Variable         | Required | Default                | Description                        |
| ---------------- | -------- | ---------------------- | ---------------------------------- |
| `GEMINI_API_KEY` | **Yes**  | —                      | Google Gemini API key              |
| `GEMINI_MODEL`   | No       | `gemini-3-pro-preview` | AI model to use                    |
| `PORT`           | No       | `8000`                 | Server port                        |
| `HOST`           | No       | `0.0.0.0`              | Server host                        |
| `DEBUG`          | No       | `False`                | Enable debug mode                  |
| `LOG_LEVEL`      | No       | `INFO`                 | Logging level (DEBUG/INFO/WARNING) |

### Generation Defaults

| Setting              | Value | Description                      |
| -------------------- | ----- | -------------------------------- |
| `MIN_MODULES`        | 4     | Minimum modules per course       |
| `MAX_MODULES`        | 5     | Maximum modules per course       |
| `QUIZ_QUESTIONS`     | 10    | Number of final quiz questions   |
| `AUDIO_WPM_DEFAULT`  | 150   | Words per minute for audio       |
| `GENERATION_TIMEOUT` | 600s  | Max generation time (10 minutes) |

---

## Troubleshooting

### "Module not found" error

**Cause:** Running the app from the wrong directory, or missing folders.
**Fix:** Make sure you `cd` into the `Kartavya-3.0` directory and that `services/`, `generators/`, and `utils/` folders exist.

### "Invalid JSON response" or quiz generation fails

**Cause:** AI response was too long and got cut off.
**Fix:** Already handled in the code (token limit increased). If it persists, reduce `QUIZ_QUESTIONS` in `config.py`.

### "GEMINI_API_KEY not set" warning

**Cause:** Missing or empty `.env` file.
**Fix:** Create a `.env` file in the project root with your API key (see [Step 3](#step-3--set-up-your-api-keys)).

### App doesn't open in browser

**Fix:** Manually navigate to `http://localhost:3000`.

### `pip install` fails on `pyaudioop`

**Cause:** `pyaudioop` is not compatible with Python 3.10+.
**Fix:** Already removed from `requirements.txt`. If you see this, update your `requirements.txt`.

### Generation takes too long or times out

**Fix:** Switch to a faster model: `GEMINI_MODEL=gemini-3-flash-preview` in your `.env` file.

### xAPI statements not showing in LMS Report

**Cause 1:** Course was generated with the old `xapiGenerator.js` (statements were never sent — now fixed).
**Cause 2:** LMS launch URL is missing `studentID`, `portalId`, etc.
**Fix:** Re-generate the course with the latest code. Verify the LMS launch URL includes all required parameters.

### Audio doesn't play in course

**Cause:** Browser autoplay policy blocks audio.
**Fix:** Click the audio play button manually. The course seekbar is intentionally locked to prevent skipping.

---

## Additional Docs

- [MAINTENANCE.md](MAINTENANCE.md) — Troubleshooting & manual fixes log
- [DEPLOYMENT.md](DEPLOYMENT.md) — Cloud deployment guide
- [CHANGELOG.md](CHANGELOG.md) — Version history
- [deploy/DEPLOY_JENKINS.md](deploy/DEPLOY_JENKINS.md) — Jenkins CI/CD setup guide
- [deploy/DEPLOY_FULLSTACK.md](deploy/DEPLOY_FULLSTACK.md) — Manual full-stack deploy guide

---

## License

MIT License
