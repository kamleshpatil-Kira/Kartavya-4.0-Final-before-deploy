"""
Utility to load course data from various file formats (JSON, DOC, PDF, PPTX, xAPI ZIP, SCORM 1.2 ZIP)
"""
import json
import zipfile
import re
from pathlib import Path
from typing import Dict, Any, Optional
from utils.document_processor import DocumentProcessor
from utils.logger import logger, log_activity


class CourseLoader:
    """Load course data from various file formats and return a rich extraction summary"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
    
    def load_course(self, file_path: Path, file_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Load course data from file and return rich extraction summary.
        
        Supports:
        - JSON: Direct course data
        - xAPI ZIP / SCORM 1.2 ZIP: Extract course.json or manifest + HTML
        - DOC, DOCX, PDF, PPTX: Full text extraction
        
        Returns a dict with:
          - extracted_content: full raw text for Gemini
          - course_title: best-guess title
          - file_type: detected file type
          - word_count: size indicator
        """
        log_activity("Loading course from file", {"file_path": str(file_path), "file_type": file_type})
        
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.json':
                return self._load_from_json(file_path)
            elif suffix == '.zip':
                return self._load_from_zip(file_path)
            elif suffix in ['.doc', '.docx', '.pdf', '.pptx']:
                return self._load_from_document(file_path)
            else:
                raise ValueError(f"Unsupported file type for course loading: {suffix}")
        except Exception as e:
            logger.error(f"Failed to load course from {file_path}: {e}", exc_info=True)
            raise
    
    def _load_from_json(self, file_path: Path) -> Dict[str, Any]:
        """Load course data from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            course_data = json.load(f)
        
        course_title = 'Unknown'
        if course_data.get('course') and isinstance(course_data['course'], dict):
            course_title = course_data['course'].get('title', 'Unknown')
        elif course_data.get('courseTitle'):
            course_title = course_data['courseTitle']
        elif course_data.get('title'):
            course_title = course_data['title']
        
        # Detect modules
        modules = course_data.get('modules', [])
        module_titles = [m.get('moduleTitle') or m.get('title', f'Module {i+1}') 
                        for i, m in enumerate(modules)]
        
        serialized = json.dumps(course_data, indent=2, ensure_ascii=False)
        
        logger.info(f"Loaded course JSON: {course_title} ({len(modules)} modules)")
        
        return {
            "extracted_content": serialized[:40000],  # Cap for Gemini token limits
            "course_title": course_title,
            "file_type": "json",
            "detected_modules": module_titles,
            "word_count": len(serialized.split()),
            "raw_course_data": course_data  # Pass through for direct use
        }
    
    def _load_from_zip(self, file_path: Path) -> Dict[str, Any]:
        """Load from xAPI or SCORM ZIP — delegate detection to DocumentProcessor"""
        result = self.processor.process_document(file_path)
        content = result.get("content", "")
        meta = result.get("metadata", {})
        file_type = meta.get("type", "zip")
        course_title = meta.get("course_title", file_path.stem)

        # Try to detect module structure from content
        module_titles = self._extract_module_hints(content)

        # Try to find and extract a raw course.json inside the ZIP (xAPI/SCORM exports)
        raw_course_data = None
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # Look for course.json at any depth inside the archive
                json_candidates = [n for n in zf.namelist() if n.endswith("course.json")]
                if not json_candidates:
                    # Also try any .json at root level
                    json_candidates = [n for n in zf.namelist()
                                       if n.endswith(".json") and "/" not in n.strip("/")]
                for candidate in json_candidates:
                    try:
                        with zf.open(candidate) as jf:
                            data = json.load(jf)
                        # Only treat as a valid course if it has a modules array
                        if isinstance(data, dict) and data.get("modules"):
                            raw_course_data = data
                            course_title = (data.get("course") or {}).get("title", course_title)
                            break
                    except Exception:
                        continue
        except Exception:
            pass

        logger.info(f"Loaded {file_type}: {course_title}")

        return {
            "extracted_content": content,
            "course_title": course_title,
            "file_type": file_type,
            "detected_modules": module_titles,
            "word_count": meta.get("word_count", len(content.split())),
            **({"raw_course_data": raw_course_data} if raw_course_data else {}),
        }
    
    def _load_from_document(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from document for course regeneration"""
        result = self.processor.process_document(file_path)
        content = result.get("content", "")
        meta = result.get("metadata", {})
        
        # Extract title: try to find prominent heading in first lines
        course_title = self._extract_title_from_content(content, file_path.stem)
        
        # Detect module structure hints
        module_titles = self._extract_module_hints(content)
        
        suffix = file_path.suffix.lower().lstrip('.')
        
        logger.info(f"Loaded {suffix} document: {course_title} (~{meta.get('word_count', 0)} words)")
        
        return {
            "extracted_content": content,
            "course_title": course_title,
            "file_type": suffix,
            "detected_modules": module_titles,
            "word_count": meta.get("word_count", len(content.split()))
        }
    
    def _extract_title_from_content(self, content: str, fallback: str) -> str:
        """Heuristic title extraction from document content"""
        if not content:
            return fallback
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        for line in lines[:15]:
            # Skip very short or very long lines
            if 5 < len(line) < 150:
                # Avoid lines that look like page footers or headers (all digits, URLs, etc.)
                if not re.match(r'^[\d\s,.]+$', line) and 'http' not in line.lower():
                    return line
        
        # Cleanup filename
        clean = re.sub(r'\s*\(\d+\)\s*$', '', fallback).strip()
        return clean or 'Untitled Course'
    
    def _extract_module_hints(self, content: str) -> list:
        """Try to detect module/chapter headings from extracted text"""
        if not content:
            return []
        
        patterns = [
            r'^(?:Module|Chapter|Unit|Section)\s+\d+[:\.\-\s]+(.*)',
            r'^\d+\.\s+([A-Z][^\n]{5,80})',
        ]
        
        found = []
        for line in content.split('\n'):
            line = line.strip()
            for pattern in patterns:
                m = re.match(pattern, line, re.IGNORECASE)
                if m:
                    title = m.group(1).strip()
                    if title and title not in found:
                        found.append(title)
                        break
            if len(found) >= 12:
                break
        
        return found
