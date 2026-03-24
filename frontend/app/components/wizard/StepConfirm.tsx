"use client";

import React from "react";
import type { FormState } from "./StepGenerationMode";

interface Props {
    form: FormState;
    estimate: { min: number; max: number };
}

export function StepConfirm({ form, estimate }: Props) {
    return (
        <div className="card surface">
            <h2 className="section-title">Step 4 · Review &amp; Confirm</h2>
            <div className="grid">
                <div>
                    <p><strong>Course Title:</strong> {form.courseTitle || "-"}</p>
                    <p><strong>Audience:</strong> {form.targetAudience || "-"}</p>
                    {/* <p><strong>Institute:</strong> {form.institute || "-"}</p> */}
                    <p><strong>Laws:</strong> {form.relevantLaws || "-"}</p>
                    <p><strong>Tone:</strong> {form.tone.join(", ") || "-"}</p>
                </div>
                <div>
                    <p><strong>Modules:</strong> {form.numModules}</p>
                    <p><strong>Language:</strong> {form.courseLanguage}</p>
                    <p><strong>Audio:</strong> {form.includeAudio ? "Yes" : "No"}</p>
                    <p><strong>Images:</strong> {form.includeImages ? "AI-generated (1 per module)" : "No"}</p>

                    <p><strong>Quiz:</strong> {form.addQuizzes ? "Yes" : "No"}</p>
                    <p>
                        <strong>Interactives:</strong>{" "}
                        {form.interactiveBlocks.length > 0
                            ? form.interactiveBlocks
                                .map((k) =>
                                    k === "tabs" ? "Tabs" :
                                        k === "accordion" ? "Accordion" :
                                            k === "note" ? "Callout" :
                                                k === "table" ? "Table" :
                                                    k === "flipcard" ? "Flip Cards" : k
                                )
                                .join(", ")
                            : "None"}
                    </p>
                </div>
            </div>
            <div className="estimate" style={{ marginTop: 10 }}>
                Estimated time: ~{estimate.min}-{estimate.max} min
            </div>
            <p className="muted">Confirm to generate your course. This may take several minutes.</p>
        </div>
    );
}
