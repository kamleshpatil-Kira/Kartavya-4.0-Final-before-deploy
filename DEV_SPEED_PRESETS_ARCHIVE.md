# 🗃️ Feature Archive: Generation Speed Presets

This file contains the code and styling logic for the **Generation Speed** presets UI (Fast, Balanced, Full) that was removed from the Step 1 (Setup) wizard in Kartavya 3.0.

If you ever want to reintroduce this feature to give users immediate bulk-toggles for course generation settings, copy-paste the logic below back into the app.

## 1. State & Logic (React / Next.js)
Drop this into your page component (e.g., `page.tsx`).

### State Variable
```tsx
const [preset, setPreset] = useState<"fast" | "balanced" | "full">("fast");
```

### Apply Logic
This function updates the `preset` state, but more importantly, it bulk-updates the `form` configuration state based on which speed tier the user selects.

```tsx
const applyPreset = (nextPreset: "fast" | "balanced" | "full") => {
  setPreset(nextPreset);
  setForm((prev) => {
    if (nextPreset === "fast") {
      return {
        ...prev,
        includeAudio: false,
        addFlashcards: false,
        addQuizzes: false,
        generateOutlineOnly: false,
      };
    }
    if (nextPreset === "balanced") {
      return {
        ...prev,
        includeAudio: true,
        addFlashcards: true,
        numFlashcards: Math.max(10, prev.numFlashcards),
        addQuizzes: false,
        generateOutlineOnly: false,
      };
    }
    return {
      ...prev,
      includeAudio: true,
      addFlashcards: true,
      numFlashcards: Math.max(10, prev.numFlashcards),
      addQuizzes: true,
      numQuizQuestions: Math.max(10, prev.numQuizQuestions),
      generateOutlineOnly: false,
    };
  });
};
```

## 2. UI Component (JSX)
Place this block inside the Step 1 view in the wizard.

```tsx
<div className="section-card">
  <h3>Generation Speed</h3>
  <p className="muted">Speed presets help control time and cost.</p>
  <div className="choice-grid">
    <button
      type="button"
      className={`choice-card${preset === "fast" ? " active" : ""}`}
      onClick={() => applyPreset("fast")}
    >
      <div className="choice-title">Fast</div>
      <div className="helper">No audio, no flashcards, no quiz.</div>
    </button>
    <button
      type="button"
      className={`choice-card${preset === "balanced" ? " active" : ""}`}
      onClick={() => applyPreset("balanced")}
    >
      <div className="choice-title">Balanced</div>
      <div className="helper">Audio + flashcards, no quiz.</div>
    </button>
    <button
      type="button"
      className={`choice-card${preset === "full" ? " active" : ""}`}
      onClick={() => applyPreset("full")}
    >
      <div className="choice-title">Full</div>
      <div className="helper">Audio + flashcards + quiz.</div>
    </button>
  </div>
</div>
```

## 3. CSS Classes
No custom CSS needs to be restored! All the classes used in this component (`section-card`, `choice-grid`, `choice-card`, `choice-title`, `helper`) are part of the core Kartavya 3.0 Claymorphism design system in `globals.css` and are safely shared across other components (like the generation logic cards).
