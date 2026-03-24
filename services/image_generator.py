"""
Image Generator Service — ported from Chitra (Node.js) to Python.

Uses Gemini's image model to generate photorealistic, educationally relevant
images for each course module.
"""

import asyncio
import base64
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from utils.logger import logger
from utils.image_stats import record_images

# ---------------------------------------------------------------------------
# Prompts & constants ported verbatim from Chitra
# ---------------------------------------------------------------------------

ART_DIRECTOR_SYSTEM_PROMPT = (
    "You are an expert AI Art Director for high-end instructional materials, shooting in the style of editorial "
    "documentary photography. Compose every image as if captured with a full-frame DSLR or mirrorless camera "
    "fitted with a 35–50 mm prime lens: shallow depth-of-field, natural ambient light, true-to-life colours, "
    "candid or posed action that feels genuinely captured rather than staged. "
    "Your task is to plan physically grounded, photorealistic images. "
    "All image concepts must be realistic, logical, and avoid any impossible or surreal elements. "
    "Support widely diverse environments (e.g., outdoors, industrial, residential, abstract, nature, retail, etc.) "
    "depending entirely on the specific context of each concept. "
    "If a scene includes signage, labels, screens, printed materials, or branding, "
    "ensure prompts explicitly describe them as completely obscured by EXTREME Gaussian blur "
    "or out-of-focus depth of field — every character must be 100% illegible, no logos are visible at all. "
    "CRITICAL: When describing people, emphasize natural, anatomically correct poses, especially for hands "
    "and fingers, to ensure flawless realism. If the concept involves an action, the action must be visually "
    "explicit, physically observable, and unambiguous. Avoid vague or implied gestures. "
    "Images must accurately depict real-world, domain-specific scenarios matching the course subject matter. "
    "Foreground subjects and background environments must both be factually correct and contextually appropriate. "
    "FORBIDDEN: generic office desks with nothing on them, handshakes, light-bulb 'idea' shots, "
    "vague motivational silhouettes, clip-art-style diagrams, stock-photo clichés. "
    "Show the actual domain scenario with specific tools, equipment, or environments from that field."
)

STRICT_STYLE_SUFFIX = """
Photorealistic, natural lighting, physically grounded scene.
Consistent perspective and realistic shadows.
Perfect anatomy when humans are present (5 fingers, natural joints, no distortions).
ABSOLUTE CRITICAL RULE ON TEXT: DO NOT GENERATE ANY READABLE TEXT. Any text in the scene (on screens, signs, posters, papers, packaging, clothing, devices, or backgrounds) MUST be heavily blurred using EXTREME depth-of-field blur, motion blur, or be out of focus. It must be 100% illegible. No coherent words, letters, or numbers.
If signage, labels, UI screens, documents, or printed materials appear, they must be heavily blurred and illegible.
No clearly visible logos, branding, trademarks, emblems, icons, or brand-like symbols.
No surreal or impossible elements.
CRITICAL: Do NOT use any specific real-world people.
"""

# Retry config (matches Chitra's MAX_RETRIES=3, INITIAL_BACKOFF_MS=1000)
MAX_RETRIES = 3
INITIAL_BACKOFF_MS = 1000


class ImageGeneratorService:
    """Generates photorealistic course images using Gemini."""

    def __init__(self, api_key: str):
        if not api_key:
            logger.warning("No GEMINI_API_KEY provided — image generation will be unavailable.")
            self.available = False
            return
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.available = True

    # ------------------------------------------------------------------
    # Retry helper (mirrors Chitra's withRetry)
    # ------------------------------------------------------------------
    async def _with_retry(self, fn):
        """Execute *fn* with up to MAX_RETRIES attempts and exponential backoff."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await fn()
            except Exception as exc:
                last_error = exc
                msg = str(exc).lower()
                is_retriable = any(
                    kw in msg for kw in ("503", "unavailable", "overloaded", "other", "deadline")
                )
                if is_retriable and attempt < MAX_RETRIES:
                    delay = (INITIAL_BACKOFF_MS * (2 ** (attempt - 1)) + random.random() * 1000) / 1000
                    logger.warning(
                        f"Image generation attempt {attempt} failed (retriable), "
                        f"retrying in {delay:.1f}s: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
        raise last_error or Exception("Image generation request failed.")

    # ------------------------------------------------------------------
    # Step 1: Analyze course content → image concepts
    # ------------------------------------------------------------------
    async def analyze_content_for_images(
        self,
        course_title: str,
        modules: List[Dict],
        requested_count: int,
        course_metadata: Dict = None,
    ) -> List[Dict[str, Any]]:
        """
        Ask Gemini to plan *requested_count* image concepts based on
        course content.  Returns a list of concept dicts.
        """
        from google.genai import types

        # Build context text from course modules
        context_parts = [f"Course Title: {course_title}\n"]
        for i, mod in enumerate(modules, 1):
            title = mod.get("moduleTitle", f"Module {i}")
            objectives = mod.get("learningObjectives", [])
            content = mod.get("content", {})

            # Extract section titles AND content snippets for richer context
            sections_text = ""
            if isinstance(content, dict):
                sections = content.get("sections", [])
                for sec in sections:
                    sec_title = sec.get("sectionTitle", "")
                    sec_content = sec.get("content", "") or ""
                    # Grab first 150 chars of section body to give AI real domain context
                    snippet = sec_content[:150].replace("\n", " ").strip()
                    if sec_title:
                        if snippet:
                            sections_text += f"  - {sec_title}: {snippet}...\n"
                        else:
                            sections_text += f"  - {sec_title}\n"

            context_parts.append(
                f"\nModule {i}: {title}\n"
                f"Learning Objectives: {', '.join(objectives) if objectives else 'N/A'}\n"
                f"Sections:\n{sections_text}"
            )

        context_text = "\n".join(context_parts)
        if course_metadata:
            context_text += f"\nTarget Audience: {course_metadata.get('targetAudience', 'general')}"
            context_text += f"\nCourse Level: {course_metadata.get('courseLevel', 'beginner')}"
            context_text += f"\nInstitute/Domain: {course_metadata.get('institute', '')}"

        # Response schema matching Chitra's structureSchema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "course_topic": {"type": "STRING"},
                "requested_images": {"type": "INTEGER"},
                "total_images": {"type": "INTEGER"},
                "image_set": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "id": {"type": "INTEGER"},
                            "title": {"type": "STRING"},
                            "source_section_title": {"type": "STRING"},
                            "use_case": {"type": "STRING"},
                            "course_relevance": {"type": "STRING"},
                            "visual_details": {"type": "STRING"},
                            "prompt_used": {"type": "STRING"},
                        },
                        "required": [
                            "id", "title", "source_section_title",
                            "use_case", "course_relevance",
                            "visual_details", "prompt_used",
                        ],
                    },
                },
            },
            "required": ["course_topic", "requested_images", "total_images", "image_set"],
        }

        prompt = (
            f"Plan {requested_count} photorealistic, domain-specific educational images "
            f"for the course below.\n\n"
            f"RULES FOR EACH IMAGE CONCEPT:\n"
            f"1. Reference a SPECIFIC situation, tool, action, or environment described in the module content — "
            f"not a generic representation of the topic.\n"
            f"2. The scene must be immediately recognisable as belonging to the course domain "
            f"(e.g. electrical substation for NERC CIP, operating theatre for medical, construction site for safety).\n"
            f"3. Describe the PRECISE action happening: who is doing what, with which object, in which setting.\n"
            f"4. FORBIDDEN: generic office desks, handshakes, light bulbs, motivational silhouettes, "
            f"stock-photo clichés, vague abstract visuals.\n"
            f"5. REQUIRED: show real domain equipment, uniforms, tools, or environments specific to this course.\n"
            f"6. For 'prompt_used': write a detailed, camera-direction-style description (40–80 words) "
            f"that a photorealistic image model can render directly.\n\n"
            f"Course content:\n\"\"\"\n{context_text}\n\"\"\""
        )

        async def _call():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=ART_DIRECTOR_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            if not response.text:
                raise Exception("Empty response from content analysis.")
            return json.loads(response.text)

        result = await self._with_retry(_call)
        image_set = result.get("image_set", [])
        logger.info(f"Art Director planned {len(image_set)} image concepts for '{course_title}'")
        return image_set

    async def plan_concept_for_module(
        self,
        course_title: str,
        module: Dict[str, Any],
        module_index: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single, context-rich image concept for one module.
        Returns None if planning fails so callers can fall back.
        """
        if not self.available:
            return None
        try:
            concepts = await self.analyze_content_for_images(
                course_title=course_title or "Course",
                modules=[module],
                requested_count=1,
            )
            if not concepts:
                return None
            concept = concepts[0] or {}
            concept.setdefault("id", module_index + 1)
            concept.setdefault("title", module.get("moduleTitle", f"Module {module_index + 1}"))
            return concept
        except Exception as exc:
            logger.warning(f"Image concept planning failed for module {module_index + 1}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Step 2: Generate a single image from a concept
    # ------------------------------------------------------------------
    async def generate_image_for_concept(
        self,
        concept: Dict[str, Any],
        seed: int,
        aspect_ratio: str = "16:9",
        image_model: str = None,
    ) -> bytes:
        """Generate a PNG image for one concept. Returns raw PNG bytes."""
        from google.genai import types
        from config import GEMINI_IMAGE_MODEL

        model_name = image_model or GEMINI_IMAGE_MODEL

        refined_prompt = concept.get("prompt_used") or concept.get("visual_details") or ""

        # Fixed rules block — always included in full (never truncated)
        rules_prefix = (
            "Generate a safe-for-work, photorealistic, physically grounded image.\n"
            "ABSOLUTE RULE — NO READABLE TEXT: Every sign, screen, label, poster, packaging, "
            "clothing print, or document in the scene MUST be rendered with EXTREME Gaussian blur "
            "so that zero letters, digits, or symbols are legible.\n"
            "NO LOGOS OR BRAND MARKS of any kind — blur or remove them entirely.\n"
            "Main subject and action must be visually dominant and unmistakable.\n"
            "Perfect human anatomy — 5 fingers, natural joints, no distortions.\n\n"
            "SCENE DESCRIPTION:\n"
        )
        style_suffix = (
            "\n\nSHOT STYLE: Editorial documentary photography, full-frame camera, "
            "35–50 mm prime lens, shallow depth-of-field, natural ambient light, "
            "candid authentic feel — NOT a stock photo."
        )

        # Truncate only the concept description to fit within 1200-char total
        max_concept_chars = 1200 - len(rules_prefix) - len(style_suffix)
        if len(refined_prompt) > max_concept_chars:
            refined_prompt = refined_prompt[:max_concept_chars]

        final_prompt = rules_prefix + refined_prompt + style_suffix

        async def _call():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                raise Exception("Model returned no response.")

            # Find image part in response
            for part in (candidate.content.parts or []):
                if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                    return part.inline_data.data

            if hasattr(candidate, "finish_reason"):
                reason = str(candidate.finish_reason)
                if "SAFETY" in reason:
                    raise Exception("Safety block occurred.")
                if "OTHER" in reason:
                    raise Exception("Generation failed: OTHER (Possible copyright or safety filter)")

            raise Exception("Generation failed: no image in response")

        image_bytes = await self._with_retry(_call)
        return await self._enforce_text_logo_blur(image_bytes)

    async def _enforce_text_logo_blur(self, image_bytes: bytes) -> bytes:
        """
        Post-process images to aggressively blur any text or logos.
        Falls back to the original image if the edit step fails.
        """
        try:
            return await self.edit_image(
                image_bytes,
                "Scan every surface in this image for readable content and apply EXTREME Gaussian blur:\n"
                "- Screens, monitors, displays: blur entire screen area so no text or UI is readable\n"
                "- Signs, banners, posters, labels: blur all text to 100% illegibility\n"
                "- Documents, papers, books, packaging: blur any printed text completely\n"
                "- Clothing prints, badges, nameplates: blur all text and symbols\n"
                "- Logos, brand marks, emblems, icons: blur or remove entirely\n"
                "Result: zero readable characters, digits, or brand symbols anywhere in the image."
            )
        except Exception as exc:
            logger.warning(f"Text/logo blur pass failed; returning original image: {exc}")
            return image_bytes

    async def edit_image(
        self,
        image_bytes: bytes,
        edit_prompt: str,
        mime_type: str = "image/png",
    ) -> bytes:
        """
        Edit an existing image using a text instruction.
        Mirrors Chitra's handleEditImage() in server/index.js (lines 112-151).
        Model: gemini-3.1-flash-image-preview
        """
        from google.genai import types
        import base64

        if not self.available:
            raise Exception("Image generation unavailable (no API key)")

        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        # Mirror Chitra's ImageEditor.tsx (lines 79-83): append style rules to edit prompt
        # This specifically handles text already present in the source image being edited
        full_edit_prompt = (
            f"{edit_prompt}\n\n"
            "IMPORTANT STYLE RULES:\n"
            "- Identify any text, words, signs, logos, or brand-like symbols in the image and apply a heavy blur "
            "to them so they are completely illegible.\n"
            f"{STRICT_STYLE_SUFFIX}"
        )

        async def _call():
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-3.1-flash-image-preview",
                contents=types.Content(
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=full_edit_prompt),
                    ]
                ),
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                raise Exception("Model returned no response.")

            for part in (candidate.content.parts or []):
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                    return part.inline_data.data

            reason = str(getattr(candidate, "finish_reason", ""))
            if "SAFETY" in reason:
                raise Exception("Safety block occurred.")
            raise Exception(f"Edit failed: {reason or 'no image in response'}")

        return await self._with_retry(_call)

    # ------------------------------------------------------------------
    # Step 3: Orchestrate image generation for a full course
    # ------------------------------------------------------------------
    async def generate_images_for_course(
        self,
        course_title: str,
        modules: List[Dict],
        output_dir: Path,
        course_id: str = "",
        max_concurrent: int = None,
        progress_callback=None,
        user_input: Dict = None,
        is_regen: bool = False,
        stats_uploads_dir: Path = None,
    ) -> Dict[int, str]:
        """
        End-to-end: analyse course → generate 1 image per module → save to disk.

        Returns: { module_index: absolute_image_file_path }
        """
        if not self.available:
            logger.warning("Image generation unavailable (no API key)")
            return {}

        from config import MAX_CONCURRENT_IMAGES

        max_concurrent = max_concurrent or MAX_CONCURRENT_IMAGES
        requested_count = len(modules)

        # Step A: Analyze content
        logger.info(f"Analyzing course content for {requested_count} image concepts...")
        if progress_callback:
            await progress_callback(76, "Analyzing course content for image planning...")

        concepts = await self.analyze_content_for_images(
            course_title, modules, requested_count, user_input
        )

        # Ensure we have enough concepts (pad or trim)
        while len(concepts) < requested_count:
            concepts.append({
                "id": len(concepts) + 1,
                "title": f"Module {len(concepts) + 1} illustration",
                "prompt_used": f"An educational illustration related to {modules[len(concepts)].get('moduleTitle', 'this topic')}",
                "visual_details": "",
            })
        concepts = concepts[:requested_count]

        # Step B: Generate images concurrently
        semaphore = asyncio.Semaphore(max_concurrent)
        session_seed = int(time.time())
        output_dir.mkdir(parents=True, exist_ok=True)

        results: Dict[int, str] = {}

        async def _gen_one(module_idx: int, concept: Dict):
            async with semaphore:
                concept_id = concept.get("id", module_idx + 1)
                varied_seed = session_seed + concept_id

                if progress_callback:
                    await progress_callback(
                        77 + int((module_idx / requested_count) * 6),
                        f"Generating image for Module {module_idx + 1}..."
                    )

                try:
                    image_bytes = await self.generate_image_for_concept(
                        concept, seed=varied_seed
                    )

                    # Save image
                    filename = f"{course_id}_module_{module_idx + 1}_image.png" if course_id else f"module_{module_idx + 1}_image.png"
                    image_path = output_dir / filename

                    await asyncio.to_thread(self._save_image, image_bytes, image_path)

                    results[module_idx] = str(image_path)
                    logger.info(
                        f"Generated image for module {module_idx + 1}: {image_path}"
                    )
                except Exception as exc:
                    logger.warning(
                        f"Image generation failed for module {module_idx + 1}: {exc}"
                    )

        tasks = [
            _gen_one(idx, concept)
            for idx, concept in enumerate(concepts)
        ]
        await asyncio.gather(*tasks)

        logger.info(
            f"Image generation complete: {len(results)}/{requested_count} images generated"
        )

        if stats_uploads_dir and results:
            try:
                record_images(stats_uploads_dir, course_id, course_title, len(results), is_regen)
            except Exception as e:
                logger.warning(f"Failed to record image stats: {e}")

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _save_image(image_bytes: bytes, path: Path):
        """Save image bytes to disk, optionally compressing with Pillow."""
        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_bytes))
            # Ensure RGB (no alpha) and save as optimized PNG
            if img.mode == "RGBA":
                img = img.convert("RGB")
            img.save(str(path), format="PNG", optimize=True)
        except ImportError:
            # Pillow not available, save raw bytes
            path.write_bytes(image_bytes)
