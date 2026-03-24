"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";

function fileNameFromPath(pathStr: string | null | undefined): string | null {
    if (!pathStr) return null;
    const parts = pathStr.split(/[\\/]/);
    return parts[parts.length - 1];
}

interface ModuleCardProps {
    module: any;
    index: number;
    hasActiveRequest: boolean;
    moduleActionBusy: number | null;
    apiUrl: (path: string) => string;
    regenerateModule: (moduleNum: number) => Promise<void>;
    saveModuleData: (moduleNum: number, moduleIdx: number, updatedCache: any) => Promise<void>;
}

export function ModuleCard({
    module,
    index,
    hasActiveRequest,
    moduleActionBusy,
    apiUrl,
    regenerateModule,
    saveModuleData,
}: ModuleCardProps) {
    const moduleNum = module.moduleNumber || index + 1;
    const [collapsed, setCollapsed] = useState(true);
    const [editing, setEditing] = useState(false);

    // Local cache for editing this specific module
    const [cache, setCache] = useState<any>({});

    const toggleCollapse = () => setCollapsed(!collapsed);

    const toggleEdit = () => {
        const isEditing = !editing;
        setEditing(isEditing);
        if (isEditing) {
            // Initialize cache when opening edit mode
            setCache({
                title: module.moduleTitle,
                content: formatModuleContent(module.content).trim(),
                knowledgeCheck: module.knowledgeCheck
                    ? JSON.parse(JSON.stringify(module.knowledgeCheck))
                    : {
                        question: "",
                        options: { A: "", B: "", C: "", D: "" },
                        correctAnswer: "A",
                        feedback: { correct: "", incorrect: "" },
                    },
                flashcards: module.flashcards ? JSON.parse(JSON.stringify(module.flashcards)) : [],
            });
        }
    };

    const handleSave = async () => {
        await saveModuleData(moduleNum, index, cache);
        setEditing(false);
    };

    // Helper function ported from page.tsx specifically for prepping module content
    function formatModuleContent(content: any): string {
        if (!content) return "";
        if (typeof content === "string") return content;

        const formatted: string[] = [];
        if (content.sections) {
            for (const section of content.sections) {
                if (section.sectionTitle) formatted.push(`### ${section.sectionTitle}`);
                if (section.content) formatted.push(section.content);
                if (section.concepts) {
                    for (const concept of section.concepts) {
                        if (concept.conceptTitle) formatted.push(`#### ${concept.conceptTitle}`);
                        if (concept.explanation) formatted.push(concept.explanation);
                        if (concept.scenario) {
                            if (concept.scenario.description) formatted.push(`**Scenario:** ${concept.scenario.description}`);
                            if (concept.scenario.whatToDo) formatted.push(`**What to do:** ${concept.scenario.whatToDo}`);
                            if (concept.scenario.whyItMatters) formatted.push(`**Why it matters:** ${concept.scenario.whyItMatters}`);
                        }
                    }
                }
                if (section.subsections) {
                    for (const sub of section.subsections) {
                        if (sub.subsectionTitle) formatted.push(`#### ${sub.subsectionTitle}`);
                        if (sub.subsectionContent) formatted.push(sub.subsectionContent);
                    }
                }
            }
        }

        if (content.learningObjectives) {
            formatted.push("**Learning Objectives:**");
            for (const obj of content.learningObjectives) formatted.push(`- ${obj}`);
        }
        if (content.keyPoints) {
            formatted.push("**Key Points:**");
            for (const point of content.keyPoints) formatted.push(`- ${point}`);
        }
        if (content.summary) {
            formatted.push("**Module Summary:**");
            formatted.push(content.summary);
        }
        return formatted.join("\n\n");
    }

    return (
        <div className="module-card">
            <div className="module-accent-strip" />
            <div
                className="module-header"
                onClick={toggleCollapse}
                aria-expanded={!collapsed}
            >
                <span className="module-num-badge">{String(moduleNum).padStart(2, "0")}</span>
                <span className="module-title-text">
                    {editing ? cache.title || module.moduleTitle : module.moduleTitle}
                </span>
                <div className="inline" style={{ gap: 8 }} onClick={(e) => e.stopPropagation()}>
                    <button
                        type="button"
                        className="secondary"
                        disabled={hasActiveRequest}
                        onClick={() => {
                            void regenerateModule(moduleNum);
                        }}
                        style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                    >
                        {moduleActionBusy === moduleNum ? "Regenerating..." : "Regenerate"}
                    </button>
                    <button
                        type="button"
                        className="secondary"
                        disabled={hasActiveRequest}
                        onClick={toggleEdit}
                        style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                    >
                        {editing ? "Cancel" : "Edit"}
                    </button>
                    {editing && (
                        <span
                            style={{
                                fontSize: "0.82rem",
                                background: "rgba(27,90,166,0.1)",
                                color: "var(--accent)",
                                padding: "4px 10px",
                                borderRadius: "100px",
                                fontWeight: 600,
                            }}
                        >
                            💡 Press Enter to save
                        </span>
                    )}
                </div>
                <ChevronDown
                    size={18}
                    className={`module-collapse-icon${collapsed ? "" : " open"}`}
                />
            </div>

            {!collapsed && (
                <div className="module-body">
                    {editing ? (
                        <>
                            <div className="field">
                                <label>Module Title</label>
                                <input
                                    value={cache.title || ""}
                                    onChange={(e) => setCache({ ...cache, title: e.target.value })}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            void handleSave();
                                        }
                                    }}
                                />
                            </div>
                            <div className="field">
                                <label>Module Content (Text/Markdown)</label>
                                <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                                    Edit the module content as readable text. Formatting like **bold** and *italics* will be preserved.
                                </p>
                                <textarea
                                    rows={16}
                                    style={{ fontFamily: "monospace", fontSize: "0.95rem", lineHeight: 1.5 }}
                                    value={cache.content || ""}
                                    onChange={(e) => setCache({ ...cache, content: e.target.value })}
                                />
                            </div>

                            {/* Knowledge Check */}
                            <div
                                className="field"
                                style={{
                                    border: "1px solid var(--border)",
                                    padding: "16px",
                                    borderRadius: "8px",
                                    marginTop: "16px",
                                }}
                            >
                                <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "block" }}>
                                    Knowledge Check
                                </label>
                                <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 12 }}>
                                    Each module has one multiple-choice question to verify understanding.
                                </p>
                                <div className="field" style={{ marginBottom: "16px" }}>
                                    <label>Question</label>
                                    <input
                                        value={cache.knowledgeCheck?.question || ""}
                                        onChange={(e) =>
                                            setCache({
                                                ...cache,
                                                knowledgeCheck: { ...cache.knowledgeCheck, question: e.target.value },
                                            })
                                        }
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") void handleSave();
                                        }}
                                    />
                                </div>
                                <div className="responsive-two-col" style={{ marginBottom: "16px" }}>
                                    {["A", "B", "C", "D"].map((opt) => (
                                        <div className="field" key={opt} style={{ margin: 0 }}>
                                            <label>Option {opt}</label>
                                            <input
                                                value={cache.knowledgeCheck?.options?.[opt] || ""}
                                                onChange={(e) =>
                                                    setCache({
                                                        ...cache,
                                                        knowledgeCheck: {
                                                            ...cache.knowledgeCheck,
                                                            options: { ...cache.knowledgeCheck?.options, [opt]: e.target.value },
                                                        },
                                                    })
                                                }
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") void handleSave();
                                                }}
                                            />
                                        </div>
                                    ))}
                                </div>
                                <div className="field" style={{ marginBottom: "16px" }}>
                                    <label>Correct Answer</label>
                                    <select
                                        value={cache.knowledgeCheck?.correctAnswer || "A"}
                                        onChange={(e) =>
                                            setCache({
                                                ...cache,
                                                knowledgeCheck: { ...cache.knowledgeCheck, correctAnswer: e.target.value },
                                            })
                                        }
                                        style={{
                                            padding: "8px",
                                            borderRadius: "4px",
                                            border: "1px solid var(--border)",
                                            background: "var(--background)",
                                            color: "var(--foreground)",
                                            width: "100%",
                                            maxWidth: "200px",
                                            display: "block",
                                        }}
                                    >
                                        <option value="A">Option A</option>
                                        <option value="B">Option B</option>
                                        <option value="C">Option C</option>
                                        <option value="D">Option D</option>
                                    </select>
                                </div>
                                <div className="responsive-two-col">
                                    <div className="field" style={{ margin: 0 }}>
                                        <label>Feedback (If Correct)</label>
                                        <input
                                            value={cache.knowledgeCheck?.feedback?.correct || ""}
                                            onChange={(e) =>
                                                setCache({
                                                    ...cache,
                                                    knowledgeCheck: {
                                                        ...cache.knowledgeCheck,
                                                        feedback: { ...cache.knowledgeCheck?.feedback, correct: e.target.value },
                                                    },
                                                })
                                            }
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") void handleSave();
                                            }}
                                        />
                                    </div>
                                    <div className="field" style={{ margin: 0 }}>
                                        <label>Feedback (If Incorrect)</label>
                                        <input
                                            value={cache.knowledgeCheck?.feedback?.incorrect || ""}
                                            onChange={(e) =>
                                                setCache({
                                                    ...cache,
                                                    knowledgeCheck: {
                                                        ...cache.knowledgeCheck,
                                                        feedback: { ...cache.knowledgeCheck?.feedback, incorrect: e.target.value },
                                                    },
                                                })
                                            }
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") void handleSave();
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Flashcards */}
                            <div
                                className="field"
                                style={{
                                    border: "1px solid var(--border)",
                                    padding: "16px",
                                    borderRadius: "8px",
                                    marginTop: "16px",
                                    marginBottom: "24px",
                                }}
                            >
                                <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "block" }}>
                                    Interactive
                                </label>
                                <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 16 }}>
                                    Key terms and definitions for this module.
                                </p>
                                {(cache.flashcards || []).map((fc: any, fcIndex: number) => (
                                    <div
                                        key={fc.id || fcIndex}
                                        className="responsive-flow-grid"
                                        style={{
                                            marginBottom: "16px",
                                            alignItems: "flex-start",
                                            paddingBottom: "16px",
                                            borderBottom:
                                                fcIndex < cache.flashcards.length - 1 ? "1px dashed var(--border)" : "none",
                                        }}
                                    >
                                        <div className="field" style={{ flex: 1, margin: 0 }}>
                                            <label>Front Context</label>
                                            <input
                                                value={fc.front || ""}
                                                onChange={(e) => {
                                                    const newFc = [...(cache.flashcards || [])];
                                                    newFc[fcIndex] = { ...newFc[fcIndex], front: e.target.value };
                                                    setCache({ ...cache, flashcards: newFc });
                                                }}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") void handleSave();
                                                }}
                                            />
                                        </div>
                                        <div className="field" style={{ flex: 1, margin: 0 }}>
                                            <label>Back Truth</label>
                                            <input
                                                value={fc.back || ""}
                                                onChange={(e) => {
                                                    const newFc = [...(cache.flashcards || [])];
                                                    newFc[fcIndex] = { ...newFc[fcIndex], back: e.target.value };
                                                    setCache({ ...cache, flashcards: newFc });
                                                }}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") void handleSave();
                                                }}
                                            />
                                        </div>
                                        <button
                                            type="button"
                                            className="secondary"
                                            style={{ marginTop: "24px", whiteSpace: "nowrap" }}
                                            disabled={hasActiveRequest}
                                            onClick={() => {
                                                const newFc = [...(cache.flashcards || [])];
                                                newFc.splice(fcIndex, 1);
                                                setCache({ ...cache, flashcards: newFc });
                                            }}
                                        >
                                            Remove
                                        </button>
                                    </div>
                                ))}
                                <button
                                    type="button"
                                    className="secondary"
                                    disabled={hasActiveRequest}
                                    onClick={() => {
                                        const newFc = [...(cache.flashcards || [])];
                                        newFc.push({ id: Date.now(), front: "", back: "" });
                                        setCache({ ...cache, flashcards: newFc });
                                    }}
                                >
                                    + Add Interactive
                                </button>
                            </div>
                            <button
                                type="button"
                                disabled={hasActiveRequest}
                                onClick={() => {
                                    void handleSave();
                                }}
                            >
                                Save Module
                            </button>
                        </>
                    ) : (
                        // Read-Only View
                        <>
                            <h3>{module.moduleTitle}</h3>
                            <p><strong>Estimated Time:</strong> {module.estimatedTime || "N/A"}</p>
                            {module.content && (
                                <div>
                                    <h4>Content</h4>
                                    <ReactMarkdown>{formatModuleContent(module.content)}</ReactMarkdown>
                                </div>
                            )}
                            {(() => {
                                const imageFile = fileNameFromPath(module.imagePath);
                                const imageUrl = imageFile ? apiUrl(`/api/media/${imageFile}`) : null;
                                if (!imageUrl) return null;
                                return (
                                    <div>
                                        <h4>Module Image</h4>
                                        <img src={imageUrl} alt={`Module ${moduleNum}`} style={{ maxWidth: 320 }} />
                                    </div>
                                );
                            })()}

                            {(() => {
                                const audioFile = fileNameFromPath(module.audioPath);
                                const audioUrl = audioFile ? apiUrl(`/api/media/${audioFile}`) : null;
                                const audioChunks: string[] = Array.isArray(module.audioPaths) ? module.audioPaths : [];

                                if (audioUrl) {
                                    return (
                                        <div>
                                            <h4>Audio</h4>
                                            <audio controls src={audioUrl} />
                                            {audioChunks.length > 1 && (
                                                <div style={{ marginTop: 8 }}>
                                                    {audioChunks.map((chunkPath, idx) => {
                                                        const chunkFile = fileNameFromPath(chunkPath);
                                                        if (!chunkFile) return null;
                                                        return (
                                                            <div key={`${moduleNum}-chunk-${idx}`} style={{ marginBottom: 6 }}>
                                                                <div className="muted">Chunk {idx + 1}</div>
                                                                <audio controls src={apiUrl(`/api/media/${chunkFile}`)} />
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                            <div>
                                                <button
                                                    type="button"
                                                    className="secondary"
                                                    disabled={hasActiveRequest}
                                                    onClick={() => {
                                                        void regenerateModule(moduleNum);
                                                    }}
                                                >
                                                    {moduleActionBusy === moduleNum ? "Regenerating..." : "Regenerate Audio"}
                                                </button>
                                            </div>
                                        </div>
                                    );
                                }

                                if (!audioUrl && audioChunks.length > 0) {
                                    return (
                                        <div>
                                            <h4>Audio</h4>
                                            {audioChunks.map((chunkPath, idx) => {
                                                const chunkFile = fileNameFromPath(chunkPath);
                                                if (!chunkFile) return null;
                                                return (
                                                    <div key={`${moduleNum}-chunk-only-${idx}`} style={{ marginBottom: 6 }}>
                                                        <div className="muted">Chunk {idx + 1}</div>
                                                        <audio controls src={apiUrl(`/api/media/${chunkFile}`)} />
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    );
                                }

                                return (
                                    <button
                                        type="button"
                                        className="secondary"
                                        disabled={hasActiveRequest}
                                        onClick={() => {
                                            void regenerateModule(moduleNum);
                                        }}
                                    >
                                        {moduleActionBusy === moduleNum ? "Generating..." : "Generate Audio"}
                                    </button>
                                );
                            })()}

                            {module.knowledgeCheck && (
                                <div style={{ marginTop: "24px" }}>
                                    <h4>Knowledge Check</h4>
                                    <div className="panel" style={{ marginTop: "8px" }}>
                                        <p style={{ fontWeight: 500, marginBottom: "12px", fontSize: "1.05rem" }}>{module.knowledgeCheck.question}</p>
                                        <div style={{ paddingLeft: "16px", borderLeft: "3px solid var(--border)", marginBottom: "16px" }}>
                                            {['A', 'B', 'C', 'D'].map(opt => (
                                                <div key={opt} style={{ marginBottom: "8px", color: module.knowledgeCheck.correctAnswer === opt ? "var(--primary)" : "inherit", fontWeight: module.knowledgeCheck.correctAnswer === opt ? 600 : 400 }}>
                                                    <span style={{ display: "inline-block", width: "24px", fontWeight: 600 }}>{opt}.</span>
                                                    {module.knowledgeCheck.options?.[opt]} {module.knowledgeCheck.correctAnswer === opt && <span style={{ marginLeft: "8px" }}>✓</span>}
                                                </div>
                                            ))}
                                        </div>
                                        <div style={{ fontSize: "0.9rem", background: "var(--background)", padding: "12px", borderRadius: "6px" }}>
                                            <div style={{ marginBottom: "6px" }}><strong style={{ color: "var(--primary)" }}>Correct Feedback:</strong> {module.knowledgeCheck.feedback?.correct}</div>
                                            <div><strong style={{ color: "var(--secondary)" }}>Incorrect Feedback:</strong> {module.knowledgeCheck.feedback?.incorrect}</div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            {module.flashcards && module.flashcards.length > 0 && (
                                <div style={{ marginTop: "24px" }}>
                                    <h4>Interactive</h4>
                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginTop: "12px" }}>
                                        {module.flashcards.map((fc: any, i: number) => (
                                            <div key={fc.id || i} style={{ padding: "16px", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                                                <div className="muted" style={{ fontSize: "0.75rem", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 600 }}>Front</div>
                                                <div style={{ fontWeight: 500, marginBottom: "16px", fontSize: "1.05rem" }}>{fc.front}</div>
                                                <div className="muted" style={{ fontSize: "0.75rem", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 600 }}>Back</div>
                                                <div style={{ lineHeight: 1.5 }}>{fc.back}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
