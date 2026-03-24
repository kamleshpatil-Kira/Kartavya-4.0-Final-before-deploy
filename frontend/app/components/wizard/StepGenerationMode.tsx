"use client";

import React, { useState } from "react";
import { InfoTip } from "../InfoTip";
import { apiFetch } from "../../lib/api";

export interface FormState {
    courseTitle: string;
    targetAudience: string;
    institute: string;
    relevantLaws: string;
    tone: string[];
    numModules: number;
    courseLevel: string;
    courseLanguage: string;
    addQuizzes: boolean;
    numQuizQuestions: number;
    difficulty: string;
    generateOutlineOnly: boolean;
    showAiFooter: boolean;
    includeAudio: boolean;
    voiceGender: string;
    speechSpeed: number;
    /** Interactive block types to include — e.g. ["tabs","flipcard"]. Empty = none. */
    interactiveBlocks: string[];
    /** Whether to generate AI images for each module */
    includeImages: boolean;
}

interface Props {
    generationMode: string;
    setGenerationMode: (mode: string) => void;
    isUploadingCourse: boolean;
    isUploadingDirectEdit: boolean;
    courseBlueprint: any;
    handleFileUpload: (file: File) => Promise<void>;
    handleDirectEditUpload: (file: File) => Promise<void>;
    onSelectFromHistory: (courseId: string) => Promise<void>;
    isLoadingHistory?: boolean;
}

export function StepGenerationMode({
    generationMode,
    setGenerationMode,
    isUploadingCourse,
    isUploadingDirectEdit,
    courseBlueprint,
    handleFileUpload,
    handleDirectEditUpload,
    onSelectFromHistory,
    isLoadingHistory = false,
}: Props) {
    const [historyOpen, setHistoryOpen] = useState(false);
    const [historyList, setHistoryList] = useState<any[]>([]);
    const [historyFetched, setHistoryFetched] = useState(false);
    const [historyFetching, setHistoryFetching] = useState(false);
    const [loadingId, setLoadingId] = useState<string | null>(null);

    const toggleHistory = async () => {
        const next = !historyOpen;
        setHistoryOpen(next);
        if (next && !historyFetched) {
            setHistoryFetching(true);
            try {
                const res = await apiFetch<{ history: any[] }>("/api/history");
                setHistoryList(res.history || []);
                setHistoryFetched(true);
            } catch {
                // silently ignore — list stays empty
            } finally {
                setHistoryFetching(false);
            }
        }
    };

    const handleLoad = async (courseId: string) => {
        setLoadingId(courseId);
        await onSelectFromHistory(courseId);
        setLoadingId(null);
        setHistoryOpen(false);
    };

    const regenActive = isUploadingCourse || !!courseBlueprint;
    const editActive = isUploadingDirectEdit;
    const anyActive = regenActive || editActive;

    return (
        <div className="card surface">
            <fieldset className="form-block">
                <h2 className="section-title">Step 1 · Setup</h2>
                <div className="section-card">
                    <h3>Generation Mode</h3>
                    <p className="muted">Choose how you want to build this course.</p>
                    <div className="choice-grid">
                        <button
                            type="button"
                            className={`choice-card${generationMode === "start_from_scratch" ? " active" : ""}`}
                            onClick={() => setGenerationMode("start_from_scratch")}
                        >
                            <div className="choice-title">Start from Scratch</div>
                            <div className="helper">Create a new course from your brief.</div>
                        </button>
                        <button
                            type="button"
                            className={`choice-card${generationMode === "regenerate_from_existing_course" ? " active" : ""}`}
                            onClick={() => setGenerationMode("regenerate_from_existing_course")}
                        >
                            <div className="choice-title">Regenerate Existing</div>
                            <div className="helper">Upload a course file and rebuild it with AI.</div>
                        </button>
                    </div>
                </div>

                {generationMode === "regenerate_from_existing_course" && (
                    <div
                        style={{
                            display: "flex",
                            gap: anyActive ? 0 : 20,
                            transition: "gap 0.4s ease",
                            marginTop: 8,
                        }}
                    >
                        {/* Panel A: Regenerate */}
                        <div
                            className="section-card"
                            style={{
                                flex: editActive ? "0 0 0%" : "1 1 0%",
                                maxWidth: editActive ? 0 : "100%",
                                opacity: editActive ? 0 : 1,
                                overflow: "hidden",
                                transition: "flex 0.45s ease, max-width 0.45s ease, opacity 0.35s ease",
                            }}
                        >
                            <h3 style={{ margin: 0 }}>🔄 Regenerate Course</h3>
                            <p className="muted">Upload a PDF, DOCX, JSON, or ZIP (xAPI, SCORM 1.2). Kartavya will analyse and rebuild the course.</p>

                            <div
                                className="upload-box"
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    const f = e.dataTransfer.files?.[0];
                                    if (f) void handleFileUpload(f);
                                }}
                            >
                                <input
                                    type="file"
                                    accept=".pdf,.docx,.doc,.json,.zip"
                                    disabled={isUploadingCourse || isLoadingHistory}
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) void handleFileUpload(file);
                                    }}
                                />
                                {isUploadingCourse && <span className="muted">
                                    {isLoadingHistory ? "Loading from history..." : "Analysing course file..."}
                                </span>}
                                {courseBlueprint && !isUploadingCourse && (
                                    <span className="muted">✅ Blueprint ready. Fill the form and generate.</span>
                                )}
                            </div>

                            {/* ── or / Select from History ── */}
                            <div style={{ margin: "16px 0 4px", display: "flex", alignItems: "center", gap: 10 }}>
                                <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
                                <span style={{ fontSize: "0.78rem", color: "var(--muted)", fontWeight: 600, whiteSpace: "nowrap" }}>or</span>
                                <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
                            </div>

                            <button
                                type="button"
                                className="secondary"
                                disabled={isUploadingCourse}
                                onClick={() => void toggleHistory()}
                                style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}
                            >
                                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <span>🕐</span>
                                    <span>Select from History</span>
                                </span>
                                <span style={{ fontSize: "0.75rem", transition: "transform 0.2s", display: "inline-block", transform: historyOpen ? "rotate(180deg)" : "rotate(0deg)" }}>▼</span>
                            </button>

                            {historyOpen && (
                                <div style={{
                                    marginTop: 8,
                                    border: "1px solid var(--border)",
                                    borderRadius: 8,
                                    overflow: "hidden",
                                }}>
                                    {historyFetching && (
                                        <div style={{ padding: "12px 16px", color: "var(--muted)", fontSize: "0.85rem" }}>Loading history...</div>
                                    )}
                                    {!historyFetching && historyList.length === 0 && (
                                        <div style={{ padding: "12px 16px", color: "var(--muted)", fontSize: "0.85rem" }}>No course history found.</div>
                                    )}
                                    {historyList.map((course) => (
                                        <div
                                            key={course.id}
                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "space-between",
                                                padding: "10px 14px",
                                                borderBottom: "1px solid var(--border)",
                                                gap: 12,
                                            }}
                                        >
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                <div style={{ fontWeight: 500, fontSize: "0.88rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                    {course.title || "Untitled"}
                                                </div>
                                                <div style={{ fontSize: "0.77rem", color: "var(--muted)", marginTop: 2 }}>
                                                    {course.modules ?? 0} mod · {course.created_at || "—"}
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                className="secondary"
                                                disabled={loadingId !== null}
                                                onClick={() => void handleLoad(course.id)}
                                                style={{ flexShrink: 0, padding: "4px 12px", fontSize: "0.82rem" }}
                                            >
                                                {loadingId === course.id ? "Loading..." : "Load"}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {courseBlueprint && !isUploadingCourse && (
                                <div
                                    style={{
                                        marginTop: 12,
                                        padding: 16,
                                        borderRadius: 10,
                                        background: "rgba(27, 90, 166, 0.06)",
                                        border: "1px solid rgba(27, 90, 166, 0.15)",
                                    }}
                                >
                                    <h4 style={{ margin: "0 0 8px", fontSize: "0.95rem" }}>📋 Course Blueprint</h4>
                                    {(courseBlueprint.detectedTitle || courseBlueprint.blueprint?.courseTitle) && (
                                        <p style={{ margin: "4px 0", fontSize: "0.85rem" }}>
                                            <strong>Title:</strong>{" "}
                                            {courseBlueprint.detectedTitle || courseBlueprint.blueprint?.courseTitle}
                                        </p>
                                    )}
                                    {(courseBlueprint.detectedAudience || courseBlueprint.blueprint?.detectedAudience) && (
                                        <p style={{ margin: "4px 0", fontSize: "0.85rem" }}>
                                            <strong>Audience:</strong>{" "}
                                            {courseBlueprint.detectedAudience || courseBlueprint.blueprint?.detectedAudience}
                                        </p>
                                    )}
                                    {courseBlueprint.fileType && (
                                        <p style={{ margin: "4px 0", fontSize: "0.85rem" }}>
                                            <strong>File Type:</strong>{" "}
                                            {courseBlueprint.fileType === "history" ? "Source: History" : courseBlueprint.fileType.toUpperCase()}
                                        </p>
                                    )}
                                    {(
                                        courseBlueprint.detectedModules ||
                                        courseBlueprint.blueprint?.detectedModules ||
                                        []
                                    ).length > 0 && (
                                            <div style={{ margin: "8px 0" }}>
                                                <strong style={{ fontSize: "0.85rem" }}>
                                                    Detected Modules (
                                                    {(courseBlueprint.detectedModules || courseBlueprint.blueprint?.detectedModules).length}):
                                                </strong>
                                                <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: "0.82rem" }}>
                                                    {(courseBlueprint.detectedModules || courseBlueprint.blueprint?.detectedModules).map(
                                                        (m: any, i: number) => (
                                                            <li key={i}>{m.moduleTitle || m}</li>
                                                        )
                                                    )}
                                                </ul>
                                            </div>
                                        )}
                                    {(courseBlueprint.suggestedImprovements || courseBlueprint.blueprint?.suggestedImprovements) && (
                                        <div
                                            style={{
                                                margin: "8px 0 0",
                                                padding: "8px 12px",
                                                background: "rgba(255,180,0,0.08)",
                                                borderRadius: 6,
                                                fontSize: "0.82rem",
                                            }}
                                        >
                                            <strong>💡 Suggested Improvements:</strong>
                                            <p style={{ margin: "4px 0 0" }}>
                                                {courseBlueprint.suggestedImprovements || courseBlueprint.blueprint?.suggestedImprovements}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* OR divider */}
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                maxWidth: anyActive ? 0 : 40,
                                opacity: anyActive ? 0 : 1,
                                overflow: "hidden",
                                transition: "max-width 0.4s ease, opacity 0.3s ease",
                                fontWeight: 600,
                                color: "var(--muted)",
                                fontSize: "0.8rem",
                            }}
                        >
                            OR
                        </div>

                        {/* Panel B: Direct Edit */}
                        <div
                            className="section-card"
                            style={{
                                flex: regenActive ? "0 0 0%" : "1 1 0%",
                                maxWidth: regenActive ? 0 : "100%",
                                opacity: regenActive ? 0 : 1,
                                overflow: "hidden",
                                transition: "flex 0.45s ease, max-width 0.45s ease, opacity 0.35s ease",
                            }}
                        >
                            <h3 style={{ margin: 0 }}>✏️ Edit Directly</h3>
                            <p className="muted">Upload an xAPI/SCORM ZIP package to jump straight to the inline editor.</p>
                            <div className="upload-box">
                                <input
                                    type="file"
                                    accept=".zip"
                                    disabled={isUploadingDirectEdit}
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) void handleDirectEditUpload(file);
                                    }}
                                />
                                {isUploadingDirectEdit && <span className="muted">Loading course into editor...</span>}
                            </div>
                        </div>
                    </div>
                )}
            </fieldset>
        </div>
    );
}
