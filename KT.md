📚 Kartavya-3.0: The Complete Knowledge Transfer (KT) & Action Guide
Welcome to the Kartavya-3.0 project! This document is your ultimate single source of truth. It contains absolutely everything you need to know to take ownership of this project, run it locally, understand its deepest mechanics, make modifications, and deploy it successfully.
It seamlessly combines our comprehensive Project README with deeper developer insights, troubleshooting logs, and a feature modification cheatsheet.

🏗️ 1. What Does This Project Do & Tech Stack?
Kartavya-3.0 is an AI-powered platform that generates complete, interactive e-learning courses — with text, images, audio narration, knowledge checks, quizzes, flashcards, and certificates — then packages everything into an xAPI/TinCan-compliant ZIP ready for upload to any LMS (Learning Management System).
You provide a course title, target audience, and some context — the system then:
Generates a course outline (4–5 modules by default) using Google Gemini AI
Writes detailed content for each module with real-world scenarios
Creates knowledge checks (quiz questions per module)
Generates images for each module using Gemini image generation
Produces audio narration (American/British/Indian accents, male/female voices)
Builds a final quiz (10 questions, 80% passing score, 3 attempts)
Auto-generates a certificate upon quiz pass
Packages everything into an xAPI ZIP file you can upload to your LMS

Our Current Tech Stack
Backend: Python 3.10+, FastAPI
Frontend: React 18, Next.js 14, TailwindCSS
AI Engine: Google Gemini Pro (google-generativeai)
Audio Engine: Google Cloud TTS (google-cloud-texttospeech)
Document Processing: ReportLab (PDFs), Python-Docx, PyPDF2, python-pptx
Deployment: Docker, Docker Compose (v2), Jenkins CI/CD

🚀 2. Setup & How to Run Locally
Prerequisites


Step 1: Clone and Setup Environment Variables
Clone the repo:
git clone <repository-url>
cd Kartavya-3.0
Create a .env file in the project root based on .env.example:
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional Defaults
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-3-pro-preview
⚠️ Security Rule 1: NEVER commit your .env file to Git. (It is already in .gitignore).

Step 2: Start the Backend (FastAPI)
Open a terminal in the root folder:
# 1. Create a virtual environment (do this once)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn backend.main:app --reload --port 8000
Backend is live at http://localhost:8000. API Swagger Docs at http://localhost:8000/docs.
Step 3: Start the Frontend (Next.js)
Open a new terminal in the frontend/ folder:
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
UI is live at http://localhost:3000.
Option B — Run Full Stack with Docker (Recommended)
Make sure you have a .env file with your GEMINI_API_KEY in the project root first, then:
docker compose -f docker-compose.prod.yml up -d --build
Open Frontend at http://localhost:3000 and API check at http://localhost:8000/api/health.

💻 3. Using the App — The 5-Step Wizard
The web UI walks users through a 5-step wizard to generate a course without coding:
Step 1 — Choose Generation Mode


Step 2 — Course Information
Course Title, Audience, Institute, Relevant Laws: Core inputs the AI builds upon.
Tone: Professional, Friendly, Academic, etc.
Reference Documents: You can upload .docx, .pdf, .pptx, .zip for the AI to extract context from.
Step 3 — Content Options
Modules: Choose 1–10 (Default: 4).
Course Level: Beginner, Intermediate, or Advanced.
Flashcards: Enable flip cards for key concepts.
Final Quiz: Select number of quiz questions (if enabled).
Step 4 — Audio & Media
Choose to include audio, select Accent (American/British/Indian), Voice Gender, and Speech Speed (0.5x to 2.0x).
Step 5 — Review & Confirm
Review selections and click generate. It takes 2–10 minutes. A live progress bar will track the status.

⚙️ 4. Generation Pipeline (What Happens Behind the Scenes)
When you hit generate, services/course_generator.py executes this sequence:
Course Outline (gemini_service.py) → Gemini generates a structured JSON array of module titles.
Module Content (gemini_service.py) → Detailed text written per module.
Knowledge Checks → 1 inline quiz question generated per module section.
Flashcards (flashcard_generator.py) → (Optional) Front/Back flip cards.
Image Generation → Gemini creates module cover images.
Audio Generation (google_tts_service.py) → Google TTS chunks long texts (<4000 bytes) and converts them to sequential MP3 audio files.
Final Quiz → 10 questions, 80% passing score, 3 attempts.
QA Validation (qa_validator.py) → Validates JSON structure, detects AI hallucinations against source files.
Packaging (xapi_generator.py & pdf_generator.py) → ZIP and offline PDF created.

📦 5. Output — What You Get & Course Features
After generation, click Download to get a .zip file:
YourCourse.zip/
├── index.html              ← Complete interactive course (open in any browser)
├── tincan.xml              ← xAPI/TinCan manifest for LMS compliance
├── course.json             ← Course data and metadata
└── assets/
    ├── styles.css          ← Responsive Course styling
    ├── script.js           ← Interactivity & xAPI tracking logic
    ├── xapiwrapper.min.js  ← ADL xAPI Wrapper library (v1.11.0)
    ├── module-1.png        ← Generated images
    ├── audio-m1-s1.mp3     ← Generated chunked audio
    └── ...
Output File Features:
✅ Responsive design (desktop, tablet, mobile) with Module-by-module navigation sidebar.
✅ Course Instructions page with audio narration.
✅ Audio narration per section (seekbar purposely locked — no skipping forward).
✅ Knowledge checks per module (must answer correctly to proceed).
✅ Interactive flashcards per section (if enabled).
✅ Final quiz with 80% passing score and 3 retry attempts.
✅ Certificate of completion on quiz pass.
✅ xAPI statement tracking + portalId injects + LMS State API persistence.

📁 6. Project Directory & Deep File-by-File Reference
Here is a map of the entire operation. Look here if you need to modify behavior.
`backend/` & Root Files


`frontend/` (Next.js Application)



📡 7. xAPI Tracking & LMS Integration (Deep Dive)
The produced ZIP file is a SCORM/xAPI package. When a user opens it in an LMS (like emPower LMS or SCORM Cloud), tracking works via standard ADL Wrapper + custom injection.
The Launch
The LMS opens index.html with URL parameters:
?endpoint=https://lrs...&auth=Basic+xxx&actor={...}&registration=uuid
The JavaScript Engine (`script.js` in `xapi_generator.py`)
Parses URL Parameters: Extracts endpoint, auth, actor and standard metadata. It also looks for custom emPower LMS fields (portalId, studentID, subscriptionId, identifier).
Actor Normalization: SCORM Cloud injects completely broken, non-standard Actor JSON logic (passing arrays instead of strings, accountName instead of name). The JS intercepts and normalizes this auto-magically so it doesn't crash.
State API Validation: It attempts to restore prior progress from the LRS State API. It saves current module and completed module states.
What xAPI Statements Are Sent?
The wrapper tracks:
experienced: Course started, Module viewed.
viewed: Image loaded.
listened / paused: Audio track interactions.
answered: Knowledge check interactions.
passed / failed: Final quiz submitted.
completed: Master course completion.

Every single statement sent will naturally wrap the custom emPower LMS fields (portalId, studentID, subscriptionId, identifier) inside the payload so they correctly show up inside the emPower UI Reports.
Bug Fix History Note: Previously, statements weren't appearing in the LMS because the ADL.XAPIWrapper.sendStatement() line was flat-out commented out in an old legacy file (xapiGenerator.js). This is fully fixed in the new generators/xapi_generator.py pipeline. Every statement is now wrapped in a try/catch.

🛠️ 8. Developer Cheatsheet (Component Feature Modifying)
❓ "How do I add a new input field to the Wizard?"
Frontend UI: Open frontend/app/page.tsx. Add your <input> to Step 2. Add the value to the courseConfig state object.
Backend API Model: Open backend/main.py. Find class GenerateCourseRequest(BaseModel) and add your field (e.g., company_values: Optional[str] = None).
Backend Logic Prompt: In services/course_generator.py, find the course_setup_prompt block and inject your new variable so the AI knows about it: "Make sure to incorporate these company values: {company_values}".
❓ "I want to add a new Language (like Spanish) for TTS"
Frontend UI: Add the language to the dropdown options in frontend/app/page.tsx or frontend/app/lib/languages.ts.
Backend TTS: In services/google_tts_service.py, add your language code mapping (e.g., 'Spanish': 'es-ES') to the Google Cloud Voice dictionaries.
PDF Generator: Open generators/pdf_generator.py. Find _setup_custom_styles(). Add an elif language == "Spanish": fontName = "DejaVuSans" condition to properly handle Latin character rendering instead of fallback fonts.
❓ "My generated course keeps opening at the Final Quiz!" (Testing State API)
What's happening: The generated course (index.html) saves learner progress in the browser localStorage so they can resume later. It's working too well while you are testing.
The Fix: You must clear your browser's local cache. Open browser DevTools (F12) → Application → Local Storage → Right click and clear kartavya_progress_... keys.
❓ "I want to change the Logo inside the ZIP file or Web App"
The Web UI Logo: This lives in frontend/public/ (Next.js).
The Course ZIP Logo: The course is completely separate from the web UI once generated. To change the logo inside the exported xAPI course, edit generators/xapi_generator.py (_create_assets() method) and inject your Base64 encoded logo inside the generated code output.

🚢 9. Production Deployment (Jenkins + Docker)
Code pushed to the master branch automatically triggers Jenkins CI/CD.
The Pipeline Flow
Code pushed to master triggers Jenkins.
Jenkins reads the Jenkinsfile in the repository root.
Crucial Setup: Jenkins grabs the .env file credentials from its securely vaulted system (kartavya-env-secrets) and dynamically places it in the execution root.
Jenkins runs: docker compose -f docker-compose.prod.yml build --no-cache
Backend Container (Dockerfile.backend): Uses Python 3.10. Re-runs requirements.txt. Grabs apt-get install Linux fonts (fonts-lohit-devanagari, fonts-dejavu-core) for robust language PDF support.
Frontend Container (Dockerfile.frontend): Uses Node 20. Runs npm run build enabling standalone output mode for highly condensed performance. Note: It must copy the frontend/public/ directory over to /app/public.
Fast startup: docker compose -f docker-compose.prod.yml up -d
Jenkins intentionally deletes .env from disk so memory cannot be queried.
Infrastructure Configuration Reference
All hard limits can be configured dynamically without redeploys via ENV:
DEBUG=False
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-3-pro-preview

🚨 10. Comprehensive Troubleshooting & Error Guide
🛑 1. "Failed to reach backend at ... Is it running?"
Cause: Frontend proxy cannot reach FastAPI.
Solution (Docker/Prod): Check NEXT_API_BASE_URL inside docker-compose.prod.yml. Or see if backend crashed: docker compose logs backend.
Solution (Local): Ensure uvicorn backend.main:app --port 8000 is absolutely running simultaneously in another terminal.
🛑 2. "Tofu Boxes" (Missing text `[][][]`) in generated PDFs
What it means: The PDF library (ReportLab) does not have a font that supports the characters in the course (e.g., Hindi or Japanese text).
Solution: For Docker deployments, ensure fonts-dejavu-core, fonts-droid-fallback, and fonts-lohit-devanagari are active in apt-get install inside Dockerfile.backend.
🛑 3. "GEMINI API Request Failed / Quota Exceeded"
Cause: GEMINI_API_KEY is missing in .env, or you've made too many requests too fast.
Solution: Validated .env. Review services/gemini_service.py limit handling; it has model downgrades gemini-3-pro-preview -> gemini-3-flash-preview built in, wait roughly 60 seconds if Quota limits lock it.
🛑 4. "COPY --from=builder /app/public ./public" fails during Docker build
What it means: The frontend/public/ directory does not exist or wasn't pulled from Git.
Solution: Git ignores empty folders. Run these commands locally:
mkdir -p frontend/public && touch frontend/public/.gitkeep
git add frontend/public/.gitkeep
🛑 5. "Invalid JSON response" from AI during Quiz Generation
What it means: Gemini returned a malformed response (missing brackets) or markdown formatting that couldn't be parsed.
Solution: gemini_service.py intercepts this and attempts to strip markdown (```json tags). If it fails heavily on token limits, check logs/error.log for the exact string to debug the model's behavior.
🛑 6. Audio does not play automatically in the course
Cause: Modern browsers (Chrome, Safari) globally block Auto-Play media to protect users unless the user clicks something.
Solution: This is an expected Chrome browser behavior. Users must simply hit 'Play' or start the course normally. The script.js enforces that they cannot manually scrub the audio timeline forward.
🔒 11. Core Security Golden Rules for Juniors
NEVER hardcode GEMINI_API_KEY, passwords, or tokens into ANY .py or .tsx file.
NEVER type git add .env. If you accidentally do, type git rm --cached .env.
ALWAYS use config.py to securely read backend variables safely using os.getenv().

End of KT Guide.

## 📢 12. Recent Architecture & UI Updates (Feb-Mar 2026)

This section documents the major architectural refactors, UI overhauls, and bug fixes applied to Kartavya 3.0 during February and March 2026. These updates significantly improved the platform's visual polish, performance, and reliability.

### 🎨 Frontend UI & UX Overhaul
*   **Claymorphism Design System:** Migrated the entire user interface from a flat design to a premium "Claymorphism" aesthetic. This introduced frosted glass cards, soft shadows, rounded edges, and tactile hover states.
*   **Aurora WebGL Background:** Replaced the static background with a dynamic, fluid WebGL Aurora mesh canvas using the `ogl` rendering engine via React Bits, giving the app a next-generation feel.
*   **Streamlined Wizard:** The course generation wizard was consolidated from 5 steps down to 4 logically grouped steps.
*   **Interactive Timelines & Steppers:** Added a sleek horizontal animated timeline to visualize the active AI generation phase (Queued → Outline → Modules → Quiz → Finalizing) and spring-bounce animations to form interactions.
*   **Outline-Only Mode:** Added the ability to completely bypass full course generation and exclusively output the Course Outline. This includes full inline-editing capabilities on the View page, allowing users to modify the AI's structure before committing.

### 🛠️ Backend & API Reliability Fixes
*   **CORS Preflight Routing:** Resolved severe "Failed to save quiz" errors by routing all frontend cross-origin API calls through the Next.js API proxy (`apiFetch`) instead of requesting the backend port directly.
*   **Polling Loop Fix:** Addressed a critical bug in `CourseContext.tsx` where background jobs triggered an infinite polling loop of GET requests even after the job completed, preserving server bandwidth.

### 🐳 Deployment & Docker Optimization
*   **Image Size Reduction:** Drastically reduced the Docker image footprint (saving ~3.5GB) by swapping the default PyTorch library to the CPU-only version in the backend `requirements.txt`.
*   **Dependency Cleanup:** Conducted a deep codebase audit to safely remove completely unused, bloated libraries (`openai-whisper`, `moviepy`, `pydub`, `motion`) that were slowing down Jenkins builds.
*   **Build Caching:** Ensured Jenkins CI/CD explicitly utilizes `--no-cache-dir` safely for the backend to prevent stale dependency locking.

### �� xAPI Tracking Restoration
*   **Statement Transmission:** Fixed a legacy flaw in the generated `script.js` where the ADL wrapper's `sendStatement()` call was commented out. All course interactions (quiz passes, module views, audio listens) are now successfully and transparently transmitted to the connected LMS.
