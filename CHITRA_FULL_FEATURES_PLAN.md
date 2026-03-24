# Chitra Full Features Integration Plan
## Regenerate · Edit · Batch Regenerate · Preview

---

## Architecture Decision

**Use Kartavya's existing FastAPI backend — do NOT run Chitra's Node.js server.**

Reasons:
- `image_generator.py` already has all the generation logic
- `load_course_json` / `save_course_json` already exist in `main.py`
- `/api/media/{filename}` already serves images from `output/assets/`
- Adding 3 endpoints to `main.py` is 80 lines total — no new services, no CORS, no second process

---

## Complete Feature Map

| Feature | Chitra Source | Kartavya Target | Status |
|---|---|---|---|
| Generate image during course creation | `handleGenerate()` | `course_generator.py` + Step 03 | ✅ Done |
| **Regenerate single module image** | `handleRegenerate()` | New endpoint + button in view | ❌ To build |
| **Batch regenerate selected images** | `handleRegenerateSelected()` | New endpoint + checkboxes in view | ❌ To build |
| **Edit image with text prompt** | `handleEditImage()` via `gemini-3.1-flash-image-preview` | New endpoint + inline edit UI | ❌ To build |
| Full-size image preview | `ImagePreviewModal` | Click-to-enlarge in view | ❌ To build |

---

## Files to Change

| File | Type of Change |
|---|---|
| `services/image_generator.py` | Add `edit_image()` method |
| `backend/main.py` | Add 3 new API endpoints |
| `frontend/app/view/page.tsx` | Add image controls UI per module card |

No new files needed.

---

## Part 1 — Backend: `services/image_generator.py`

### Add `edit_image()` method

Add this method to the `ImageGeneratorService` class after `generate_image_for_concept()`.

Uses `gemini-3.1-flash-image-preview` (Chitra's edit model — different from the generation model).

```python
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
        "- Identify any text, words, or signs in the image and apply a heavy blur "
        "to them so they are completely illegible.\n"
        f"{STRICT_STYLE_SUFFIX}"
    )

    async def _call():
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model="gemini-3.1-flash-image-preview",
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(data=b64_data, mime_type=mime_type)
                    ),
                    types.Part(text=full_edit_prompt),
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
```

**Why separate from `generate_image_for_concept`:**
- Uses a different Gemini model (`gemini-3.1-flash-image-preview` vs `gemini-3-pro-image-preview`)
- Takes image bytes as input instead of a text concept dict
- No seed, no aspect ratio config — it's inpainting/editing

---

## Part 2 — Backend: `backend/main.py`

Add these 3 endpoints. Place them after the existing `/api/media/{filename}` endpoint (after line 1155).

### Endpoint 1: Regenerate Single Module Image

```python
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

    # Build a concept from the module's existing data
    concept = {
        "id": module_index + 1,
        "title": module_title,
        "prompt_used": (
            module.get("imageConcept", {}).get("prompt_used")
            or f"An educational illustration about: {module_title}"
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

    return {"filename": filename, "imagePath": str(image_path)}
```

**Request:**
```json
POST /api/course/course-1773140543/image/regenerate
{ "moduleIndex": 0 }
```

**Response:**
```json
{ "filename": "course-1773140543_module_1_image.png", "imagePath": "/abs/path/..." }
```

---

### Endpoint 2: Batch Regenerate Selected Modules

```python
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
    semaphore = asyncio.Semaphore(2)
    results = {}

    async def regen_one(module_index: int):
        async with semaphore:
            if module_index >= len(modules):
                results[str(module_index)] = {"error": "Module not found"}
                return

            module = modules[module_index]
            module_title = module.get("moduleTitle", f"Module {module_index + 1}")
            concept = {
                "id": module_index + 1,
                "title": module_title,
                "prompt_used": (
                    module.get("imageConcept", {}).get("prompt_used")
                    or f"An educational illustration about: {module_title}"
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

    return {"results": results}
```

**Request:**
```json
POST /api/course/course-1773140543/image/regenerate-batch
{ "moduleIndices": [0, 2, 3] }
```

**Response:**
```json
{
  "results": {
    "0": { "filename": "course-1773140543_module_1_image.png" },
    "2": { "filename": "course-1773140543_module_3_image.png" },
    "3": { "error": "Safety block occurred." }
  }
}
```

---

### Endpoint 3: Edit Image with Prompt

```python
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

    # Overwrite the same file (or save with _edited suffix — see note below)
    filename = f"{course_id}_module_{module_index + 1}_image.png"
    image_path = OUTPUT_DIR / "assets" / filename
    ImageGeneratorService._save_image(edited_bytes, image_path)

    modules[module_index]["imagePath"] = str(image_path)
    save_course_json(course_data)

    return {"filename": filename, "imagePath": str(image_path)}
```

**Request:**
```json
POST /api/course/course-1773140543/image/edit
{ "moduleIndex": 0, "editPrompt": "Change the background to an outdoor park setting" }
```

**Response:**
```json
{ "filename": "course-1773140543_module_1_image.png", "imagePath": "/abs/path/..." }
```

### Add instance to `main.py` top-level (after existing service instances)

Find where `xAPIGenerator_instance` is created in `main.py` and add next to it:

```python
from services.image_generator import ImageGeneratorService
from config import GEMINI_API_KEY

image_gen_instance = ImageGeneratorService(api_key=GEMINI_API_KEY)
```

> **Note:** `ImageGeneratorService` is already imported in `course_generator.py` but you need a
> top-level instance in `main.py` for the new endpoints to use directly.

---

## Part 3 — Frontend: `frontend/app/view/page.tsx`

### Step A — Add state variables (near top of component, with existing `useState` hooks)

```tsx
// Image feature state
const [imageRegen, setImageRegen] = useState<Record<number, boolean>>({});   // moduleNum → loading
const [imageEdit, setImageEdit] = useState<Record<number, boolean>>({});     // moduleNum → edit panel open
const [imageEditPrompt, setImageEditPrompt] = useState<Record<number, string>>({}); // moduleNum → prompt text
const [imageEditBusy, setImageEditBusy] = useState<Record<number, boolean>>({});    // moduleNum → editing
const [selectedModules, setSelectedModules] = useState<Set<number>>(new Set());     // for batch regen
const [batchRegenBusy, setBatchRegenBusy] = useState(false);
const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null); // full-size preview
```

---

### Step B — Add helper functions (after existing `regenerateModule` function)

```tsx
// Regenerate a single module's image
async function regenerateModuleImage(moduleNum: number, moduleIndex: number) {
  setImageRegen(prev => ({ ...prev, [moduleNum]: true }));
  try {
    const res = await apiFetch(`/api/course/${effectiveCourseId}/image/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ moduleIndex }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Regeneration failed");

    // Bust browser image cache by appending timestamp
    const ts = Date.now();
    setCourseData((prev: any) => {
      if (!prev) return prev;
      const mods = [...prev.modules];
      mods[moduleIndex] = { ...mods[moduleIndex], imagePath: data.imagePath, _imgTs: ts };
      return { ...prev, modules: mods };
    });
  } catch (e: any) {
    alert(`Image regeneration failed: ${e.message}`);
  } finally {
    setImageRegen(prev => ({ ...prev, [moduleNum]: false }));
  }
}

// Edit a module's image with a text prompt
async function editModuleImage(moduleNum: number, moduleIndex: number) {
  const prompt = imageEditPrompt[moduleNum]?.trim();
  if (!prompt) return;

  setImageEditBusy(prev => ({ ...prev, [moduleNum]: true }));
  try {
    const res = await apiFetch(`/api/course/${effectiveCourseId}/image/edit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ moduleIndex, editPrompt: prompt }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Edit failed");

    const ts = Date.now();
    setCourseData((prev: any) => {
      if (!prev) return prev;
      const mods = [...prev.modules];
      mods[moduleIndex] = { ...mods[moduleIndex], imagePath: data.imagePath, _imgTs: ts };
      return { ...prev, modules: mods };
    });
    // Close edit panel and clear prompt on success
    setImageEdit(prev => ({ ...prev, [moduleNum]: false }));
    setImageEditPrompt(prev => ({ ...prev, [moduleNum]: "" }));
  } catch (e: any) {
    alert(`Image edit failed: ${e.message}`);
  } finally {
    setImageEditBusy(prev => ({ ...prev, [moduleNum]: false }));
  }
}

// Toggle module selection for batch regen
function toggleModuleSelection(moduleNum: number) {
  setSelectedModules(prev => {
    const next = new Set(prev);
    if (next.has(moduleNum)) next.delete(moduleNum);
    else next.add(moduleNum);
    return next;
  });
}

// Batch regenerate selected modules
async function batchRegenerateImages() {
  if (selectedModules.size === 0) return;
  setBatchRegenBusy(true);

  // Convert moduleNum (1-based) to moduleIndex (0-based)
  const moduleIndices = Array.from(selectedModules).map(n => n - 1);

  try {
    const res = await apiFetch(`/api/course/${effectiveCourseId}/image/regenerate-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ moduleIndices }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Batch regen failed");

    // Update imagePaths for successful modules
    const ts = Date.now();
    setCourseData((prev: any) => {
      if (!prev) return prev;
      const mods = [...prev.modules];
      Object.entries(data.results).forEach(([idxStr, result]: any) => {
        const idx = parseInt(idxStr);
        if (result.filename && !result.error) {
          mods[idx] = { ...mods[idx], _imgTs: ts };
        }
      });
      return { ...prev, modules: mods };
    });
    setSelectedModules(new Set());
  } catch (e: any) {
    alert(`Batch regeneration failed: ${e.message}`);
  } finally {
    setBatchRegenBusy(false);
  }
}
```

---

### Step C — Add batch regen floating bar

Place this **above** the `{modules.map(...)}` loop (after the Collapse All button area):

```tsx
{selectedModules.size > 0 && (
  <div style={{
    position: "sticky", top: 8, zIndex: 20,
    background: "var(--accent, #1b5aa6)", color: "#fff",
    borderRadius: 10, padding: "10px 20px",
    display: "flex", alignItems: "center", justifyContent: "space-between",
    boxShadow: "0 4px 16px rgba(27,90,166,0.25)", marginBottom: 16,
  }}>
    <span style={{ fontWeight: 600 }}>
      {selectedModules.size} module{selectedModules.size > 1 ? "s" : ""} selected
    </span>
    <div style={{ display: "flex", gap: 8 }}>
      <button
        type="button"
        disabled={batchRegenBusy}
        onClick={() => void batchRegenerateImages()}
        style={{ background: "#fff", color: "var(--accent)", fontWeight: 600,
                 border: "none", borderRadius: 6, padding: "6px 16px", cursor: "pointer" }}
      >
        {batchRegenBusy ? "Regenerating..." : `Regenerate ${selectedModules.size} Images`}
      </button>
      <button
        type="button"
        onClick={() => setSelectedModules(new Set())}
        style={{ background: "rgba(255,255,255,0.15)", color: "#fff", fontWeight: 600,
                 border: "none", borderRadius: 6, padding: "6px 12px", cursor: "pointer" }}
      >
        Clear
      </button>
    </div>
  </div>
)}
```

---

### Step D — Replace the image section in each module card

Find the existing image block in the module card (currently around line 1167):

```tsx
{imageUrl && (
  <div>
    <h4>Module Image</h4>
    <img src={imageUrl} alt={`Module ${moduleNum}`} style={{ maxWidth: 320 }} />
  </div>
)}
```

Replace it with this full image controls block:

```tsx
{/* ── Module Image Section ── */}
<div style={{ marginTop: 16 }}>
  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
    <h4 style={{ margin: 0 }}>Module Image</h4>

    {/* Select for batch regen */}
    <label style={{ display: "flex", alignItems: "center", gap: 4,
                    fontSize: "0.8rem", cursor: "pointer", color: "var(--muted)" }}>
      <input
        type="checkbox"
        checked={selectedModules.has(moduleNum)}
        onChange={() => toggleModuleSelection(moduleNum)}
      />
      Select
    </label>
  </div>

  {imageUrl ? (
    <>
      {/* Image with click-to-preview */}
      <img
        src={`${imageUrl}${module._imgTs ? `?t=${module._imgTs}` : ""}`}
        alt={`Module ${moduleNum}`}
        style={{ maxWidth: 320, borderRadius: 8, cursor: "zoom-in", display: "block" }}
        onClick={() => setPreviewImageUrl(
          `${imageUrl}${module._imgTs ? `?t=${module._imgTs}` : ""}`
        )}
        title="Click to preview full size"
      />

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          className="secondary"
          disabled={imageRegen[moduleNum] || hasActiveRequest}
          onClick={() => void regenerateModuleImage(moduleNum, index)}
          style={{ fontSize: "0.8rem", padding: "5px 12px" }}
        >
          {imageRegen[moduleNum] ? "Regenerating..." : "🔄 Regenerate"}
        </button>

        <button
          type="button"
          className="secondary"
          disabled={imageEditBusy[moduleNum] || hasActiveRequest}
          onClick={() => setImageEdit(prev => ({ ...prev, [moduleNum]: !prev[moduleNum] }))}
          style={{ fontSize: "0.8rem", padding: "5px 12px" }}
        >
          ✏️ Edit Image
        </button>
      </div>

      {/* Inline edit panel (shown when ✏️ Edit Image is clicked) */}
      {imageEdit[moduleNum] && (
        <div style={{ marginTop: 10, padding: "12px", background: "var(--surface, #f8fafc)",
                      border: "1px solid var(--border, #e2e8f0)", borderRadius: 8 }}>
          <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: 6 }}>
            Describe the changes to make:
          </div>
          <textarea
            rows={2}
            placeholder="e.g. Change the background to an outdoor park setting"
            value={imageEditPrompt[moduleNum] || ""}
            onChange={e => setImageEditPrompt(prev => ({ ...prev, [moduleNum]: e.target.value }))}
            style={{ width: "100%", padding: "8px", borderRadius: 6, fontSize: "0.85rem",
                     border: "1px solid var(--border, #e2e8f0)", resize: "vertical",
                     fontFamily: "inherit", boxSizing: "border-box" }}
          />
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button
              type="button"
              disabled={imageEditBusy[moduleNum] || !imageEditPrompt[moduleNum]?.trim()}
              onClick={() => void editModuleImage(moduleNum, index)}
              style={{ fontSize: "0.8rem", padding: "5px 14px" }}
            >
              {imageEditBusy[moduleNum] ? "Applying..." : "Apply Edit"}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => setImageEdit(prev => ({ ...prev, [moduleNum]: false }))}
              style={{ fontSize: "0.8rem", padding: "5px 12px" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  ) : (
    /* No image yet — show a generate button */
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>No image generated</span>
      <button
        type="button"
        className="secondary"
        disabled={imageRegen[moduleNum] || hasActiveRequest}
        onClick={() => void regenerateModuleImage(moduleNum, index)}
        style={{ fontSize: "0.8rem", padding: "5px 12px" }}
      >
        {imageRegen[moduleNum] ? "Generating..." : "✨ Generate Image"}
      </button>
    </div>
  )}
</div>
```

---

### Step E — Add full-size image preview modal

Add this **at the bottom of the JSX return**, just before the closing `</div>` of the page:

```tsx
{/* Full-size image preview modal */}
{previewImageUrl && (
  <div
    style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0,0,0,0.85)",
      display: "flex", alignItems: "center", justifyContent: "center",
      cursor: "zoom-out",
    }}
    onClick={() => setPreviewImageUrl(null)}
  >
    <img
      src={previewImageUrl}
      alt="Full size preview"
      style={{ maxWidth: "90vw", maxHeight: "90vh", borderRadius: 12,
               boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}
      onClick={e => e.stopPropagation()}
    />
    <button
      onClick={() => setPreviewImageUrl(null)}
      style={{ position: "absolute", top: 20, right: 24,
               background: "rgba(255,255,255,0.15)", color: "#fff",
               border: "none", borderRadius: "50%", width: 36, height: 36,
               fontSize: "1.1rem", cursor: "pointer", fontWeight: 700 }}
    >
      ✕
    </button>
  </div>
)}
```

---

## Implementation Order

| # | Task | File | Effort |
|---|---|---|---|
| 1 | Add `edit_image()` method | `services/image_generator.py` | ~25 lines |
| 2 | Add `image_gen_instance` at top level | `backend/main.py` | 3 lines |
| 3 | Add `/image/regenerate` endpoint | `backend/main.py` | ~35 lines |
| 4 | Add `/image/regenerate-batch` endpoint | `backend/main.py` | ~45 lines |
| 5 | Add `/image/edit` endpoint | `backend/main.py` | ~35 lines |
| 6 | Add 7 state variables | `frontend/app/view/page.tsx` | 7 lines |
| 7 | Add 4 helper functions | `frontend/app/view/page.tsx` | ~80 lines |
| 8 | Add batch regen sticky bar | `frontend/app/view/page.tsx` | ~25 lines |
| 9 | Replace image section in module card | `frontend/app/view/page.tsx` | ~75 lines |
| 10 | Add full-size preview modal | `frontend/app/view/page.tsx` | ~20 lines |

**Total: ~350 lines across 3 files.**

---

## Final UI Layout (Per Module Card)

```
┌─────────────────────────────────────────────────┐
│  Module Image                    [☐ Select]     │
│                                                 │
│  ┌──────────────────────┐                       │
│  │                      │  ← click = full       │
│  │   [image 320px]      │    size preview       │
│  │                      │                       │
│  └──────────────────────┘                       │
│                                                 │
│  [🔄 Regenerate]  [✏️ Edit Image]               │
│                                                 │
│  (when ✏️ clicked:)                             │
│  ┌─────────────────────────────────────────┐   │
│  │ Describe the changes to make:           │   │
│  │ [________________________________]      │   │
│  │ [Apply Edit]  [Cancel]                  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘

(when modules are selected, sticky bar appears at top:)
┌─────────────────────────────────────────────────┐
│  3 modules selected                             │
│  [Regenerate 3 Images]  [Clear]                 │
└─────────────────────────────────────────────────┘
```

---

## Edge Cases to Handle

| Case | Handling |
|---|---|
| Edit called but no existing image | Endpoint returns 404 with message "Generate one first" → frontend shows "✨ Generate Image" button |
| Gemini safety block during edit | `edit_image()` raises exception → endpoint returns 500 → frontend shows `alert()` |
| Batch regen: some succeed, some fail | `regenerate-batch` returns per-index results → frontend only updates successful ones |
| Browser caches old image after regen | `?t={timestamp}` appended to `img src` on update busts the cache |
| Concurrent edits on same module | Buttons are disabled while `imageEditBusy[moduleNum]` or `imageRegen[moduleNum]` is true |
| Module has no `imagePath` (images disabled during generation) | Show "✨ Generate Image" button instead of Regenerate/Edit |
