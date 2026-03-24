"use client";

import React, { useState, useEffect, useRef } from "react";
import { InfoTip } from "../InfoTip";
import { COURSE_LANGUAGES } from "../../lib/languages";
import { detectDomain, getMismatchWarning, getUnknownTerms, DOMAIN_SUGGESTIONS, DOMAIN_LABELS } from "../../lib/domain-suggestions";
import { suggestGuidelinesByDictionary } from "../../lib/course-catalog";
import type { FormState } from "./StepGenerationMode";

const tones = ["Professional", "Conversational", "Fun", "Academic"];

const INTERACTIVE_BLOCKS = [
    { key: "tabs", label: "🗂 Tabs", hint: "Tabbed content panels" },
    { key: "accordion", label: "📋 Accordion", hint: "Expand/collapse Q&A" },
    { key: "note", label: "💡 Callout", hint: "Info/tip/warning box" },
    { key: "table", label: "📊 Table", hint: "Data comparison table" },
    { key: "flipcard", label: "🃏 Flip Cards", hint: "Term/definition cards" },
];
interface Props {
    form: FormState;
    setForm: React.Dispatch<React.SetStateAction<FormState>>;
    isUploadingDocs: boolean;
    processedDocuments: string | null;
    handleDocumentsUpload: (files: FileList | null) => Promise<void>;
}

export function StepCourseInfo({
    form,
    setForm,
    isUploadingDocs,
    processedDocuments,
    handleDocumentsUpload,
}: Props) {
    const toggleTone = (tone: string) => {
        setForm((prev) => ({
            ...prev,
            tone: prev.tone.includes(tone) ? prev.tone.filter((t) => t !== tone) : [...prev.tone, tone],
        }));
    };

    const toggleInteractiveBlock = (key: string) => {
        setForm((prev) => ({
            ...prev,
            interactiveBlocks: prev.interactiveBlocks.includes(key)
                ? prev.interactiveBlocks.filter((k) => k !== key)
                : [...prev.interactiveBlocks, key],
        }));
    };


    // --- Dictionary-powered guideline suggestions ---
    const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
    const [aiDomain, setAiDomain] = useState<string>("");

    const detectedDomain = detectDomain(form.courseTitle);

    useEffect(() => {
        const title = form.courseTitle.trim();
        const audience = form.targetAudience.trim();

        if (!title || !audience) {
            setAiSuggestions([]);
            setAiDomain("");
            return;
        }

        const dictSuggestions = suggestGuidelinesByDictionary(title, audience);
        setAiSuggestions(dictSuggestions);
        setAiDomain("");
    }, [form.courseTitle, form.targetAudience]);

    // Show AI suggestions; no hardcoded fallback to avoid stale-domain flash
    const suggestions = aiSuggestions;
    const suggestionLabel = aiDomain || (detectedDomain ? DOMAIN_LABELS[detectedDomain] : "");

    // Validation (still client-side, unchanged)
    const mismatchWarning = detectedDomain ? getMismatchWarning(detectedDomain, form.relevantLaws) : null;
    const unknownTerms = getUnknownTerms(form.relevantLaws);

    const handleSuggestionClick = (suggestion: string) => {
        const currentTerms = form.relevantLaws.split(",").map((s) => s.trim()).filter(Boolean);
        if (!currentTerms.includes(suggestion)) {
            const newTerms = currentTerms.length > 0 ? `${currentTerms.join(", ")}, ${suggestion}` : suggestion;
            setForm({ ...form, relevantLaws: newTerms });
        }
    };

    const hasWarning = !!mismatchWarning || unknownTerms.length > 0;

    return (
        <div className="card surface">
            <fieldset className="form-block">
                <h2 className="section-title">Step 2 · Course Details</h2>
                <div className="grid">
                    {/* Left column: Course Profile */}
                    <div className="section-card">
                        <h3>Course Profile</h3>
                        <div className="field">
                            <label>
                                Course Title *
                                <InfoTip text="Short, client-facing name for the course." />
                            </label>
                            <input
                                value={form.courseTitle}
                                onChange={(e) => setForm({ ...form, courseTitle: e.target.value })}
                            />
                        </div>
                        <div className="field">
                            <label>
                                Target Audience *
                                <InfoTip text="Who is the learner? Be specific (role, level)." />
                            </label>
                            <input
                                value={form.targetAudience}
                                onChange={(e) => setForm({ ...form, targetAudience: e.target.value })}
                            />
                        </div>
                        {/* <div className="field">
                            <label>Institute / Organization</label>
                            <input
                                value={form.institute}
                                onChange={(e) => setForm({ ...form, institute: e.target.value })}
                            />
                        </div> */}
                    </div>

                    {/* Right column: Compliance & Sources */}
                    <div className="section-card">
                        <h3>Compliance &amp; Sources</h3>
                        <div className="field">
                            <label>
                                Relevant Laws / Guidelines *
                                <InfoTip text="Comma-separated standards or policies to align content." />
                            </label>
                            <input
                                value={form.relevantLaws}
                                onChange={(e) => setForm({ ...form, relevantLaws: e.target.value })}
                                style={hasWarning ? { borderColor: "#eab308", borderWidth: "2px" } : undefined}
                                disabled={!form.courseTitle.trim() || !form.targetAudience.trim()}
                                placeholder={(!form.courseTitle.trim() || !form.targetAudience.trim()) ? "Enter Course Title & Target Audience to unlock" : "Enter guidelines e.g., OSHA, HIPAA"}
                            />
                            {mismatchWarning && (
                                <p style={{ color: "#ca8a04", fontSize: "0.85rem", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                                    ⚠️ {mismatchWarning}
                                </p>
                            )}
                            {unknownTerms.length > 0 && (
                                <p style={{ color: "#ca8a04", fontSize: "0.85rem", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                                    ⚠️ Unrecognized: <strong>{unknownTerms.join(", ")}</strong> — this doesn&apos;t match any known standard. Check spelling or select from suggestions below.
                                </p>
                            )}
                            {suggestions.length > 0 && (
                                <div style={{ marginTop: 8 }}>
                                    <span className="muted" style={{ fontSize: "0.8rem", display: "block", marginBottom: 6 }}>
                                        {`Suggested${suggestionLabel ? ` for ${suggestionLabel}` : ""}:`}
                                    </span>
                                    <div className="chip-group" style={{ flexWrap: "wrap", gap: 6 }}>
                                        {suggestions.map((s) => (
                                            <button
                                                key={s}
                                                type="button"
                                                className="chip"
                                                onClick={() => handleSuggestionClick(s)}
                                                style={{ fontSize: "0.75rem", padding: "4px 8px", minHeight: "auto" }}
                                            >
                                                + {s}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="field">
                            <label>Upload Supporting Documents</label>
                            <div className="upload-box">
                                <input
                                    type="file"
                                    multiple
                                    accept=".pdf,.doc,.docx,.txt,.csv"
                                    disabled={isUploadingDocs}
                                    onChange={(e) => void handleDocumentsUpload(e.target.files)}
                                />
                                {processedDocuments && <span className="muted">Documents processed.</span>}
                                {isUploadingDocs && <span className="muted">Processing documents...</span>}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tone & Structure */}
                <div className="section-card">
                    <h3>Tone &amp; Structure</h3>
                    <div className="field">
                        <label>
                            Tone *
                            <InfoTip text="Choose the voice and attitude of the content." />
                        </label>
                        <div className="chip-group">
                            {tones.map((tone) => (
                                <button
                                    key={tone}
                                    type="button"
                                    className={`chip${form.tone.includes(tone) ? " active" : ""}`}
                                    onClick={() => toggleTone(tone)}
                                >
                                    {tone}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="grid">
                        <div className="field">
                            <label>
                                Number of Modules *
                                <InfoTip text="Controls the length and structure of the course." />
                            </label>
                            <input
                                type="number"
                                min={1}
                                max={20}
                                value={form.numModules}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setForm({ ...form, numModules: val === "" ? ("" as unknown as number) : parseInt(val, 10) });
                                }}
                                onBlur={() => {
                                    if (form.numModules.toString() === "" || form.numModules < 1) {
                                        setForm({ ...form, numModules: 1 });
                                    } else if (form.numModules > 20) {
                                        setForm({ ...form, numModules: 20 });
                                    }
                                }}
                            />
                            {(form.numModules.toString() === "" || form.numModules < 1 || form.numModules > 20) && (
                                <p style={{ color: "red", fontSize: "0.8rem", marginTop: 4 }}>
                                    Number of modules must be between 1 and 20.
                                </p>
                            )}
                        </div>
                        <div className="field">
                            <label>
                                Difficulty Level *
                                <InfoTip text="Learner experience level: beginner to advanced." />
                            </label>
                            <select
                                value={form.courseLevel}
                                onChange={(e) => setForm({ ...form, courseLevel: e.target.value })}
                            >
                                <option value="Beginner">Beginner</option>
                                <option value="Intermediate">Intermediate</option>
                                <option value="Advanced">Advanced</option>
                            </select>
                        </div>
                        <div className="field">
                            <label>
                                Course Language *
                                <InfoTip text="Sets language for content and TTS accent." />
                            </label>
                            <select
                                value={form.courseLanguage}
                                onChange={(e) => setForm({ ...form, courseLanguage: e.target.value })}
                            >
                                <option value="">Select language…</option>
                                {COURSE_LANGUAGES.map((lang) => (
                                    <option key={lang} value={lang}>{lang}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Learning Aids + Generation Scope */}
                <div className="grid">
                    <div
                        className="section-card"
                        style={form.generateOutlineOnly ? { opacity: 0.45, pointerEvents: "none" } : undefined}
                    >
                        <h3>Learning Aids</h3>
                        {form.generateOutlineOnly && (
                            <p className="muted" style={{ fontStyle: "italic", marginBottom: 12 }}>
                                Not applicable for outline-only generation.
                            </p>
                        )}
                        <div className="field">
                            <label>
                                Final Quiz
                                <InfoTip text="Adds a summative quiz to assess learning." />
                            </label>
                            <div className="toggle-group">
                                <button
                                    type="button"
                                    className={`toggle-button${form.addQuizzes ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, addQuizzes: true })}
                                >On</button>
                                <button
                                    type="button"
                                    className={`toggle-button${!form.addQuizzes ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, addQuizzes: false })}
                                >Off</button>
                            </div>
                        </div>
                        {form.addQuizzes && (
                            <>
                                <div className="field">
                                    <label>
                                        Quiz Questions
                                        <InfoTip text="Total questions in the final quiz." />
                                    </label>
                                    <input
                                        type="number"
                                        min={5}
                                        max={50}
                                        value={form.numQuizQuestions}
                                        onChange={(e) => setForm({ ...form, numQuizQuestions: Number(e.target.value) })}
                                    />
                                </div>
                                <div className="field">
                                    <label>
                                        Quiz Difficulty
                                        <InfoTip text="Controls complexity of quiz questions." />
                                    </label>
                                    <select
                                        value={form.difficulty}
                                        onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                                    >
                                        <option value="Easy">Easy</option>
                                        <option value="Medium">Medium</option>
                                        <option value="Hard">Hard</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Interactive Blocks */}
                        <div className="field" style={{ marginTop: 8 }}>
                            <label>
                                Interactive Blocks
                                <InfoTip text="Adds Rise-like interactive elements. One per module, automatically shuffled so no two consecutive modules share the same type." />
                            </label>
                            <div className="chip-group" style={{ flexWrap: "wrap", gap: 8 }}>
                                {INTERACTIVE_BLOCKS.map((block) => (
                                    <button
                                        key={block.key}
                                        type="button"
                                        title={block.hint}
                                        className={`chip${form.interactiveBlocks.includes(block.key) ? " active" : ""}`}
                                        onClick={() => toggleInteractiveBlock(block.key)}
                                    >
                                        {block.label}
                                    </button>
                                ))}
                            </div>
                            {form.interactiveBlocks.length > 0 && (
                                <p className="muted" style={{ marginTop: 6, fontSize: "0.8rem" }}>
                                    Selected: {form.interactiveBlocks.length} type{form.interactiveBlocks.length > 1 ? "s" : ""} — 1 per module, no consecutive repeats.
                                </p>
                            )}
                        </div>
                    </div>

                    <div className="section-card">
                        <h3>Generation Scope</h3>
                        <div className="field">
                            <label>
                                Generate Outline Only
                                <InfoTip text="Create outline without full content generation." />
                            </label>
                            <div className="toggle-group">
                                <button
                                    type="button"
                                    className={`toggle-button${form.generateOutlineOnly ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, generateOutlineOnly: true })}
                                >Yes</button>
                                <button
                                    type="button"
                                    className={`toggle-button${!form.generateOutlineOnly ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, generateOutlineOnly: false })}
                                >No</button>
                            </div>
                        </div>
                        <div className="field">
                            <label>
                                Show AI Disclaimer Footer
                                <InfoTip text="Adds a disclosure footer to the final course." />
                            </label>
                            <div className="toggle-group">
                                <button
                                    type="button"
                                    className={`toggle-button${form.showAiFooter ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, showAiFooter: true })}
                                >Yes</button>
                                <button
                                    type="button"
                                    className={`toggle-button${!form.showAiFooter ? " active" : ""}`}
                                    onClick={() => setForm({ ...form, showAiFooter: false })}
                                >No</button>
                            </div>
                        </div>
                    </div>
                </div>
            </fieldset>
        </div>
    );
}
