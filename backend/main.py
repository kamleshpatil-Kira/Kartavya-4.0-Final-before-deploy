import asyncio
import io
import json
import mimetypes
import os
import re
import shutil
import sys
import time
import uuid
import zipfile
from collections import OrderedDict
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse

# Allow importing existing project modules
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config import OUTPUT_DIR, UPLOADS_DIR  # noqa: E402
from services.course_generator import CourseGenerator  # noqa: E402
from services.gemini_service import GeminiService
from services.flashcard_generator import FlashcardGenerator  # noqa: E402
from services.google_tts_service import GoogleTTSService  # noqa: E402
from utils.course_loader import CourseLoader  # noqa: E402
from utils.document_processor import DocumentProcessor  # noqa: E402
from utils.image_stats import record_images
from utils.logger import logger  # noqa: E402
from generators.xapi_generator import xAPIGenerator_instance  # noqa: E402
from generators.pdf_generator import pdf_generator_instance  # noqa: E402
from routes.history import make_router as make_history_router, make_stats_router  # noqa: E402
from services.image_generator import ImageGeneratorService
from config import GEMINI_API_KEY

image_gen_instance = ImageGeneratorService(api_key=GEMINI_API_KEY)

app = FastAPI(title="Kartavya-3.0 API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular route files
app.include_router(make_history_router(UPLOADS_DIR))
app.include_router(make_stats_router(UPLOADS_DIR))


@dataclass
class JobState:
    id: str
    status: str
    progress: int
    message: str
    error: Optional[str] = None
    course_id: Optional[str] = None
    course_data: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)  # for job TTL pruning (Fix F2)


_jobs: Dict[str, JobState] = {}
_jobs_lock = asyncio.Lock()
_job_tasks: Dict[str, asyncio.Task] = {}

# LRU course cache — capped at 50 entries to prevent unbounded memory growth (Fix F1)
_MAX_CACHE = 50
_course_cache: OrderedDict = OrderedDict()

_image_sessions: Dict[str, Dict[str, Path]] = {}

# Job retention: keep at most 200 jobs, prune terminal jobs older than 24 h (Fix F2)
_MAX_JOBS = 200
_JOB_TTL_SECONDS = 86_400  # 24 hours


def _prune_jobs() -> None:
    """Remove terminal jobs older than _JOB_TTL_SECONDS; hard-cap at _MAX_JOBS."""
    cutoff = time.time() - _JOB_TTL_SECONDS
    terminal = {"completed", "failed", "cancelled"}
    to_delete = [
        jid for jid, j in _jobs.items()
        if j.status in terminal and j.created_at < cutoff
    ]
    for jid in to_delete:
        _jobs.pop(jid, None)
    # Hard cap: if still too many, drop oldest terminal jobs first
    if len(_jobs) > _MAX_JOBS:
        terminal_ids = [jid for jid, j in _jobs.items() if j.status in terminal]
        for jid in terminal_ids[:len(_jobs) - _MAX_JOBS]:
            _jobs.pop(jid, None)


# -------------------------
# Helpers
# -------------------------

def sanitize_filename(filename: str) -> str:
    import unicodedata
    # Normalise Unicode → ASCII (handles Hindi, Arabic, Chinese, etc.)
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = re.sub(r'[\s\u00a0]+', '-', sanitized)  # also handles non-breaking spaces
    sanitized = re.sub(r'-+', '-', sanitized)
    sanitized = sanitized.strip('-')
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('-')
    return sanitized if sanitized else "course"


_PROVIDER_REDACTIONS = (
    (re.compile(r"google ai studio", re.IGNORECASE), "provider dashboard"),
    (re.compile(r"google cloud text[- ]to[- ]speech", re.IGNORECASE), "speech service"),
    (re.compile(r"google cloud", re.IGNORECASE), "cloud service"),
    (re.compile(r"google tts", re.IGNORECASE), "speech service"),
    (re.compile(r"gtts", re.IGNORECASE), "speech fallback service"),
    (re.compile(r"gemini", re.IGNORECASE), "AI service"),
    (re.compile(r"google", re.IGNORECASE), "provider"),
)


def _sanitize_provider_details(text: Optional[str]) -> Optional[str]:
    """Redact backend provider names from user-facing status/error messages."""
    if text is None:
        return None
    sanitized = str(text)
    for pattern, replacement in _PROVIDER_REDACTIONS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def _public_extractor_name(name: str) -> str:
    """Map internal extractor IDs to user-safe labels."""
    normalized = str(name or "").strip().lower()
    if normalized == "gemini-vision":
        return "vision-ocr"
    return normalized


from routes.history import save_course_to_history as _save_course_to_history

def save_course_to_history(course_data: Dict[str, Any]) -> None:
    _save_course_to_history(UPLOADS_DIR, course_data)



def _randomize_kc_options(course_data: Dict[str, Any]) -> None:
    import random
    for module in course_data.get("modules", []):
        kc = module.get("knowledgeCheck")
        if not kc or not isinstance(kc, dict):
            continue
        
        options = kc.get("options")
        correct_key = str(kc.get("correctAnswer", "")).upper()
        if not isinstance(options, dict) or not correct_key:
            continue
            
        # Standardize keys to uppercase for matching
        upper_options = {str(k).upper(): v for k, v in options.items()}
        if correct_key not in upper_options:
            continue
            
        correct_val = upper_options[correct_key]
        values = list(upper_options.values())
        random.shuffle(values)
        
        new_options = {}
        new_correct = correct_key
        letters = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, val in enumerate(values):
            k = letters[i] if i < len(letters) else str(i)
            new_options[k] = val
            if val == correct_val:
                new_correct = k
                
        kc["options"] = new_options
        kc["correctAnswer"] = new_correct

    # Also randomize final quiz questions
    quiz = course_data.get("quiz", {})
    for question in quiz.get("questions", []):
        if not isinstance(question, dict):
            continue
        options = question.get("options")
        correct_key = str(question.get("correctAnswer", "")).upper()
        if not isinstance(options, dict) or not correct_key:
            continue

        upper_options = {str(k).upper(): v for k, v in options.items()}
        if correct_key not in upper_options:
            continue

        correct_val = upper_options[correct_key]
        values = list(upper_options.values())
        random.shuffle(values)

        new_options = {}
        new_correct = correct_key
        letters = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, val in enumerate(values):
            k = letters[i] if i < len(letters) else str(i)
            new_options[k] = val
            if val == correct_val:
                new_correct = k

        question["options"] = new_options
        question["correctAnswer"] = new_correct

def save_course_json(course_data: Dict[str, Any]) -> str:
    _randomize_kc_options(course_data)
    course_id = course_data.get("course", {}).get("id")
    if not course_id:
        course_id = f"course-{int(time.time())}"
        course_data.setdefault("course", {})
        course_data["course"]["id"] = course_id

    output_path = OUTPUT_DIR / course_id
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "course.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(course_data, f, indent=2, ensure_ascii=False)

    # LRU: move to end, evict oldest if over cap (Fix F1)
    _course_cache[course_id] = course_data
    _course_cache.move_to_end(course_id)
    if len(_course_cache) > _MAX_CACHE:
        _course_cache.popitem(last=False)
    return course_id


def load_course_json(course_id: str) -> Dict[str, Any]:
    if course_id in _course_cache:
        _course_cache.move_to_end(course_id)  # refresh LRU position
        return _course_cache[course_id]

    json_path = OUTPUT_DIR / course_id / "course.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Course not found")

    with open(json_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    def _clean_nbsp(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _clean_nbsp(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_clean_nbsp(item) for item in obj]
        elif isinstance(obj, str):
            return obj.replace('\xa0', ' ').replace('\u00A0', ' ')
        return obj

    course_data = _clean_nbsp(course_data)
    _randomize_kc_options(course_data)

    _course_cache[course_id] = course_data
    _course_cache.move_to_end(course_id)
    if len(_course_cache) > _MAX_CACHE:
        _course_cache.popitem(last=False)
    return course_data


def module_content_to_text(module: Dict[str, Any]) -> str:
    module_title = module.get("moduleTitle", "")
    module_text = module_title

    content = module.get("content")
    if isinstance(content, dict):
        if "sections" in content:
            for section in content.get("sections", []):
                module_text += " " + str(section.get("sectionTitle", ""))
                module_text += " " + str(section.get("content", ""))[:200]
        elif "summary" in content:
            module_text += " " + str(content.get("summary", ""))
    elif isinstance(content, str):
        module_text += " " + content[:200]

    return module_text


def build_module_image_context(module: Dict[str, Any]) -> str:
    title = str(module.get("moduleTitle", "Module")).strip()
    objectives = module.get("learningObjectives", []) or []
    content = module.get("content")

    section_titles: List[str] = []
    section_snippets: List[str] = []

    def _clean_snippet(text: str, limit: int = 240) -> str:
        return re.sub(r"\s+", " ", text).strip()[:limit]

    if isinstance(content, dict):
        sections = content.get("sections", [])
        for section in sections:
            sec_title = str(section.get("sectionTitle", "")).strip()
            if sec_title:
                section_titles.append(sec_title)
            sec_content = str(section.get("content", "")).strip()
            if sec_content:
                section_snippets.append(_clean_snippet(sec_content))
        if not section_snippets:
            summary = str(content.get("summary", "")).strip()
            if summary:
                section_snippets.append(_clean_snippet(summary))
    elif isinstance(content, str) and content.strip():
        section_snippets.append(_clean_snippet(content))

    parts: List[str] = [f"Module title: {title}."]
    if objectives:
        parts.append(f"Learning objectives: {'; '.join([str(o).strip() for o in objectives[:5] if str(o).strip()])}.")
    if section_titles:
        parts.append(f"Key sections: {'; '.join(section_titles[:5])}.")
    if section_snippets:
        parts.append(f"Key content: {' '.join(section_snippets[:2])}.")

    return " ".join([p for p in parts if p and p.strip()])


def extract_keywords(text: str) -> set:
    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = text.split()
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "should",
        "could",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "from",
        "into",
        "through",
        "during",
        "including",
        "until",
        "against",
        "among",
        "throughout",
        "despite",
        "towards",
        "upon",
        "about",
        "over",
        "under",
        "above",
        "below",
        "up",
        "down",
        "out",
        "off",
        "away",
        "back",
        "more",
        "most",
        "other",
        "some",
        "such",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "just",
        "don",
        "now",
    }
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]

    phrases = []
    for i in range(len(words) - 1):
        if len(words[i]) > 2 and len(words[i + 1]) > 2:
            phrase = f"{words[i]} {words[i + 1]}"
            if not any(sw in phrase for sw in stop_words):
                phrases.append(phrase)

    return set(keywords + phrases)


def calculate_match_score(module_text: str, image_filename: str, module_number: int = 0) -> int:
    module_keywords = extract_keywords(module_text)
    image_keywords = extract_keywords(image_filename)

    overlap = len(module_keywords & image_keywords)

    # Number matching: use the actual module number (not digits scraped from the title)
    # This correctly handles "module_1.png", "image_01.jpg", "slide_1.png" etc.
    module_num_match = 0
    if module_number > 0:
        image_nums = re.findall(r"\b0*(\d+)\b", image_filename)  # 0* strips leading zeros
        if str(module_number) in image_nums:
            module_num_match = 5

    substring_score = 0
    image_filename_lower = image_filename.lower()
    for keyword in module_keywords:
        if len(keyword) > 3:
            if keyword in image_filename_lower:
                substring_score += 3
            elif any(kw in image_filename_lower for kw in image_keywords if keyword in kw or kw in keyword):
                substring_score += 1

    module_text_lower = module_text.lower()
    for img_keyword in image_keywords:
        if len(img_keyword) > 3 and img_keyword in module_text_lower:
            substring_score += 2

    total_score = (overlap * 4) + module_num_match + substring_score
    return total_score


def auto_match_images_to_modules(modules: List[Dict[str, Any]], image_names: List[str]) -> Dict[str, Any]:
    matches: Dict[str, Any] = {}
    used_images: set = set()

    module_contents: Dict[int, str] = {}
    for idx, module in enumerate(modules, 1):
        module_num = module.get("moduleNumber", idx)
        module_contents[module_num] = module_content_to_text(module)

    # Pass 1: semantic + number matching
    for module_num, module_text in module_contents.items():
        best_match = None
        best_score = 0

        for img_name in image_names:
            if img_name in used_images:
                continue
            score = calculate_match_score(module_text, img_name, module_number=module_num)
            if score > best_score:
                best_score = score
                best_match = img_name

        if best_match and best_score >= 2:
            matches[str(module_num)] = {
                "image_name": best_match,
                "score": best_score,
                "confidence": "high" if best_score >= 5 else "medium" if best_score >= 3 else "low",
            }
            used_images.add(best_match)
        else:
            matches[str(module_num)] = {"image_name": None, "score": 0, "confidence": "none"}

    # Pass 2: sequential fallback — assign leftover images to unmatched modules in order
    # This handles the case where all images are generically named (no semantic words, no numbers)
    unmatched_modules = [mn for mn, m in matches.items() if m["image_name"] is None]
    leftover_images = [img for img in image_names if img not in used_images]

    for module_key, img_name in zip(unmatched_modules, leftover_images):
        matches[module_key] = {
            "image_name": img_name,
            "score": 1,
            "confidence": "low",  # sequential fallback, not a real semantic match
        }

    return matches



# -------------------------
# Jobs
# -------------------------

async def _run_generation(job_id: str, user_input: Dict[str, Any]) -> None:
    async with _jobs_lock:
        job = _jobs[job_id]
        job.status = "running"
        job.progress = 0
        job.message = "Starting generation"

    async def progress_callback(progress: int, message: str) -> None:
        sanitized = _sanitize_provider_details(message) or message
        async with _jobs_lock:
            job = _jobs[job_id]
            job.progress = int(progress)
            job.message = sanitized
            
        # Log to a backend file for easy viewing of only steps
        log_path = ROOT_DIR / "backend" / "steps.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{job_id[:8]}] {progress}%: {sanitized}\n")

    try:
        generator = CourseGenerator()
        is_regen = bool(user_input.get("existingCourseData"))
        course_data = await generator.generate_course(
            user_input, 
            progress_callback, 
            is_regen=is_regen, 
            stats_uploads_dir=UPLOADS_DIR
        )

        course_id = save_course_json(course_data)
        save_course_to_history(course_data)

        async with _jobs_lock:
            job = _jobs[job_id]
            job.status = "completed"
            job.progress = 100
            job.message = "Completed"
            job.course_id = course_id
            job.course_data = course_data
    except asyncio.CancelledError:
        async with _jobs_lock:
            job = _jobs[job_id]
            job.status = "cancelled"
            job.message = "Cancelled"
            job.error = None
        raise
    except Exception as exc:
        logger.error(f"Generation failed: {exc}", exc_info=True)
        async with _jobs_lock:
            job = _jobs[job_id]
            job.status = "failed"
            job.error = _sanitize_provider_details(str(exc))
            job.message = "Failed"
    finally:
        async with _jobs_lock:
            _job_tasks.pop(job_id, None)


# -------------------------
# API Endpoints
# -------------------------

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/api/guidelines/suggest")
async def suggest_guidelines(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Auto-fetch relevant compliance guidelines for any course title.
    Uses Gemini to return real, citable laws/standards as suggestion chips.
    """
    course_title = (body.get("courseTitle") or "").strip()
    if not course_title or len(course_title) < 3:
        return {"domain": "", "suggestions": []}
    try:
        gemini = GeminiService()
        return gemini.suggest_guidelines_for_title(course_title)
    except Exception as exc:
        logger.warning(f"Guidelines suggestion failed: {exc}")
        return {"domain": "", "suggestions": []}


@app.post("/api/course/generate")
async def generate_course(user_input: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    # Normalize selected course language/audio options so generation and TTS stay aligned.
    course_language = str(user_input.get("courseLanguage") or "English")
    user_input["courseLanguage"] = course_language
    audio_options = user_input.get("audioOptions")
    if not isinstance(audio_options, dict):
        audio_options = {}
    tts = GoogleTTSService()
    normalized_accent = tts.normalize_language_key(audio_options.get("accent") or course_language)
    audio_options["accent"] = normalized_accent
    audio_options["gender"] = str(audio_options.get("gender") or "male").lower()
    audio_options["speed"] = float(audio_options.get("speed") or 1.0)
    user_input["audioOptions"] = audio_options

    job_id = uuid.uuid4().hex
    async with _jobs_lock:
        _prune_jobs()  # housekeep before adding new job (Fix F2)
        _jobs[job_id] = JobState(
            id=job_id,
            status="queued",
            progress=0,
            message="Queued",
        )

    task = asyncio.create_task(_run_generation(job_id, user_input))
    async with _jobs_lock:
        _job_tasks[job_id] = task
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    async with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        data = asdict(job)

    data["message"] = _sanitize_provider_details(data.get("message"))
    data["error"] = _sanitize_provider_details(data.get("error"))
    return data


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> Dict[str, Any]:
    async with _jobs_lock:
        job = _jobs.get(job_id)
        task = _job_tasks.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status in ("completed", "failed", "cancelled"):
            return {"status": job.status}

        job.status = "cancelled"
        job.message = "Cancelled"
        job.error = None

    if task and not task.done():
        task.cancel()

    return {"status": "cancelled"}


@app.post("/api/course/save")
async def save_course(course_data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    course_id = save_course_json(course_data)
    save_course_to_history(course_data)
    return {"course_id": course_id}


@app.get("/api/course/{course_id}")
async def get_course(course_id: str) -> Dict[str, Any]:
    course_data = load_course_json(course_id)
    return course_data


@app.post("/api/course/load")
async def load_course(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Loads a course package for the Image Mapping page.
    Accepted: .zip (xAPI, xAPI Rise 360, SCORM 1.2)
    Returns a course_data dict with at least: course.title + modules[].moduleTitle
    """
    course_loader = CourseLoader()
    suffix = Path(file.filename).suffix.lower()

    if suffix != ".zip":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{suffix}'. "
                "The Image Mapping page only accepts xAPI, xAPI Rise 360, or SCORM 1.2 ZIP packages (.zip)."
            )
        )

    temp_path = UPLOADS_DIR / Path(file.filename).name  # Bug #16 fix: use basename only — prevents path traversal
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        extraction = course_loader.load_course(temp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_sanitize_provider_details(str(e)))

    if not extraction:
        raise HTTPException(status_code=400, detail="Could not load course data from the ZIP file.")

    # --- Primary path: Kartavya-format ZIP (contains course.json with modules array) ---
    course_data = extraction.get("raw_course_data")

    if course_data and isinstance(course_data, dict):
        # Full Kartavya export — use as-is
        course_id = save_course_json(course_data)
        save_course_to_history(course_data)
        return {"course_data": course_data, "course_id": course_id}

    # --- Fallback path: xAPI / Rise360 / SCORM 1.2 ZIP ---
    # These don't contain a Kartavya course.json. We synthesise a minimal course_data
    # from the extracted text so the image mapping UI can display module slots.
    course_title = extraction.get("course_title") or Path(file.filename).stem.replace("-", " ").replace("_", " ").title()
    detected_modules: list = extraction.get("detected_modules") or []
    file_type = extraction.get("file_type", "xapi")

    if not detected_modules:
        # CourseLoader couldn't detect module headings — still allow the UI to load with a
        # single placeholder so the user can manually assign images.
        logger.warning(
            f"No module headings detected in {file.filename} ({file_type}). "
            "Falling back to a single-module placeholder for image mapping."
        )
        detected_modules = [course_title]

    # Build minimal course_data structure compatible with the image mapping UI
    synthetic_modules = [
        {
            "moduleNumber": i + 1,
            "moduleTitle": title,
            "content": {},
        }
        for i, title in enumerate(detected_modules)
    ]
    course_data = {
        "course": {
            "title": course_title,
            "description": f"Imported from {file_type.upper()} package: {file.filename}",
            "overview": "",
            "learningObjectives": [],
        },
        "modules": synthetic_modules,
        "outline": {},
        "metadata": {
            "source_file": file.filename,
            "source_type": file_type,
            "imported_for": "image_mapping",
        },
    }

    logger.info(
        f"Synthesised course_data for image mapping: '{course_title}' "
        f"({len(synthetic_modules)} module(s)) from {file_type} ZIP"
    )

    course_id = save_course_json(course_data)
    save_course_to_history(course_data)
    return {"course_data": course_data, "course_id": course_id}


@app.post("/api/documents/process")
async def process_documents(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    processor = DocumentProcessor()
    try:
        gemini = GeminiService()
    except Exception as e:
        logger.warning(f"Could not initialize GeminiService for document analysis: {e}")
        gemini = None

    all_content: List[str] = []
    file_summaries: List[Dict[str, Any]] = []
    temp_paths: List[Path] = []

    for file in files:
        temp_path = UPLOADS_DIR / Path(file.filename).name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
        temp_paths.append(temp_path)

        try:
            result = processor.process_document(temp_path)
            content_text = result.get("content", "")
            file_meta = result.get("metadata", {})
            extractor_name = _public_extractor_name(file_meta.get("extractor", ""))
            all_content.append(content_text)
            file_summaries.append({
                "filename": file.filename,
                "type": file_meta.get("type", "unknown"),
                "extractor": extractor_name,
                "pages": file_meta.get("pages") or file_meta.get("slides"),
                "word_count": file_meta.get("word_count", len(content_text.split())),
            })
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            file_summaries.append({"filename": file.filename, "error": _sanitize_provider_details(str(e))})

    processed_content = "\n\n---\n\n".join(all_content)
    total_words = sum(s.get("word_count", 0) for s in file_summaries)

    # Determine how the content was extracted (for UX feedback)
    extractors_used = list({s.get("extractor", "") for s in file_summaries if s.get("extractor")})
    is_vision_ocr = "vision-ocr" in extractors_used

    # Extract metadata using Gemini if available
    metadata: Dict[str, Any] = {}
    if gemini and processed_content.strip():
        try:
            metadata = await asyncio.to_thread(gemini.analyze_document_metadata, processed_content)
        except Exception as e:
            logger.error(f"Failed to extract document metadata: {e}")

    return {
        "processedDocuments": processed_content,
        "metadata": metadata,
        "detectedLanguage": metadata.get("detectedLanguage", ""),
        "wordCount": total_words,
        "files": file_summaries,
        "extractionMethod": extractors_used[0] if len(extractors_used) == 1 else ", ".join(extractors_used),
        "isVisionOCR": is_vision_ocr,
    }


@app.post("/api/course/upload-existing")
async def upload_existing_course(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Dedicated endpoint for Regenerate Existing Course upload.
    Accepts: PDF, DOCX, DOC, ZIP (xAPI / SCORM 1.2), JSON.
    Returns: full extraction summary + Gemini course blueprint for UI preview.
    """
    from utils.course_loader import CourseLoader

    allowed_extensions = {".pdf", ".docx", ".doc", ".zip", ".json"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Accepted: PDF, DOCX, DOC, ZIP (xAPI/SCORM), JSON"
        )

    temp_path = UPLOADS_DIR / Path(file.filename).name  # Bug #15 fix: use basename only — prevents path traversal
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        loader = CourseLoader()
        extraction = loader.load_course(temp_path)

        # Run Gemini deep analysis to produce the blueprint
        gemini = GeminiService()
        blueprint = await asyncio.to_thread(
            gemini.analyze_existing_course,
            extraction.get("extracted_content", ""),
            extraction.get("file_type", "unknown")
        )

        # If the upload contains structured course data (Kartavya xAPI/JSON export),
        # use the actual module count from there — ground truth, not Gemini's guess
        raw_course_data = extraction.get("raw_course_data")
        exact_module_count = None
        if raw_course_data and isinstance(raw_course_data, dict):
            raw_modules = raw_course_data.get("modules", [])
            if raw_modules:
                exact_module_count = len(raw_modules)
                logger.info(f"Exact module count from structured course data: {exact_module_count}")

        # Determine final module count: prefer exact (from structured data) over Gemini's estimate
        blueprint_module_count = blueprint.get("estimatedModuleCount") or len(blueprint.get("detectedModules", []))
        final_module_count = exact_module_count if exact_module_count is not None else blueprint_module_count

        # If we have raw structured data, enrich blueprint's detectedModules with actual titles
        if raw_course_data and exact_module_count:
            raw_modules = raw_course_data.get("modules", [])
            detected_modules_from_data = []
            for m in raw_modules:
                detected_modules_from_data.append({
                    "moduleTitle": m.get("moduleTitle") or m.get("title", ""),
                    "keyTopics": [],
                    "learningObjectives": []
                })
            blueprint["detectedModules"] = detected_modules_from_data
            blueprint["estimatedModuleCount"] = exact_module_count

        return {
            "status": "success",
            "fileName": file.filename,
            "fileType": extraction.get("file_type", "unknown"),
            "detectedTitle": blueprint.get("courseTitle") or extraction.get("course_title", ""),
            "detectedAudience": blueprint.get("detectedAudience", ""),
            "detectedTone": blueprint.get("detectedTone", ""),
            "complianceRefs": blueprint.get("complianceRefs", []),
            "detectedModules": blueprint.get("detectedModules", []),
            "suggestedImprovements": blueprint.get("suggestedImprovements", ""),
            "estimatedModuleCount": final_module_count,
            "wordCount": extraction.get("word_count", 0),
            "blueprint": blueprint,
            "extractionSummary": extraction,
        }
    except Exception as e:
        logger.error(f"Failed to process uploaded existing course: {e}", exc_info=True)
        safe_error = _sanitize_provider_details(str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process course file: {safe_error}")



@app.post("/api/audio/preview")
async def preview_audio(payload: Dict[str, Any] = Body(...)) -> StreamingResponse:
    tts = GoogleTTSService()
    selected_language = payload.get("language") or payload.get("accent") or "English"
    language_key = str(selected_language).strip().lower()
    preview_defaults = {
        "english": "Hello, this is a preview of the selected voice settings for your course.",
        "hindi": "नमस्ते, यह आपके कोर्स के लिए चयनित वॉइस सेटिंग्स का पूर्वावलोकन है।",
        "spanish": "Hola, esta es una vista previa de la configuracion de voz seleccionada para tu curso.",
        "french": "Bonjour, ceci est un apercu des parametres vocaux selectionnes pour votre cours.",
        "german": "Hallo, dies ist eine Vorschau der ausgewahlten Spracheinstellungen fur Ihren Kurs.",
        "portuguese": "Ola, esta e uma previa das configuracoes de voz selecionadas para o seu curso.",
        "italian": "Ciao, questa e un'anteprima delle impostazioni vocali selezionate per il tuo corso.",
        "dutch": "Hallo, dit is een voorbeeld van de geselecteerde steminstellingen voor uw cursus.",
        "russian": "Здравствуйте, это предварительный просмотр выбранных голосовых настроек для вашего курса.",
        "chinese": "你好，这是您课程所选语音设置的预览。",
        "chinese (simplified)": "你好，这是您课程所选语音设置的预览。",
        "chinese (traditional)": "你好，這是您課程所選語音設定的預覽。",
        "japanese": "こんにちは、これはコースの選択した音声設定のプレビューです。",
        "korean": "안녕하세요, 이것은 코스의 선택된 음성 설정의 미리보기입니다.",
        "arabic": "مرحبًا، هذه معاينة لإعدادات الصوت المحددة لدورتك.",
        "turkish": "Merhaba, bu kursunuz icin secilen ses ayarlarinin bir onizlemesidir.",
        "vietnamese": "Xin chao, day la ban xem truoc cai dat giong noi da chon cho khoa hoc cua ban.",
        "thai": "สวัสดี นี่คือตัวอย่างการตั้งค่าเสียงที่เลือกสำหรับหลักสูตรของคุณ",
        "indonesian": "Halo, ini adalah pratinjau pengaturan suara yang dipilih untuk kursus Anda.",
    }
    text = str(payload.get("text") or "").strip() or preview_defaults.get(language_key, preview_defaults["english"])
    options = {
        "accent": tts.normalize_language_key(selected_language),
        "gender": str(payload.get("gender", "male")).lower(),
        "speed": float(payload.get("speed", 1.0)),
    }

    result = tts.generate_audio(text, options)
    audio_data = result.get("audio_data")
    if not audio_data:
        raise HTTPException(status_code=500, detail="Audio generation failed")

    return StreamingResponse(io.BytesIO(audio_data), media_type="audio/mpeg")


@app.post("/api/course/{course_id}/audio/regenerate-all")
async def regenerate_all_audio(course_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    course_data = load_course_json(course_id)
    audio_options = payload.get("audioOptions", {})

    tts = GoogleTTSService()
    course_language = course_data.get("course", {}).get("courseLanguage", "English")
    audio_options = dict(audio_options or {})
    audio_options["accent"] = tts.normalize_language_key(audio_options.get("accent") or course_language)
    audio_options["gender"] = str(audio_options.get("gender") or "male").lower()
    audio_options["speed"] = float(audio_options.get("speed") or 1.0)

    success_count = 0
    modules = course_data.get("modules", [])
    for idx, module in enumerate(modules, 1):
        module_num = module.get("moduleNumber", idx)
        content = module.get("content", {})
        sections = content.get("sections", []) if isinstance(content, dict) else []
        
        if sections:
            for s_idx, section in enumerate(sections, 1):
                audio_result = tts.generate_section_audio(section, section.get("sectionTitle", ""), audio_options)
                if not audio_result or (not audio_result.get("audio_data") and not audio_result.get("is_chunked")):
                    continue
                section_text = audio_result.get("text", "")
                
                audio_filename = f"module_{module_num}_section_{s_idx}_audio.mp3"
                audio_output_path = OUTPUT_DIR / "assets" / audio_filename
                audio_output_path.parent.mkdir(parents=True, exist_ok=True)
                
                if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                    audio_data = b"".join(
                        chunk["audio_data"]
                        for chunk in audio_result["audio_chunks"]
                        if chunk.get("audio_data")
                    )
                    if audio_data:
                        audio_output_path.write_bytes(audio_data)
                        section["audioPath"] = str(audio_output_path)
                        section["transcript"] = audio_result.get("text", section_text)
                        success_count += 1
                else:
                    saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)
                    if saved_path and saved_path.exists():
                        section["audioPath"] = str(saved_path)
                        section["transcript"] = audio_result.get("text", section_text)
                        success_count += 1
            # clear module-level audio
            module.pop("audioPath", None)
            module.pop("audioPaths", None)
        else:
            audio_result = tts.generate_module_audio(content, audio_options)
            audio_filename = f"module_{module_num}_audio.mp3"
            audio_output_path = OUTPUT_DIR / "assets" / audio_filename
            audio_output_path.parent.mkdir(parents=True, exist_ok=True)
    
            if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                audio_data = b"".join(
                    chunk["audio_data"]
                    for chunk in audio_result["audio_chunks"]
                    if chunk.get("audio_data")
                )
                if audio_data:
                    audio_output_path.write_bytes(audio_data)
                    module["audioPath"] = str(audio_output_path)
                    module.pop("audioPaths", None)
                    module["transcript"] = audio_result.get("text", "")
                    success_count += 1
            else:
                saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)
                if saved_path and saved_path.exists():
                    module["audioPath"] = str(saved_path)
                    module.pop("audioPaths", None)
                    module["transcript"] = audio_result.get("text", "")
                    success_count += 1

    save_course_json(course_data)
    return {"success": True, "updated": success_count, "course_data": course_data}


@app.post("/api/course/{course_id}/module/{module_num}/audio")
async def regenerate_module_audio(course_id: str, module_num: int, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    course_data = load_course_json(course_id)
    audio_options = payload.get("audioOptions", {})

    tts = GoogleTTSService()
    course_language = course_data.get("course", {}).get("courseLanguage", "English")
    audio_options = dict(audio_options or {})
    audio_options["accent"] = tts.normalize_language_key(audio_options.get("accent") or course_language)
    audio_options["gender"] = str(audio_options.get("gender") or "male").lower()
    audio_options["speed"] = float(audio_options.get("speed") or 1.0)
    modules = course_data.get("modules", [])

    target = None
    for idx, module in enumerate(modules, 1):
        if module.get("moduleNumber", idx) == module_num:
            target = module
            break

    if not target:
        raise HTTPException(status_code=404, detail="Module not found")

    try:
        content = target.get("content", {})
        sections = content.get("sections", []) if isinstance(content, dict) else []
        if sections:
            for s_idx, section in enumerate(sections, 1):
                audio_result = tts.generate_section_audio(section, section.get("sectionTitle", ""), audio_options)
                if not audio_result or (not audio_result.get("audio_data") and not audio_result.get("is_chunked")):
                    continue
                section_text = audio_result.get("text", "")
                audio_filename = f"module_{module_num}_section_{s_idx}_audio.mp3"
                audio_output_path = OUTPUT_DIR / "assets" / audio_filename
                audio_output_path.parent.mkdir(parents=True, exist_ok=True)

                if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                    audio_data = b"".join(
                        chunk["audio_data"]
                        for chunk in audio_result["audio_chunks"]
                        if chunk.get("audio_data")
                    )
                    if audio_data:
                        audio_output_path.write_bytes(audio_data)
                        section["audioPath"] = str(audio_output_path)
                        section["transcript"] = audio_result.get("text", section_text)
                else:
                    saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)
                    if saved_path and saved_path.exists():
                        section["audioPath"] = str(saved_path)
                        section["transcript"] = audio_result.get("text", section_text)

            target.pop("audioPath", None)
            target.pop("audioPaths", None)
            target.pop("transcript", None)
        else:
            audio_result = tts.generate_module_audio(target.get("content", {}), audio_options)
            audio_filename = f"module_{module_num}_audio.mp3"
            audio_output_path = OUTPUT_DIR / "assets" / audio_filename
            audio_output_path.parent.mkdir(parents=True, exist_ok=True)
    
            if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                audio_data = b"".join(
                    chunk["audio_data"]
                    for chunk in audio_result["audio_chunks"]
                    if chunk.get("audio_data")
                )
                if audio_data:
                    audio_output_path.write_bytes(audio_data)
                    target["audioPath"] = str(audio_output_path)
                    target.pop("audioPaths", None)
                    target["transcript"] = audio_result.get("text", "")
            else:
                saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)
                if saved_path and saved_path.exists():
                    target["audioPath"] = str(saved_path)
                    target.pop("audioPaths", None)
                    target["transcript"] = audio_result.get("text", "")
    except Exception as exc:
        logger.warning(f"Failed to regenerate audio for Module {module_num}: {exc}")

    save_course_json(course_data)
    return {"course_data": course_data}


@app.post("/api/course/{course_id}/module/{module_num}/section/{section_num}/audio")
async def regenerate_section_audio(course_id: str, module_num: int, section_num: int, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    course_data = load_course_json(course_id)
    audio_options = payload.get("audioOptions", {})

    tts = GoogleTTSService()
    course_language = course_data.get("course", {}).get("courseLanguage", "English")
    audio_options = dict(audio_options or {})
    audio_options["accent"] = tts.normalize_language_key(audio_options.get("accent") or course_language)
    audio_options["gender"] = str(audio_options.get("gender") or "male").lower()
    audio_options["speed"] = float(audio_options.get("speed") or 1.0)
    modules = course_data.get("modules", [])

    target = None
    for idx, module in enumerate(modules, 1):
        if module.get("moduleNumber", idx) == module_num:
            target = module
            break

    if not target:
        raise HTTPException(status_code=404, detail="Module not found")
        
    content = target.get("content", {})
    sections = content.get("sections", []) if isinstance(content, dict) else []
    
    if not sections or section_num < 1 or section_num > len(sections):
        raise HTTPException(status_code=404, detail="Section not found")
        
    section = sections[section_num - 1]

    try:
        audio_result = tts.generate_section_audio(section, section.get("sectionTitle", ""), audio_options)
        if not audio_result or (not audio_result.get("audio_data") and not audio_result.get("is_chunked")):
            raise Exception("No audio data generated for section")
        
        section_text = audio_result.get("text", "")
        audio_filename = f"module_{module_num}_section_{section_num}_audio.mp3"
        audio_output_path = OUTPUT_DIR / "assets" / audio_filename
        audio_output_path.parent.mkdir(parents=True, exist_ok=True)

        if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
            audio_data = b"".join(
                chunk["audio_data"]
                for chunk in audio_result["audio_chunks"]
                if chunk.get("audio_data")
            )
            if audio_data:
                audio_output_path.write_bytes(audio_data)
                section["audioPath"] = str(audio_output_path)
                section["transcript"] = audio_result.get("text", section_text)
        else:
            saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)
            if saved_path and saved_path.exists():
                section["audioPath"] = str(saved_path)
                section["transcript"] = audio_result.get("text", section_text)

        target.pop("audioPath", None)
        target.pop("audioPaths", None)
    except Exception as exc:
        logger.warning(f"Failed to regenerate audio for Module {module_num} Section {section_num}: {exc}")

    save_course_json(course_data)
    return {"course_data": course_data}


@app.post("/api/course/{course_id}/module/{module_num}/regenerate")
async def regenerate_module(course_id: str, module_num: int, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    course_data = load_course_json(course_id)
    modules = course_data.get("modules", [])
    target = None
    for idx, module in enumerate(modules, 1):
        if module.get("moduleNumber", idx) == module_num:
            target = module
            break

    if not target:
        raise HTTPException(status_code=404, detail="Module not found")

    gemini = GeminiService()
    flashcard_gen = FlashcardGenerator()
    tts = GoogleTTSService()

    original_user_input = course_data.get("metadata", {}).get("user_input") or {
        "courseTitle": course_data.get("course", {}).get("title", "Course"),
        "targetAudience": "General",
        "institute": "Not specified",
        "relevantLaws": "US Federal Guidelines",
        "tone": "Professional",
    }
    
    # Merge payload to preserve topics correctly
    if "preserve_topics" in payload:
        original_user_input["preserve_topics"] = payload["preserve_topics"]

    course_context = course_data.get("course", {})

    existing_content = target.get("content", {})
    existing_interactive = existing_content.get("interactiveBlock", {})
    raw_interactive_type = existing_interactive.get("type", None) if isinstance(existing_interactive, dict) else None
    # Normalize to lowercase so schema_map lookup in gemini_service works correctly.
    # If the original module had no interactive block, this stays None (no block added).
    interactive_type = raw_interactive_type.lower() if raw_interactive_type else None

    module_content = await asyncio.to_thread(
        gemini.generate_module_content,
        module_num,
        target.get("moduleTitle", f"Module {module_num}"),
        course_context,
        original_user_input,
        None,           # previous_content: pass None to match initial generation behaviour
        interactive_type,
        is_regeneration=True,
    )

    # Strip Gemini filler phrases — mirrors _generate_single_module in course_generator.py
    course_gen = CourseGenerator()
    module_content = course_gen._trim_verbose_content(module_content)

    # Hard guardrail: strip any interactiveBlock Gemini hallucinated when module had none
    if interactive_type is None and isinstance(module_content, dict):
        module_content.pop("interactiveBlock", None)

    knowledge_check = await asyncio.to_thread(
        gemini.generate_knowledge_check,
        module_content,
        target.get("moduleTitle", f"Module {module_num}"),
        original_user_input.get("courseLanguage", "English"),
        original_user_input.get("courseTitle", ""),
    )

    # Only generate flashcards if the user opted in — mirrors _generate_single_module
    add_flashcards = original_user_input.get("addFlashcards", False)
    sections = module_content.get("sections", []) if isinstance(module_content, dict) else []
    if add_flashcards:
        section_flashcards = {}
        for section_idx, section in enumerate(sections):
            section_title = section.get("sectionTitle", f"Section {section_idx + 1}")
            section_flashcards_list = await asyncio.to_thread(
                flashcard_gen.generate_flashcards,
                section,
                section_title
            )
            if section_flashcards_list:
                section_flashcards[section_idx] = section_flashcards_list
                section["flashcards"] = section_flashcards_list
        flashcards = section_flashcards.get(0, []) if section_flashcards else []
    else:
        # Preserve existing flashcards; do not add new ones
        flashcards = target.get("flashcards", [])
        logger.info(f"Flashcard generation skipped for Module {module_num} (user opted out)")

    audio_options = payload.get("audioOptions") or original_user_input.get("audioOptions", {})
    audio_options = dict(audio_options or {})
    source_language = original_user_input.get("courseLanguage") or course_data.get("course", {}).get("courseLanguage", "English")
    audio_options["accent"] = tts.normalize_language_key(audio_options.get("accent") or source_language)
    audio_options["gender"] = str(audio_options.get("gender") or "male").lower()
    audio_options["speed"] = float(audio_options.get("speed") or 1.0)

    target["content"] = module_content
    # If the original module had an interactive block and Gemini omitted it, restore it
    if isinstance(target["content"], dict) and existing_interactive:
        if not target["content"].get("interactiveBlock"):
            target["content"]["interactiveBlock"] = existing_interactive

    target["knowledgeCheck"] = knowledge_check
    target["flashcards"] = flashcards

    # Use per-module presence, not global user_input flags
    has_image = bool(target.get("imagePath"))
    has_audio = bool(
        target.get("audioPath") or
        any(s.get("audioPath") for s in (target.get("sectionAudio") or []))
    )

    # Regenerate image if the user originally opted in and the module had one
    include_images = original_user_input.get("includeImages", False)
    if has_image:
        try:
            module_index = module_num - 1  # convert 1-based to 0-based
            course_title = course_data.get("course", {}).get("title", "Course")
            concept = await image_gen_instance.plan_concept_for_module(
                course_title=course_title,
                module=target,
                module_index=module_index,
            )
            if concept:
                import time as _time, random as _random
                seed = int(_time.time()) + _random.randint(0, 1000)
                image_bytes = await image_gen_instance.generate_image_for_concept(concept, seed=seed)
                img_filename = f"{course_id}_module_{module_num}_image.png"
                img_path = OUTPUT_DIR / "assets" / img_filename
                ImageGeneratorService._save_image(image_bytes, img_path)
                try:
                    record_images(UPLOADS_DIR, course_id, course_title, 1, is_regen=True)
                except Exception as exc:
                    logger.warning(f"Failed to record image stats: {exc}")
                target["imagePath"] = str(img_path)
        except Exception as exc:
            logger.warning(f"Image regeneration failed for Module {module_num}: {exc}")

    # Only regenerate audio if the user originally opted in — mirrors _generate_single_module
    include_audio = original_user_input.get("includeAudio", True)
    if has_audio:
        try:
            if sections:
                all_transcripts = []
                section_audio_data = []
                for s_idx, section in enumerate(sections):
                    s_title = section.get("sectionTitle", f"Section {s_idx + 1}")
                    try:
                        s_result = tts.generate_section_audio(section, s_title, audio_options)
                        s_path = None
                        if s_result.get("audio_data"):
                            s_filename = f"module_{module_num}_section_{s_idx + 1}.mp3"
                            s_out = OUTPUT_DIR / "assets" / s_filename
                            s_out.parent.mkdir(parents=True, exist_ok=True)
                            s_saved = tts.save_audio(s_result["audio_data"], s_out)
                            if s_saved:
                                section["audioPath"] = str(s_saved)
                                section["transcript"] = s_result.get("text", "")
                                all_transcripts.append(s_result.get("text", ""))
                                s_path = str(s_saved)

                        section_audio_data.append({
                            "sectionIndex": s_idx,
                            "sectionTitle": s_title,
                            "audioPath": s_path,
                            "audioPaths": None,
                            "transcript": section.get("transcript", ""),
                            "duration_seconds": s_result.get("duration_seconds", 0) if s_result else 0
                        })
                    except Exception as e:
                        logger.warning(f"Failed audio for section {s_idx+1}: {e}")

                target["audioPath"] = None
                target.pop("audioPaths", None)
                target["transcript"] = "\n\n".join(all_transcripts)
                target["sectionAudio"] = section_audio_data
            else:
                audio_result = tts.generate_module_audio(module_content, audio_options)
                audio_filename = f"module_{module_num}_audio.mp3"
                audio_output_path = OUTPUT_DIR / "assets" / audio_filename
                audio_output_path.parent.mkdir(parents=True, exist_ok=True)
                saved_path = None

                if audio_result.get("is_chunked") and audio_result.get("audio_chunks"):
                    audio_data = b"".join(
                        chunk["audio_data"]
                        for chunk in audio_result["audio_chunks"]
                        if chunk.get("audio_data")
                    )
                    if audio_data:
                        audio_output_path.write_bytes(audio_data)
                        saved_path = audio_output_path
                else:
                    saved_path = tts.save_audio(audio_result["audio_data"], audio_output_path)

                if saved_path and saved_path.exists() and audio_result:
                    target["audioPath"] = str(saved_path)
                    target.pop("audioPaths", None)
                    target["transcript"] = audio_result.get("text", "")
        except Exception as exc:
            logger.warning(f"Failed to regenerate module audio for Module {module_num}: {exc}")

    save_course_json(course_data)
    return {"course_data": course_data}


# History routes are handled by routes/history.py (registered via app.include_router above)


@app.get("/api/course/{course_id}/download/xapi")
async def download_xapi(course_id: str) -> FileResponse:
    course_data = load_course_json(course_id)
    course_title = course_data.get("course", {}).get("title", "Course")
    course_filename = sanitize_filename(course_title)

    output_path = OUTPUT_DIR / course_id
    output_path.mkdir(parents=True, exist_ok=True)

    # Clean stale artifacts before regenerating
    for item in output_path.iterdir():
        if item.name == "course.json":
            continue  # keep saved course data
        try:
            if item.is_dir() and item.name != "assets":
                shutil.rmtree(item, ignore_errors=True)
            elif item.suffix == ".zip":
                item.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Could not clean stale artifact {item}: {e}")

    package_path = xAPIGenerator_instance.generate_package(course_data, str(output_path))
    
    # Write zip to parent directory (outside the packaged folder) to prevent self-inclusion
    zip_path = OUTPUT_DIR / f"{course_id}_{course_filename}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in Path(package_path).rglob("*"):
            if file_path.is_file() and file_path.suffix != ".zip":
                arcname = file_path.relative_to(package_path)
                zipf.write(file_path, arcname)

    # Do NOT delete package_path here, because package_path IS the course folder containing course.json
    # shutil.rmtree(package_path, ignore_errors=True)

    return FileResponse(zip_path, media_type="application/zip", filename=f"{course_filename}.zip")


@app.get("/api/course/{course_id}/download/json")
async def download_json(course_id: str) -> FileResponse:
    json_path = OUTPUT_DIR / course_id / "course.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Course JSON not found")

    course_data = load_course_json(course_id)
    course_title = course_data.get("course", {}).get("title")
    if not course_title and course_data.get("outline"):
        course_title = course_data["outline"].get("courseTitle", "Course")
    course_filename = sanitize_filename(course_title or "Course")
    return FileResponse(json_path, media_type="application/json", filename=f"{course_filename}.json")


@app.get("/api/course/{course_id}/download/pdf")
async def download_pdf(course_id: str) -> FileResponse:
    course_data = load_course_json(course_id)
    course_title = course_data.get("course", {}).get("title")
    if not course_title and course_data.get("outline"):
        course_title = course_data["outline"].get("courseTitle", "Course")
    course_filename = sanitize_filename(course_title or "Course")

    pdf_path = OUTPUT_DIR / course_id / f"{course_filename}.pdf"
    pdf_generator_instance.generate_pdf(course_data, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{course_filename}.pdf")


@app.get("/api/media/{filename}")
async def get_media(filename: str) -> FileResponse:
    safe_name = os.path.basename(filename)
    if safe_name == "null" or safe_name == "undefined":
        raise HTTPException(status_code=404, detail="File not found")
        
    file_path = OUTPUT_DIR / "assets" / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # Fix F10: infer correct Content-Type so browsers play audio/display images natively
    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(file_path, media_type=media_type or "application/octet-stream")
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Silently ignore browser icon requests so they don't spam the terminal with 404s."""
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/x-icon")

@app.post("/api/course/{course_id}/image/regenerate")
async def regenerate_module_image(course_id: str, request: Request):
    """
    Regenerate the image for a single module.
    Mirrors Chitra's handleRegenerate() in App.tsx (lines 221-254).
    """
    body = await request.json()
    module_index = body.get("moduleIndex")  # 0-based

    if module_index is None:
        raise HTTPException(status_code=400, detail="moduleIndex is required")

    course_data = load_course_json(course_id)
    modules = course_data.get("modules", [])

    if module_index >= len(modules):
        raise HTTPException(status_code=404, detail=f"Module index {module_index} not found")

    module = modules[module_index]
    module_title = module.get("moduleTitle", f"Module {module_index + 1}")

    course_title = course_data.get("course", {}).get("title", "Course")
    concept = await image_gen_instance.plan_concept_for_module(
        course_title=course_title,
        module=module,
        module_index=module_index,
    )
    if not concept:
        module_context = build_module_image_context(module)
        concept = {
            "id": module_index + 1,
            "title": module_title,
            "prompt_used": (
                module.get("imageConcept", {}).get("prompt_used")
                or f"Create a clear instructional scene that visually teaches: {module_context}"
            ),
            "visual_details": module.get("imageConcept", {}).get("visual_details", ""),
        }

    import time, random
    seed = int(time.time()) + random.randint(0, 1000)  # new seed = new image

    try:
        image_bytes = await image_gen_instance.generate_image_for_concept(concept, seed=seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save with timestamp to bust cache
    filename = f"{course_id}_module_{module_index + 1}_image.png"
    image_path = OUTPUT_DIR / "assets" / filename
    ImageGeneratorService._save_image(image_bytes, image_path)

    # Update course.json
    modules[module_index]["imagePath"] = str(image_path)
    save_course_json(course_data)

    # Record stats
    try:
        record_images(UPLOADS_DIR, course_id, course_title, 1, is_regen=True)
    except Exception as e:
        logger.warning(f"Failed to record image stats: {e}")

    return {"filename": filename, "imagePath": str(image_path)}


@app.post("/api/course/{course_id}/image/regenerate-batch")
async def regenerate_batch_images(course_id: str, request: Request):
    """
    Regenerate images for multiple selected modules concurrently.
    Mirrors Chitra's handleRegenerateSelected() in App.tsx (lines 268-318).
    Max concurrency: 2 (matches Chitra's MAX_CONCURRENT_IMAGES).
    """
    body = await request.json()
    module_indices = body.get("moduleIndices", [])  # list of 0-based indices

    if not module_indices:
        raise HTTPException(status_code=400, detail="moduleIndices must be a non-empty list")

    course_data = load_course_json(course_id)
    modules = course_data.get("modules", [])

    import asyncio, time, random
    from config import MAX_CONCURRENT_IMAGES
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_IMAGES)
    results = {}

    async def regen_one(module_index: int):
        async with semaphore:
            if module_index >= len(modules):
                results[str(module_index)] = {"error": "Module not found"}
                return

            module = modules[module_index]
            module_title = module.get("moduleTitle", f"Module {module_index + 1}")
            course_title = course_data.get("course", {}).get("title", "Course")
            concept = await image_gen_instance.plan_concept_for_module(
                course_title=course_title,
                module=module,
                module_index=module_index,
            )
            if not concept:
                module_context = build_module_image_context(module)
                concept = {
                    "id": module_index + 1,
                    "title": module_title,
                    "prompt_used": (
                        module.get("imageConcept", {}).get("prompt_used")
                        or f"Create a clear instructional scene that visually teaches: {module_context}"
                    ),
                    "visual_details": "",
                }
            seed = int(time.time()) + random.randint(0, 1000)

            try:
                image_bytes = await image_gen_instance.generate_image_for_concept(concept, seed=seed)
                filename = f"{course_id}_module_{module_index + 1}_image.png"
                image_path = OUTPUT_DIR / "assets" / filename
                ImageGeneratorService._save_image(image_bytes, image_path)
                modules[module_index]["imagePath"] = str(image_path)
                results[str(module_index)] = {"filename": filename}
            except Exception as e:
                results[str(module_index)] = {"error": str(e)}

    await asyncio.gather(*[regen_one(i) for i in module_indices])
    save_course_json(course_data)

    # Record stats
    try:
        module_count = len([r for r in results.values() if "error" not in r])
        if module_count > 0:
            course_title = course_data.get("course", {}).get("title", "Course")
            record_images(UPLOADS_DIR, course_id, course_title, module_count, is_regen=True)
    except Exception as e:
        logger.warning(f"Failed to record batch image stats: {e}")

    return {"results": results}


@app.post("/api/course/{course_id}/image/edit")
async def edit_module_image(course_id: str, request: Request):
    """
    Edit an existing module image using a text instruction.
    Mirrors Chitra's handleEditImage() via gemini-3.1-flash-image-preview.
    """
    body = await request.json()
    module_index = body.get("moduleIndex")
    edit_prompt = body.get("editPrompt", "").strip()

    if module_index is None:
        raise HTTPException(status_code=400, detail="moduleIndex is required")
    if not edit_prompt:
        raise HTTPException(status_code=400, detail="editPrompt is required")

    course_data = load_course_json(course_id)
    modules = course_data.get("modules", [])

    if module_index >= len(modules):
        raise HTTPException(status_code=404, detail=f"Module index {module_index} not found")

    module = modules[module_index]
    existing_path = module.get("imagePath")

    if not existing_path or not Path(existing_path).exists():
        raise HTTPException(
            status_code=404,
            detail="No existing image found for this module. Generate one first."
        )

    # Read existing image bytes
    image_bytes = Path(existing_path).read_bytes()

    try:
        edited_bytes = await image_gen_instance.edit_image(image_bytes, edit_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Overwrite the same file
    filename = f"{course_id}_module_{module_index + 1}_image.png"
    image_path = OUTPUT_DIR / "assets" / filename
    ImageGeneratorService._save_image(edited_bytes, image_path)

    modules[module_index]["imagePath"] = str(image_path)
    save_course_json(course_data)

    try:
        course_title = course_data.get("course", {}).get("title", "Course")
        record_images(UPLOADS_DIR, course_id, course_title, 1, is_regen=True)
    except Exception as exc:
        logger.warning(f"Failed to record image stats: {exc}")

    return {"filename": filename, "imagePath": str(image_path)}


@app.post("/api/images/upload")
async def upload_images(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    session_id = uuid.uuid4().hex
    session_dir = UPLOADS_DIR / "temp_images" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Allowed standalone image extensions (matches frontend accept attribute)
    allowed_image_extensions = {".jpg", ".jpeg", ".png"}
    # Extensions we will extract from ZIP (we do not extract .gif/.bmp — they won't be in the accept list)
    image_extensions_in_zip = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    stored_images: Dict[str, Path] = {}

    for file in files:
        file_ext = Path(file.filename).suffix.lower()

        if file_ext == ".zip":
            contents = await file.read()
            zip_path = session_dir / file.filename
            with open(zip_path, "wb") as f:
                f.write(contents)

            try:
                images_found = 0
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    for item in zip_ref.infolist():
                        item_ext = Path(item.filename).suffix.lower()
                        if item_ext not in image_extensions_in_zip:
                            continue
                        item_name = Path(item.filename).name
                        if not item_name:
                            continue
                        extract_path = session_dir / item_name
                        extract_path = _avoid_overwrite(extract_path)
                        with zip_ref.open(item) as source:
                            with open(extract_path, "wb") as target:
                                target.write(source.read())
                        stored_images[extract_path.name] = extract_path
                        images_found += 1
                if images_found == 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"The ZIP '{file.filename}' contains no supported images (.png, .jpg, .jpeg). "
                               "Please upload a ZIP that contains only images."
                    )
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail=f"Invalid ZIP file: {file.filename}")

        elif file_ext in allowed_image_extensions:
            contents = await file.read()
            img_path = session_dir / file.filename
            img_path = _avoid_overwrite(img_path)
            with open(img_path, "wb") as f:
                f.write(contents)
            stored_images[img_path.name] = img_path

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_ext}' for image upload. "
                       "Accepted: .png, .jpg, .jpeg, or a .zip containing images."
            )

    _image_sessions[session_id] = stored_images
    return {"session_id": session_id, "images": sorted(stored_images.keys())}


def _avoid_overwrite(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    while counter <= 9999:  # Fix F5: cap to prevent infinite loop on full disk
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
    raise OSError(f"Too many files with name '{path.name}' in {parent} — cannot create unique filename")


@app.post("/api/images/match")
async def match_images(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    course_data = payload.get("course_data")
    if not session_id or session_id not in _image_sessions:
        raise HTTPException(status_code=404, detail="Image session not found")
    if not course_data:
        raise HTTPException(status_code=400, detail="course_data is required")

    image_names = list(_image_sessions[session_id].keys())
    modules = course_data.get("modules", [])
    matches = auto_match_images_to_modules(modules, image_names)
    return {"matches": matches}


@app.get("/api/images/{session_id}/{filename}")
async def get_uploaded_image(session_id: str, filename: str) -> FileResponse:
    session = _image_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Image session not found")

    safe_name = os.path.basename(filename)
    path = session.get(safe_name)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(path)


@app.post("/api/images/save")
async def save_images(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    course_id = payload.get("course_id")
    mappings = payload.get("mappings", {})

    if not session_id or session_id not in _image_sessions:
        raise HTTPException(status_code=404, detail="Image session not found")
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id is required")

    course_data = load_course_json(course_id)
    session = _image_sessions[session_id]

    updated = 0
    for module in course_data.get("modules", []):
        module_num = module.get("moduleNumber")
        selection = mappings.get(str(module_num)) or mappings.get(module_num)
        if not selection:
            continue
        img_path = session.get(selection)
        if not img_path or not img_path.exists():
            continue

        img_ext = img_path.suffix
        final_img_name = f"{course_id}_module_{module_num}_image{img_ext}"
        final_img_path = OUTPUT_DIR / "assets" / final_img_name
        final_img_path.parent.mkdir(parents=True, exist_ok=True)

        # Fix F6: shutil.copyfile uses OS-level copy — no full-file memory load
        shutil.copyfile(img_path, final_img_path)

        module["imagePath"] = str(final_img_path)
        updated += 1

    save_course_json(course_data)
    return {"updated": updated, "course_data": course_data}


@app.get("/api/tts/voices")
async def list_voices(language: Optional[str] = None) -> Dict[str, Any]:
    tts = GoogleTTSService()
    voices = tts.list_available_voices(language=language)
    return {"voices": voices, "count": len(voices), "language": language or "all"}
