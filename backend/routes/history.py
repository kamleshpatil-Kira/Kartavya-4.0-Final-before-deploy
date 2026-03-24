"""
History route handlers.
Manages course generation history (load, clear, delete by ID).
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from utils.image_stats import load_stats
from utils.logger import logger

def _get_history_path(uploads_dir: Path) -> Path:
    return uploads_dir / "course_history.json"


def load_history(uploads_dir: Path) -> List[Dict[str, Any]]:
    history_file = _get_history_path(uploads_dir)
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Failed to load course history: {exc}")  # Fix G2: was silent
    return []


def save_history(uploads_dir: Path, history: List[Dict[str, Any]]) -> None:
    history_file = _get_history_path(uploads_dir)
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, default=str)


def save_course_to_history(uploads_dir: Path, course_data: Dict[str, Any]) -> None:
    """Add a course to the history file (no-op if already exists)."""
    course_title = "Unknown"
    if isinstance(course_data.get("course"), dict) and course_data["course"].get("title"):
        course_title = course_data["course"]["title"]
    elif isinstance(course_data.get("outline"), dict) and course_data["outline"].get("courseTitle"):
        course_title = course_data["outline"]["courseTitle"]
    elif course_data.get("courseTitle"):
        course_title = course_data.get("courseTitle")
    elif course_data.get("title"):
        course_title = course_data.get("title")

    course_id = course_data.get("course", {}).get("id", f"course-{int(time.time())}")

    description = ""
    if isinstance(course_data.get("course"), dict) and course_data["course"].get("description"):
        description = course_data["course"]["description"][:100]
    elif isinstance(course_data.get("outline"), dict) and course_data["outline"].get("courseDescription"):
        description = course_data["outline"]["courseDescription"][:100]

    history_entry = {
        "id": course_id,
        "title": course_title,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "modules": len(course_data.get("modules", [])),
        "has_quiz": bool(course_data.get("quiz")),
        "has_interactive": any(
            (mod.get("content") or {}).get("interactiveBlock") is not None or
            (mod.get("flashcards") and len(mod.get("flashcards")) > 0)
            for mod in (course_data.get("modules") or [])
        ),
        "course_level": course_data.get("metadata", {}).get("user_input", {}).get("courseLevel"),
        "description": description,
    }

    history = load_history(uploads_dir)
    if course_id not in [h.get("id") for h in history]:
        history.insert(0, history_entry)
        save_history(uploads_dir, history)


def make_router(uploads_dir: Path) -> APIRouter:
    """Factory: returns the router with uploads_dir bound via closure."""
    # Fix G1: router created INSIDE the factory so make_router() called twice
    # returns two separate routers — no duplicate route registration.
    router = APIRouter(prefix="/api/history", tags=["history"])
    @router.get("")
    async def get_history() -> Dict[str, Any]:
        return {"history": load_history(uploads_dir)}

    @router.delete("")
    async def clear_history() -> Dict[str, Any]:
        history_file = _get_history_path(uploads_dir)
        if history_file.exists():
            history_file.unlink()
        return {"success": True}

    @router.delete("/{course_id}")
    async def delete_history_entry(course_id: str) -> Dict[str, Any]:
        history = load_history(uploads_dir)
        updated = [h for h in history if h.get("id") != course_id]
        if len(updated) == len(history):
            raise HTTPException(status_code=404, detail="History entry not found")
        save_history(uploads_dir, updated)
        return {"success": True}

    return router


def make_stats_router(uploads_dir: Path) -> APIRouter:
    router = APIRouter(prefix="/api/image-stats", tags=["stats"])

    @router.get("")
    async def get_image_stats():
        return load_stats(uploads_dir)

    return router
