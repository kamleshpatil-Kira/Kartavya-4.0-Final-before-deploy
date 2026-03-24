"use client";

import React, { useState } from "react";

interface OutlineEditorProps {
    courseData: any;
    saveCourse: (updatedData: any) => Promise<void>;
    setUiNotice: (notice: { type: "error" | "success" | "info"; text: string } | null) => void;
}

export function OutlineEditor({ courseData, saveCourse, setUiNotice }: OutlineEditorProps) {
    const [editingOutline, setEditingOutline] = useState(false);
    const [outlineCache, setOutlineCache] = useState<any>(null);
    const [savingOutline, setSavingOutline] = useState(false);

    const toggleEditOutline = () => {
        if (!editingOutline) {
            setOutlineCache(JSON.parse(JSON.stringify(courseData.outline)));
        }
        setEditingOutline(!editingOutline);
    };

    const saveOutline = async () => {
        if (!outlineCache || savingOutline) return;
        setSavingOutline(true);
        setUiNotice(null);
        try {
            const updated = { ...courseData };
            updated.outline = outlineCache;
            await saveCourse(updated);
            setEditingOutline(false);
            setUiNotice({ type: "success", text: "Outline saved." });
        } catch (err: any) {
            setUiNotice({ type: "error", text: `Failed to save outline: ${err?.message || "Unknown error"}` });
        } finally {
            setSavingOutline(false);
        }
    };

    if (!courseData?.outline) return null;

    return (
        <div className="card surface">
            <div className="inline" style={{ justifyContent: "space-between", width: "100%" }}>
                <h2 className="section-title">Course Outline</h2>
                <div className="inline" style={{ gap: 8 }}>
                    {editingOutline && <span className="muted" style={{ fontSize: '0.8rem' }}>💡 Press Enter to save</span>}
                    <button type="button" className="secondary" onClick={toggleEditOutline}>
                        {editingOutline ? "Cancel" : "Edit"}
                    </button>
                </div>
            </div>

            {editingOutline && outlineCache ? (
                <div>
                    <div className="field" style={{ marginBottom: 16 }}>
                        <label>Course Title</label>
                        <input
                            value={outlineCache.courseTitle || ""}
                            onChange={(e) => setOutlineCache({ ...outlineCache, courseTitle: e.target.value })}
                            onKeyDown={(e) => { if (e.key === 'Enter') { void saveOutline(); } }}
                        />
                    </div>
                    <div className="field" style={{ marginBottom: 16 }}>
                        <label>Course Description</label>
                        <input
                            value={outlineCache.courseDescription || ""}
                            onChange={(e) => setOutlineCache({ ...outlineCache, courseDescription: e.target.value })}
                            onKeyDown={(e) => { if (e.key === 'Enter') { void saveOutline(); } }}
                        />
                    </div>
                    {(outlineCache.modules || []).map((mod: any, idx: number) => (
                        <div key={idx} style={{ marginBottom: 20, padding: 16, border: '1px solid var(--border)', borderRadius: 8 }}>
                            <div className="field" style={{ marginBottom: 12 }}>
                                <label>Module {mod.moduleNumber || idx + 1} Title</label>
                                <input
                                    value={mod.moduleTitle || ""}
                                    onChange={(e) => {
                                        const mods = [...outlineCache.modules];
                                        mods[idx] = { ...mods[idx], moduleTitle: e.target.value };
                                        setOutlineCache({ ...outlineCache, modules: mods });
                                    }}
                                    onKeyDown={(e) => { if (e.key === 'Enter') { void saveOutline(); } }}
                                />
                            </div>
                            <label>Learning Objectives</label>
                            {(mod.learningObjectives || []).map((obj: string, oi: number) => (
                                <div key={oi} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'center' }}>
                                    <input
                                        style={{ flex: 1 }}
                                        value={obj}
                                        onChange={(e) => {
                                            const mods = [...outlineCache.modules];
                                            const objs = [...(mods[idx].learningObjectives || [])];
                                            objs[oi] = e.target.value;
                                            mods[idx] = { ...mods[idx], learningObjectives: objs };
                                            setOutlineCache({ ...outlineCache, modules: mods });
                                        }}
                                        onKeyDown={(e) => { if (e.key === 'Enter') { void saveOutline(); } }}
                                    />
                                    <button
                                        type="button"
                                        className="secondary"
                                        style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                                        onClick={() => {
                                            const mods = [...outlineCache.modules];
                                            const objs = [...(mods[idx].learningObjectives || [])];
                                            objs.splice(oi, 1);
                                            mods[idx] = { ...mods[idx], learningObjectives: objs };
                                            setOutlineCache({ ...outlineCache, modules: mods });
                                        }}
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                className="secondary"
                                style={{ marginTop: 6, fontSize: '0.85rem' }}
                                onClick={() => {
                                    const mods = [...outlineCache.modules];
                                    const objs = [...(mods[idx].learningObjectives || []), ""];
                                    mods[idx] = { ...mods[idx], learningObjectives: objs };
                                    setOutlineCache({ ...outlineCache, modules: mods });
                                }}
                            >
                                + Add Objective
                            </button>
                        </div>
                    ))}
                    <button type="button" disabled={savingOutline} onClick={() => { void saveOutline(); }}>
                        {savingOutline ? "Saving..." : "Save Outline"}
                    </button>
                </div>
            ) : (
                courseData.outline.modules && courseData.outline.modules.length > 0 ? (
                    <div>
                        {courseData.outline.modules.map((mod: any, idx: number) => (
                            <div key={idx} style={{ marginBottom: 24 }}>
                                <h3 style={{ marginBottom: 8 }}>Module {mod.moduleNumber || idx + 1}: {mod.moduleTitle}</h3>
                                {mod.learningObjectives && mod.learningObjectives.length > 0 && (
                                    <ul style={{ paddingLeft: 20 }}>
                                        {mod.learningObjectives.map((obj: string, oi: number) => (
                                            <li key={oi} style={{ marginBottom: 4 }}>{obj}</li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="muted">No modules defined in outline.</p>
                )
            )}
        </div>
    );
}
