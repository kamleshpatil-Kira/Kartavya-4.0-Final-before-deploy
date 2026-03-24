"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useCourse } from "./context/CourseContext";
import { apiFetch, apiFetchBlob, apiUrl, readApiErrorMessage } from "./lib/api";
import { getVoicePreviewText, toTtsAccent } from "./lib/languages";
import { StepGenerationMode } from "./components/wizard/StepGenerationMode";
import type { FormState } from "./components/wizard/StepGenerationMode";
import { StepCourseInfo } from "./components/wizard/StepCourseInfo";
import { StepAudioMedia } from "./components/wizard/StepAudioMedia";
import { StepConfirm } from "./components/wizard/StepConfirm";

export default function CourseGenerationPage() {
  const {
    courseData,
    courseId,
    setCourseData,
    setCourseId,
    jobState,
    setJobState,
    setAutoRedirect,
    startNewCourse,
  } = useCourse();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [generationMode, setGenerationMode] = useState("start_from_scratch");
  const [existingCourseData, setExistingCourseData] = useState<any>(null);
  const [processedDocuments, setProcessedDocuments] = useState<string | null>(null);

  const [form, setForm] = useState<FormState>({
    courseTitle: "",
    targetAudience: "",
    institute: "",
    relevantLaws: "",
    tone: [] as string[],
    numModules: 4,
    courseLevel: "Intermediate",
    courseLanguage: "English",
    addQuizzes: false,
    numQuizQuestions: 10,

    difficulty: "Medium",
    generateOutlineOnly: false,
    showAiFooter: true,
    includeAudio: false,
    voiceGender: "Male",
    speechSpeed: 1.0,
    interactiveBlocks: [],
    includeImages: false,
  });

  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isUploadingCourse, setIsUploadingCourse] = useState(false);
  const [isUploadingDirectEdit, setIsUploadingDirectEdit] = useState(false);
  const [courseBlueprint, setCourseBlueprint] = useState<any>(null);
  const [isUploadingDocs, setIsUploadingDocs] = useState(false);
  const [isPreviewingAudio, setIsPreviewingAudio] = useState(false);
  const [uiNotice, setUiNotice] = useState<{
    type: "error" | "success" | "info";
    text: string;
  } | null>(null);
  const [previewAudioUrl, setPreviewAudioUrl] = useState<string | null>(null);

  const steps = ["Generation Mode", "Course Information", "Audio & Media", "Review & Confirm"];

  const estimate = useMemo(() => {
    const modules = Math.max(1, form.numModules || 1);
    const basePerModule = form.generateOutlineOnly ? 0.5 : 1.1;
    const audioPerModule = form.includeAudio ? 0.7 : 0;
    const quizMinutes = form.addQuizzes
      ? Math.max(0.5, form.numQuizQuestions * 0.08)
      : 0;
    const docBoost = processedDocuments ? 0.6 : 0;
    const modeBoost = generationMode !== "start_from_scratch" ? 0.4 : 0;
    const imageMinutes = form.includeImages ? 3 : 0;
    const total =
      modules * (basePerModule + audioPerModule) +
      quizMinutes +
      docBoost +
      modeBoost +
      imageMinutes;
    const min = Math.max(1, Math.round(total * 0.8));
    const max = Math.max(min + 1, Math.round(total * 1.3));
    return { min, max };
  }, [
    form.numModules,
    form.generateOutlineOnly,
    form.includeAudio,
    form.addQuizzes,
    form.numQuizQuestions,
    form.includeImages,
    generationMode,
    processedDocuments,
  ]);

  const handleHistorySelect = async (courseId: string) => {
    setIsLoadingHistory(true);
    setIsUploadingCourse(true);
    setUiNotice(null);
    setCourseBlueprint(null);
    try {
      const res = await apiFetch<any>(`/api/course/${courseId}`);
      const c = res.course || {};
      // All original user-facing fields (audience, laws, tone, etc.) are stored
      // under metadata.user_input — the course object itself only has title + display fields.
      const ui = res.metadata?.user_input || {};
      const modules: any[] = Array.isArray(res.modules) ? res.modules : [];

      // Transform API response into the same blueprint shape as file upload
      const blueprint = {
        detectedTitle: c.title || ui.courseTitle || "",
        detectedAudience: ui.targetAudience || c.target_audience || "",
        detectedModules: modules.map((m: any) => ({ moduleTitle: m.moduleTitle || m.title || "" })),
        fileType: "history",
      };
      setCourseBlueprint(blueprint);
      setExistingCourseData(res);

      // Pre-fill form fields — prefer metadata.user_input as ground truth
      const title = c.title || ui.courseTitle || "";
      const audience = ui.targetAudience || c.target_audience || "";
      const institute = ui.institute || c.institute || "";
      const laws = ui.relevantLaws || (
        Array.isArray(c.relevant_laws)
          ? c.relevant_laws.join(", ")
          : (c.relevant_laws || "")
      );
      const toneRaw: string = ui.tone || c.tone || "";
      const toneArr = toneRaw ? toneRaw.split(",").map((t: string) => t.trim()).filter(Boolean) : [];
      const moduleCount = modules.length || ui.numModules || c.num_modules || 4;
      const level = ui.courseLevel || c.course_level || "Intermediate";
      const lang = ui.courseLanguage || c.courseLanguage || "English";
      const hasQuiz = ui.addQuizzes ?? !!(res.quiz);
      const quizCount = ui.numQuizQuestions || (Array.isArray(res.quiz?.questions) ? res.quiz.questions.length : 10);

      setForm((prev) => ({
        ...prev,
        courseTitle: title || prev.courseTitle,
        targetAudience: audience || prev.targetAudience,
        institute: institute || prev.institute,
        relevantLaws: laws || prev.relevantLaws,
        tone: toneArr.length ? toneArr : prev.tone,
        numModules: moduleCount || prev.numModules,
        courseLevel: level || prev.courseLevel,
        courseLanguage: lang || prev.courseLanguage,
        addQuizzes: hasQuiz,
        numQuizQuestions: quizCount,
        includeAudio: ui.includeAudio ?? !!(res.has_audio),
        includeImages: ui.includeImages ?? !!(res.has_images),
      }));

      setGenerationMode("regenerate_from_existing_course");
      setUiNotice({ type: "success", text: `Loaded "${c.title || "course"}" from history — settings pre-filled.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to load course from history." });
    } finally {
      setIsLoadingHistory(false);
      setIsUploadingCourse(false);
    }
  };

  const isStepValid = () => {
    if (step === 1) return generationMode !== "";
    if (step === 2) {
      return (
        form.courseTitle.trim() &&
        form.targetAudience.trim() &&
        form.relevantLaws.trim() &&
        form.tone.length > 0 &&
        form.courseLanguage
      );
    }
    return true;
  };

  const isGenerating =
    jobState.status === "queued" || jobState.status === "running";
  const progressValue = Math.max(0, Math.min(100, Number(jobState.progress) || 0));
  const visibleProgress = isGenerating ? Math.max(progressValue, 6) : progressValue;
  const statusMessage =
    jobState.message || (isGenerating ? "Preparing generation..." : "Status");

  const generationPhases = ["Queued", "Outline", "Modules", "Quiz & Packaging", "Finalizing"];
  const generationPhaseIndex = useMemo(() => {
    const msg = (jobState.message || "").toLowerCase();
    if (jobState.status === "completed") return generationPhases.length - 1;
    if (jobState.status === "queued") return 0;
    if (msg.includes("final") || progressValue >= 90) return 4;
    if (
      msg.includes("quiz") ||
      msg.includes("packag") ||
      msg.includes("xapi") ||
      msg.includes("validat") ||
      progressValue >= 70
    )
      return 3;
    if (
      msg.includes("module") ||
      msg.includes("knowledge") ||
      msg.includes("audio") ||
      progressValue >= 30
    )
      return 2;
    if (msg.includes("outline") || progressValue >= 10) return 1;
    return 0;
  }, [jobState.message, jobState.status, progressValue]);

  const handleFileUpload = async (file: File) => {
    setIsUploadingCourse(true);
    setUiNotice(null);
    setCourseBlueprint(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(apiUrl("/api/course/upload-existing"), {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(await readApiErrorMessage(response));
      const data = await response.json();
      setCourseBlueprint(data);
      const bp = data.blueprint || data;
      const title = data.detectedTitle || bp.courseTitle || "";
      const audience = data.detectedAudience || bp.detectedAudience || "";
      const tone = bp.detectedTone || "";
      const laws = (data.complianceRefs || bp.complianceRefs || []).join(", ");
      const moduleCount = data.estimatedModuleCount || bp.estimatedModuleCount || 0;
      if (title) setForm((f) => ({ ...f, courseTitle: title }));
      if (audience) setForm((f) => ({ ...f, targetAudience: audience }));
      if (tone) setForm((f) => ({ ...f, tone: [tone] }));
      if (laws) setForm((f) => ({ ...f, relevantLaws: laws }));
      if (moduleCount > 0) setForm((f) => ({ ...f, numModules: moduleCount }));
      setExistingCourseData(data);
      const filled = [title, audience, tone, laws].filter(Boolean).length;
      setUiNotice({
        type: "success",
        text: `Course analysed — ${filled} field${filled !== 1 ? "s" : ""} auto-filled. Review blueprint below and generate.`,
      });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to analyse course file." });
    } finally {
      setIsUploadingCourse(false);
    }
  };

  const handleDirectEditUpload = async (file: File) => {
    setIsUploadingDirectEdit(true);
    setUiNotice(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(apiUrl("/api/course/load"), {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(await readApiErrorMessage(response));
      const data = await response.json();
      const resolvedId = data.course_id || data.course_data?.course?.id || null;
      setCourseData(data.course_data);
      setCourseId(resolvedId);
      router.push("/view");
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to load course for editing." });
    } finally {
      setIsUploadingDirectEdit(false);
    }
  };

  const handleDocumentsUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploadingDocs(true);
    setUiNotice(null);
    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append("files", file));
      const response = await fetch(apiUrl("/api/documents/process"), {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error(await readApiErrorMessage(response));
      const data = await response.json();
      setProcessedDocuments(data.processedDocuments);
      const meta = data.metadata || {};

      // Auto-fill form fields from extracted metadata
      if (meta.courseTitle) setForm((f) => ({ ...f, courseTitle: meta.courseTitle }));
      if (meta.targetAudience) setForm((f) => ({ ...f, targetAudience: meta.targetAudience }));
      if (meta.institute) setForm((f) => ({ ...f, institute: meta.institute }));
      if (meta.relevantLaws) setForm((f) => ({ ...f, relevantLaws: meta.relevantLaws }));

      // Auto-fill course language from detected document language
      const detectedLang = data.detectedLanguage || meta.detectedLanguage || "";
      if (detectedLang) {
        // Match detected language to our supported COURSE_LANGUAGES list (case-insensitive)
        const matchedLang = detectedLang.charAt(0).toUpperCase() + detectedLang.slice(1).toLowerCase();
        setForm((f) => ({ ...f, courseLanguage: matchedLang }));
      }

      const filledFields = [meta.courseTitle, meta.targetAudience, meta.institute, meta.relevantLaws].filter(Boolean).length;
      const wordCount = data.wordCount ? ` · ${data.wordCount.toLocaleString()} words` : "";
      const langNote = detectedLang ? ` · Language: ${detectedLang}` : "";
      const ocrNote = data.isVisionOCR ? " (via Vision OCR)" : "";
      const fileCount = (data.files || []).length;

      setUiNotice({
        type: "success",
        text: filledFields > 0
          ? `${fileCount} document${fileCount !== 1 ? "s" : ""} processed${ocrNote} — ${filledFields} field${filledFields > 1 ? "s" : ""} auto-filled${wordCount}${langNote}`
          : `Document${fileCount !== 1 ? "s" : ""} processed${ocrNote}${wordCount}${langNote} — no metadata could be extracted.`,
      });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to process uploaded documents." });
    } finally {
      setIsUploadingDocs(false);
    }
  };

  const generateCourse = async () => {
    if (isGenerating) return;
    if (generationMode !== "start_from_scratch" && !existingCourseData) {
      setUiNotice({ type: "error", text: "Please upload an existing course file for regenerate/edit modes." });
      return;
    }
    setUiNotice(null);
    setJobState({ id: null, status: "queued", progress: 0, message: "Queued", error: null });
    setAutoRedirect(true);

    const accent = toTtsAccent(form.courseLanguage);
    const userInput = {
      courseTitle: form.courseTitle,
      targetAudience: form.targetAudience,
      institute: form.institute,
      relevantLaws: form.relevantLaws,
      tone: form.tone.join(", "),
      numModules: form.numModules,
      courseLevel: form.courseLevel,
      courseLanguage: form.courseLanguage,
      generationType: generationMode,
      audioOptions: { accent, gender: form.voiceGender.toLowerCase(), speed: form.speechSpeed },
      includeAudio: form.includeAudio,
      addQuizzes: form.addQuizzes,
      numQuizQuestions: form.addQuizzes ? form.numQuizQuestions : 0,
      difficulty: form.difficulty,
      interactiveBlocks: form.interactiveBlocks,
      includeImages: form.includeImages,
      generateOutlineOnly: form.generateOutlineOnly,
      showAiFooter: form.showAiFooter,
      processedDocuments,
      existingCourseData,
      existingCourseBlueprint: courseBlueprint?.blueprint || courseBlueprint || null,
      userId: "web_user",
    };

    try {
      const res = await apiFetch<{ job_id: string }>("/api/course/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userInput),
      });
      setJobState({ id: res.job_id, status: "queued", progress: 0, message: "Queued", error: null });
      setUiNotice({ type: "info", text: "Generation started. You can keep browsing while processing runs." });
    } catch (err: any) {
      setJobState({ id: null, status: "failed", progress: 0, message: "Failed", error: err?.message || "Failed to start generation" });
      setAutoRedirect(false);
      setUiNotice({ type: "error", text: err?.message || "Failed to start generation." });
    }
  };

  const stopGeneration = async () => {
    if (!jobState.id) return;
    // Fix A4: confirm before cancelling — generation can't be recovered
    if (!window.confirm("Stop generation? The current job will be permanently cancelled and cannot be resumed.")) return;
    try {
      await apiFetch(`/api/jobs/${jobState.id}/cancel`, { method: "POST" });
      setJobState((prev) => ({ ...prev, status: "cancelled", message: "Cancelled", error: null }));
      setAutoRedirect(false);
      setUiNotice({ type: "info", text: "Generation cancelled." });
    } catch (err: any) {
      setJobState((prev) => ({ ...prev, error: err?.message || "Failed to cancel job" }));
      setUiNotice({ type: "error", text: err?.message || "Failed to cancel generation." });
    }
  };

  const previewAudio = async () => {
    setIsPreviewingAudio(true);
    setPreviewAudioUrl(null);
    setUiNotice(null);
    try {
      const accent = toTtsAccent(form.courseLanguage);
      const blob = await apiFetchBlob("/api/audio/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: getVoicePreviewText(form.courseLanguage),
          language: form.courseLanguage,
          accent,
          gender: form.voiceGender.toLowerCase(),
          speed: form.speechSpeed,
        }),
      });
      // Fix A2: revoke previous blob URL before creating a new one to prevent memory leak
      setPreviewAudioUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
      setUiNotice({ type: "success", text: "Voice preview generated." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to generate voice preview." });
    } finally {
      setIsPreviewingAudio(false);
    }
  };

  return (
    <div>
      {/* Always show error notices; suppress info/success during generation (Fix A1) */}
      {uiNotice && (uiNotice.type === "error" || !isGenerating) && (
        <div className={`notice ${uiNotice.type}`} role={uiNotice.type === "error" ? "alert" : "status"}>
          {uiNotice.text}
        </div>
      )}

      {/* Generation progress card */}
      {isGenerating && (
        <div className="card surface" aria-busy="true" style={{ padding: "32px 40px" }}>
          <div>
            <div className="muted" style={{ fontSize: "0.85rem", marginBottom: "8px" }}>
              Live job update
            </div>
            <div style={{ fontWeight: 600, fontSize: "1.1rem", marginBottom: "32px", color: "var(--accent)" }}>
              {statusMessage}
            </div>
          </div>

          <div className="gen-timeline" role="status" aria-live="polite"
            style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 0, margin: "16px 0 24px" }}>
            {generationPhases.map((phase, index) => {
              const state =
                index < generationPhaseIndex ? "done" : index === generationPhaseIndex ? "active" : "pending";
              const isLast = index === generationPhases.length - 1;
              const align = index === 0 ? "flex-start" : isLast ? "flex-end" : "center";
              const textJustify = index === 0 ? "left" : isLast ? "right" : "center";
              return (
                <React.Fragment key={phase}>
                  <div className="gen-timeline-step"
                    style={{ display: "flex", flexDirection: "column", flex: "0 0 auto", width: index === 0 || isLast ? "auto" : "80px" }}>
                    <div style={{ width: "100%", display: "flex", justifyContent: align }}>
                      <div className={`gen-step-circle ${state}`}>
                        {state === "done" ? "✓" : index + 1}
                      </div>
                    </div>
                    <div className={`gen-step-label ${state}`}
                      style={{ marginTop: "10px", textAlign: textJustify, width: "100%" }}>
                      {phase}
                    </div>
                  </div>
                  {!isLast && (
                    <div style={{
                      flex: 1, height: "2px",
                      background: index < generationPhaseIndex ? "var(--accent)" : "var(--border)",
                      marginTop: "15px", marginLeft: "8px", marginRight: "8px",
                      transition: "background 0.3s ease",
                    }} />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {(jobState.id || jobState.status) && (
            <div style={{ marginTop: "24px" }}>
              <div className="progress-track"
                style={{ height: "6px", background: "var(--border)", borderRadius: "999px", overflow: "hidden" }}>
                <div
                  className={`progress-bar${isGenerating ? " indeterminate" : ""}`}
                  style={{ width: `${visibleProgress}%`, height: "100%", transition: "width 0.3s ease" }}
                />
              </div>
              <div className="inline" style={{ marginTop: 10, justifyContent: "space-between" }}>
                <div>
                  <span className="badge">Progress {progressValue}%</span>
                  {jobState.status && (
                    <span className="pill" style={{ marginLeft: "8px" }}>Status: {jobState.status}</span>
                  )}
                </div>
                <div className="estimate">
                  Estimated time: ~{estimate.min}-{estimate.max} min
                </div>
              </div>
              {jobState.error && <p style={{ color: "#b91c1c", marginTop: "8px" }}>{jobState.error}</p>}
            </div>
          )}

          <div className="inline" style={{ marginTop: "20px", justifyContent: "space-between", alignItems: "center" }}>
            <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
              You can keep browsing — generation runs in the background.
            </p>
            <button type="button" className="secondary" onClick={() => void stopGeneration()}>
              Stop Generation
            </button>
          </div>
        </div>
      )}

      {/* Stepper indicator */}
      {!isGenerating && (
        <div className="card surface">
          <div className="stepper">
            {steps.map((label, idx) => {
              const active = idx + 1 === step;
              return (
                <div key={label} className={`step${active ? " active" : ""}`}>
                  <span className="badge">0{idx + 1}</span>
                  <span>{label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Wizard steps — each is its own component */}
      {!isGenerating && step === 1 && (
        <StepGenerationMode
          generationMode={generationMode}
          setGenerationMode={setGenerationMode}
          isUploadingCourse={isUploadingCourse}
          isUploadingDirectEdit={isUploadingDirectEdit}
          courseBlueprint={courseBlueprint}
          handleFileUpload={handleFileUpload}
          handleDirectEditUpload={handleDirectEditUpload}
          onSelectFromHistory={handleHistorySelect}
          isLoadingHistory={isLoadingHistory}
        />
      )}

      {!isGenerating && step === 2 && (
        <StepCourseInfo
          form={form}
          setForm={setForm}
          isUploadingDocs={isUploadingDocs}
          processedDocuments={processedDocuments}
          handleDocumentsUpload={handleDocumentsUpload}
        />
      )}

      {!isGenerating && step === 3 && (
        <StepAudioMedia
          form={form}
          setForm={setForm}
          isPreviewingAudio={isPreviewingAudio}
          previewAudioUrl={previewAudioUrl}
          previewAudio={previewAudio}
        />
      )}

      {!isGenerating && step === 4 && (
        <StepConfirm form={form} estimate={estimate} />
      )}

      {/* Navigation buttons */}
      {!isGenerating && (
        <div className="card surface wizard-actions">
          <div className="inline">
            <button
              type="button"
              className="secondary"
              disabled={step === 1 || isUploadingCourse || isUploadingDocs || isPreviewingAudio}
              onClick={() => setStep((s) => Math.max(1, s - 1))}
            >
              Previous
            </button>
            {step < 4 && (
              <button
                type="button"
                disabled={!isStepValid() || isUploadingCourse || isUploadingDocs || isPreviewingAudio}
                onClick={() => setStep((s) => Math.min(4, s + 1))}
              >
                Next
              </button>
            )}
            {step === 4 && (
              <button
                type="button"
                disabled={isGenerating || isUploadingCourse || isUploadingDocs || isPreviewingAudio}
                onClick={() => void generateCourse()}
              >
                {isGenerating ? "Generating..." : "Generate Course"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Outline-only completion card */}
      {jobState.status === "completed" &&
        courseData &&
        courseData.outline &&
        (!courseData.modules || courseData.modules.length === 0) &&
        !isGenerating && (
          <div className="card surface">
            <h2 className="section-title">✅ Outline Generated</h2>
            <p className="muted">
              Your course outline has been created successfully. View and edit it on the Course Preview page.
            </p>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              To generate full content with modules, audio, and downloads, turn off "Generate Outline Only" and start a new generation.
            </p>
            <div className="inline" style={{ marginTop: 12 }}>
              <button type="button" onClick={() => router.push("/view")}>View Outline</button>
              <button type="button" className="secondary" onClick={() => startNewCourse()}>Start New Course</button>
            </div>
          </div>
        )}

      {/* Full course completion downloads */}
      {jobState.status === "completed" &&
        courseData &&
        courseId &&
        Array.isArray(courseData.modules) &&
        courseData.modules.length > 0 &&
        !isGenerating && (
          <div className="card">
            <h2 className="section-title">Downloads</h2>
            <p className="muted">Ready exports for: {courseData.course?.title || "Latest course"}</p>
            <div className="inline">
              <button type="button" onClick={() => window.open(apiUrl(`/api/course/${courseId}/download/xapi`), "_blank")}>
                Download xAPI ZIP
              </button>
              <button type="button" className="secondary" onClick={() => window.open(apiUrl(`/api/course/${courseId}/download/json`), "_blank")}>
                Download JSON
              </button>
              <button type="button" className="secondary" onClick={() => window.open(apiUrl(`/api/course/${courseId}/download/pdf`), "_blank")}>
                Download PDF
              </button>
            </div>
          </div>
        )}
    </div>
  );
}
