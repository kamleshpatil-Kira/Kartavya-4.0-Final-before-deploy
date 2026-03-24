import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.logger import logger


def load_stats(uploads_dir: Path) -> Dict[str, Any]:
    stats_file = uploads_dir / "image_stats.json"
    if not stats_file.exists():
        return {
            "total_generated": 0,
            "total_regenerated": 0,
            "last_updated": datetime.now().isoformat(),
            "by_course": []
        }
    try:
        with open(stats_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "total_generated": 0,
            "total_regenerated": 0,
            "last_updated": datetime.now().isoformat(),
            "by_course": []
        }

def save_stats(uploads_dir: Path, stats: Dict[str, Any]) -> None:
    stats_file = uploads_dir / "image_stats.json"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    stats["last_updated"] = datetime.now().isoformat()
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def record_images(uploads_dir: Path, course_id: str, title: str, count: int, is_regen: bool = False) -> None:
    stats = load_stats(uploads_dir)
    
    if is_regen:
        stats["total_regenerated"] += count
    else:
        stats["total_generated"] += count
        
    # Append to by_course list
    stats["by_course"].append({
        "course_id": course_id,
        "title": title,
        "generated": 0 if is_regen else count,
        "regenerated": count if is_regen else 0,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep last 1000 entries to prevent file bloat
    if len(stats["by_course"]) > 1000:
        stats["by_course"] = stats["by_course"][-1000:]
        
    save_stats(uploads_dir, stats)
    
    # Log the counts for the user to see in the backend console
    logger.info(f"🟢 IMAGE STATS LIVE COUNT: {stats['total_generated']} Generated | {stats['total_regenerated']} Regenerated")
