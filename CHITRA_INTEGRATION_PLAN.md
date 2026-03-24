# Chitra Integration Plan: Image Generation in Step 03 (Audio & Media)

## Executive Summary

Chitra is a standalone React + Express image generation app using Gemini's image model.
Kartavya is a FastAPI + Next.js course generation platform. This plan integrates Chitra's
image generation logic **natively into Kartavya's backend pipeline**, so images are
auto-generated alongside audio in Step 03, and `StepAudioMedia.tsx` gets an
"Image Generation" section.

---

## Architecture Overview

```
Current Flow (Step 03):
User → StepAudioMedia.tsx (audio settings only) → backend generates audio only

Target Flow (Step 03):
User → StepAudioMedia.tsx (audio + image settings) → backend generates audio + images
                                                      → images saved to assets/
                                                      → images referenced in course.json
                                                      → xAPI package includes images
```

---

## Phase 1: Backend — Create Image Generation Service

### File to Create: `services/image_generator.py`

Port Chitra's Node.js server logic (`Chitra--main/server/index.js`) to Python using the
`google-generativeai` SDK.

**Class structure:**

```python
class ImageGeneratorService:
    def __init__(self, api_key: str)

    async def analyze_content_for_images(
        self,
        course_title: str,
        modules: List[Dict],      # All module titles + learning objectives
        requested_count: int      # 1 image per module = len(modules)
    ) -> List[ImageConcept]
    # Mirrors: handleAnalyzeContent() in Chitra--main/server/index.js
    # Uses: Gemini text model with Art Director system prompt
    # Returns: List of ImageConcept with title, visual_details, prompt_used

    async def generate_image_for_concept(
        self,
        concept: ImageConcept,
        seed: int,
        aspect_ratio: str = "16:9"
    ) -> bytes  # PNG image bytes
    # Mirrors: handleGenerateImage() in Chitra--main/server/index.js
    # Model: gemini-3-pro-image-preview (or configured via GEMINI_IMAGE_MODEL)
    # Returns: Raw PNG bytes decoded from base64

    async def generate_images_for_course(
        self,
        course_title: str,
        modules: List[Dict],
        output_dir: Path,
        max_concurrent: int = 2   # Matches Chitra's MAX_CONCURRENT_IMAGES = 2
    ) -> Dict[int, str]           # module_index → absolute image file path
    # Orchestrator: calls analyze then generates concurrently
    # Saves as: module_{N}_image.png in output_dir/assets/
```

**Key Chitra details to port exactly:**

| Detail | Source Location | Notes |
|--------|----------------|-------|
| Art Director system prompt | `Chitra--main/server/index.js` handleAnalyzeContent() | Copy verbatim |
| `STRICT_STYLE_SUFFIX` | `Chitra--main/App.tsx` | Append to every image prompt |
| Retry logic | `Chitra--main/server/index.js` — MAX_RETRIES=3, exponential backoff | Port to Python |
| Seed strategy | `Chitra--main/App.tsx` — `sessionSeed + concept.id` | Use `int(time.time()) + module_index` |
| Response schema | `Chitra--main/server/index.js` handleAnalyzeContent() JSON schema | Port to Python dict |
| Concurrency limit | `Chitra--main/App.tsx` — `MAX_CONCURRENT_IMAGES = 2` | Use asyncio.Semaphore(2) |

---

## Phase 2: Backend — Wire Into `course_generator.py`

### File to Modify: `services/course_generator.py`

**1. Import the new service** (top of file):
```python
from services.image_generator import ImageGeneratorService
```

**2. Initialize in `__init__`** alongside `self.google_tts`:
```python
self.image_gen = ImageGeneratorService(api_key=GEMINI_API_KEY)
```

**3. Read user preference** from `user_input` (Step 03 form payload):
```python
include_images = user_input.get("includeImages", False)
```

**4. Add image generation phase** after all modules have content (after audio phase, ~line 933):
```python
if include_images:
    await progress_callback(73, "Generating course images...")

    image_paths = await self.image_gen.generate_images_for_course(
        course_title=course_title,
        modules=modules,
        output_dir=OUTPUT_DIR / "assets",
        max_concurrent=2
    )

    for module_idx, image_path in image_paths.items():
        modules[module_idx]["imagePath"] = str(image_path)
```

**5. Adjust progress percentages:**

| Phase | Current % | New % (with images) |
|-------|-----------|---------------------|
| Audio generation | 70–90% | 70–75% |
| Image generation (new) | — | 75–85% |
| Quiz + Certificate | 85–95% | 85–95% |

**6. Make image failures non-blocking** (same pattern as audio):
```python
try:
    image_paths = await self.image_gen.generate_images_for_course(...)
    for module_idx, image_path in image_paths.items():
        modules[module_idx]["imagePath"] = str(image_path)
except Exception as e:
    logger.warning(f"Image generation failed, continuing without images: {e}")
```

---

## Phase 3: Backend — Optional Standalone Endpoint

### File to Modify: `backend/main.py`

Add `/api/course/generate-images` for on-demand regeneration of module images after a
course already exists (e.g. regenerate a single module's image from the course view page).

```python
@app.post("/api/course/generate-images")
async def generate_images_for_course(request: Request):
    body = await request.json()
    course_id = body.get("courseId")
    module_indices = body.get("moduleIndices", [])  # Which modules to (re)generate for
    # Load course from cache → generate images → save → return updated module data
```

> **This is optional for MVP.** Focus on Phases 1–2 first.

---

## Phase 4: Frontend — Update `StepAudioMedia.tsx`

### File to Modify: `frontend/app/components/wizard/StepAudioMedia.tsx`

Add an "Image Generation" section below the existing audio settings.

**New UI fields:**

```tsx
{/* Image Generation Toggle */}
<label>Images</label>
<select
  value={form.includeImages ? "true" : "false"}
  onChange={e => setForm({ ...form, includeImages: e.target.value === "true" })}
>
  <option value="false">Without images</option>
  <option value="true">With AI-generated images</option>
</select>

{/* When includeImages = true, show info note */}
{form.includeImages && (
  <p className="text-sm text-yellow-600">
    ⚠ Adds ~2–3 minutes to generation. 1 photorealistic image per module (16:9).
  </p>
)}
```

**Visual layout after change:**
```
┌─────────────────────────────────────┐
│  AUDIO SETTINGS                     │
│  [With audio ▼]                     │
│  Voice: [Female ▼]                  │
│  Speed: [━━●──────] 1.0x            │
│  [▶ Preview Voice]                  │
│                                     │
│  IMAGE SETTINGS                     │
│  [With AI-generated images ▼]       │
│  Style: Photorealistic, 16:9        │
│  Count: 1 image per module          │
│  ⚠ Adds ~2–3 min to generation     │
└─────────────────────────────────────┘
```

---

## Phase 5: Frontend — Form State & Payload

### File to Modify: wherever `FormState` type is defined (likely `frontend/app/context/` or `page.tsx`)

**Add field to `FormState`:**
```ts
includeImages: boolean  // default: false
```

**Verify** that `includeImages` is included in the POST body sent to `/api/course/generate`
when the user clicks Generate in Step 04. It should already flow through `user_input` if
`FormState` is serialized correctly.

---

## Phase 6: Frontend — Update `StepConfirm.tsx`

### File to Modify: `frontend/app/components/wizard/StepConfirm.tsx`

**Add images to settings summary:**
```tsx
{form.includeImages && (
  <div>Images: AI-generated (1 per module, photorealistic 16:9)</div>
)}
```

**Update time estimate calculation:**
```ts
// Current: estimate based on modules + audio
// Add: +2-3 minutes if includeImages = true
const extraMinutes = form.includeImages ? 3 : 0
const estimatedMin = baseMin + extraMinutes
const estimatedMax = baseMax + extraMinutes
```

---

## Phase 7: xAPI Package — No Changes Needed

### File: `generators/xapi_generator_merged.py`

**Already handled.** The `_copy_assets()` method already copies `module.imagePath` into
the assets folder, and the HTML already references it. As long as `imagePath` is set on
each module object, the xAPI package will automatically include and display the images.

```python
# This code already exists in _copy_assets():
if module.get('imagePath'):
    src = Path(module['imagePath'])
    dst = assets_dir / src.name
    shutil.copy2(src, dst)
```

**No changes needed to this file.**

---

## Phase 8: Configuration

### File to Modify: `config.py`

Add image model config so it's easy to swap:
```python
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
MAX_CONCURRENT_IMAGES = int(os.getenv("MAX_CONCURRENT_IMAGES", "2"))
```

### File to Check: `requirements.txt`

`google-generativeai` is already a dependency. Verify `Pillow` is present for optional
image compression before saving:
```
Pillow>=10.0.0
```

---

## Implementation Order (Recommended)

| # | Task | File | Priority |
|---|------|------|----------|
| 1 | Create `ImageGeneratorService` class | `services/image_generator.py` (NEW) | Critical |
| 2 | Add `GEMINI_IMAGE_MODEL` to config | `config.py` | Critical |
| 3 | Add `includeImages` to `FormState` | `frontend/app/context/` or `page.tsx` | Critical |
| 4 | Update `StepAudioMedia.tsx` UI | `frontend/app/components/wizard/StepAudioMedia.tsx` | Critical |
| 5 | Wire image gen into `course_generator.py` | `services/course_generator.py` | Critical |
| 6 | Adjust progress percentages | `services/course_generator.py` | Critical |
| 7 | Update `StepConfirm.tsx` summary + time | `frontend/app/components/wizard/StepConfirm.tsx` | Important |
| 8 | Verify `requirements.txt` has Pillow | `requirements.txt` | Important |
| 9 | End-to-end test: generate course with images | — | Critical |
| 10 | Add `/api/course/generate-images` endpoint | `backend/main.py` | Optional |

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Gemini image model rate limits | Use `max_concurrent=2` + exponential backoff (3 retries) — matches Chitra |
| Image generation failure | Non-blocking — course generates without images on failure (same pattern as audio) |
| Slow generation (+2–3 min) | Show accurate time estimate in StepConfirm, show image phase in progress bar |
| Model ID changes / unavailability | Abstract to `GEMINI_IMAGE_MODEL` in `config.py` — easy to swap |
| Large image files bloating ZIP | Use Pillow to compress/resize to max ~1MB before saving |
| `imagePath` not reaching xAPI generator | Already supported in `_copy_assets()` — just ensure it's set on module dict |

---

## End Result

After integration, every generated course (when the user opts in) will have:
- One photorealistic, educationally relevant hero image per module
- Images automatically included in the downloadable xAPI ZIP package
- Images displayed in the course HTML at the top of each module
- No UI changes to the course viewer needed — already supported
