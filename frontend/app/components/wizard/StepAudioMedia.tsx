"use client";

import React from "react";
import { InfoTip } from "../InfoTip";
import { Slider } from "@heroui/react";
import { AlertCircle } from "lucide-react";
import type { FormState } from "./StepGenerationMode";

interface Props {
    form: FormState;
    setForm: React.Dispatch<React.SetStateAction<FormState>>;
    isPreviewingAudio: boolean;
    previewAudioUrl: string | null;
    previewAudio: () => Promise<void>;
}

export function StepAudioMedia({
    form,
    setForm,
    isPreviewingAudio,
    previewAudioUrl,
    previewAudio,
}: Props) {
    return (
        <div className="card surface">
            <h2 className="section-title">Step 3 · Audio &amp; Media</h2>
            <div className="grid">
                <div>
                    <div className="field">
                        <label>
                            Include Audio
                            <InfoTip text="Adds narration audio to each module." />
                        </label>
                        <select
                            value={form.includeAudio ? "yes" : "no"}
                            onChange={(e) => setForm({ ...form, includeAudio: e.target.value === "yes" })}
                        >
                            <option value="yes">With audio</option>
                            <option value="no">Without audio</option>
                        </select>
                    </div>
                    <div className="field">
                        <label>
                            Voice Gender
                            <InfoTip text="Select a voice style for narration." />
                        </label>
                        <select
                            value={form.voiceGender}
                            onChange={(e) => setForm({ ...form, voiceGender: e.target.value })}
                        >
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                        </select>
                    </div>
                    <div className="field">
                        <label>
                            Speech Speed
                            <InfoTip text="Control TTS speed. 1.0 is normal." />
                        </label>
                        <Slider
                            aria-label="Speech Speed"
                            step={0.1}
                            minValue={0.5}
                            maxValue={2.0}
                            value={form.speechSpeed}
                            onChange={(val) => setForm({ ...form, speechSpeed: Number(val) })}
                            color="primary"
                            size="md"
                            showTooltip
                            tooltipValueFormatOptions={{ style: "decimal", minimumFractionDigits: 1 }}
                            startContent={
                                <span style={{ fontSize: "0.75rem", color: "var(--muted, #94a3b8)", whiteSpace: "nowrap" }}>
                                    Slow
                                </span>
                            }
                            endContent={
                                <span style={{ fontSize: "0.75rem", color: "var(--muted, #94a3b8)", whiteSpace: "nowrap" }}>
                                    Fast
                                </span>
                            }
                            getValue={(val) => `${Number(val).toFixed(1)}x`}
                            className="max-w-md"
                        />
                    </div>
                </div>
                <div>
                    {form.includeAudio && (
                        <>
                            <p className="muted">Audio accent is based on course language: {form.courseLanguage}</p>
                            <button
                                type="button"
                                className="secondary"
                                disabled={isPreviewingAudio}
                                onClick={() => void previewAudio()}
                            >
                                {isPreviewingAudio ? "Generating Preview..." : "Generate Voice Preview"}
                            </button>
                            {previewAudioUrl && (
                                <audio controls src={previewAudioUrl} style={{ display: "block", marginTop: 12 }} />
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Image Generation Section */}
            <div style={{ marginTop: 24, borderTop: "1px solid var(--border, #e2e8f0)", paddingTop: 20 }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: 12 }}>Image Generation</h3>
                <div className="grid">
                    <div>
                        <div className="field">
                            <label>
                                Include Images
                                <InfoTip text="Generates one AI photorealistic image per module based on its topic." />
                            </label>
                            <select
                                value={form.includeImages ? "yes" : "no"}
                                onChange={(e) => setForm({ ...form, includeImages: e.target.value === "yes" })}
                            >
                                <option value="no">Without images</option>
                                <option value="yes">With images</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        {form.includeImages && (
                            <div style={{
                                padding: "12px 16px",
                                borderRadius: 8,
                                background: "rgba(234, 179, 8, 0.08)",
                                border: "1px solid rgba(234, 179, 8, 0.2)",
                                fontSize: "0.85rem",
                                color: "var(--text, #334155)",
                                display: "flex",
                                alignItems: "start",
                                gap: "8px"
                            }}>
                                <AlertCircle size={16} style={{ marginTop: "2px", color: "#eab308", flexShrink: 0 }} />
                                <div>
                                    <strong>Note:</strong> Adds ~2–3 minutes to generation time.
                                    <br />1 photorealistic image per module (16:9 aspect ratio).
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
