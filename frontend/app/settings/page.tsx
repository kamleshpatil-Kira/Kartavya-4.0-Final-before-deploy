"use client";

import React, { useState } from "react";
import { apiFetch } from "../lib/api";

interface VoiceRecord {
  name: string;
  description?: string;
  gender?: string;
  accent?: string;
  language?: string;
}

interface ImageStats {
  total_generated: number;
  total_regenerated: number;
  last_updated: string;
  by_course: any[];
}

export default function SettingsPage() {
  const [voices, setVoices] = useState<VoiceRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const [imageStats, setImageStats] = useState<ImageStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  const loadVoices = async () => {
    setLoading(true);
    try {
      const res = await apiFetch<{ voices: VoiceRecord[] }>("/api/tts/voices");
      setVoices(res.voices || []);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    setLoadingStats(true);
    try {
      const res = await apiFetch<ImageStats>("/api/image-stats");
      setImageStats(res);
    } finally {
      setLoadingStats(false);
    }
  };

  const groupedByLanguage = voices.reduce<Record<string, { male: VoiceRecord[]; female: VoiceRecord[] }>>((acc, voice) => {
    const key = voice.language || "Unknown";
    if (!acc[key]) acc[key] = { male: [], female: [] };
    if (voice.gender === "male") acc[key].male.push(voice);
    else acc[key].female.push(voice);
    return acc;
  }, {});

  const languageEntries = Object.entries(groupedByLanguage).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div>
      <div className="card hero">
        <div>
          <div className="hero-pill">Configuration</div>
          <h1>Settings</h1>
          <p>Review voice availability and backend tooling.</p>
        </div>
        <div className="panel">
          <div className="muted">TTS</div>
          <p style={{ margin: 0 }}>Fetch available audio voices.</p>
        </div>
      </div>

      <div className="card surface">
        <div className="card-head">
          <h2 className="section-title">Audio Voices</h2>
          {languageEntries.length > 0 && <span className="badge">{voices.length} voice(s)</span>}
        </div>
        <p className="muted">Load available voices grouped by language for quick review.</p>
        <button type="button" disabled={loading} onClick={() => void loadVoices()}>
          {loading ? "Loading..." : "List Available Voices"}
        </button>
        {!loading && languageEntries.length === 0 && (
          <div className="empty-state" style={{ marginTop: 14 }}>
            <p className="muted" style={{ margin: 0 }}>No voices loaded yet. Click "List Available Voices".</p>
          </div>
        )}
        {languageEntries.length > 0 && (
          <div className="voice-groups" style={{ marginTop: 16 }}>
            {languageEntries.map(([language, { male, female }]) => (
              <div key={language} className="voice-group">
                <div className="section-title" style={{ fontSize: "1rem", marginBottom: 8 }}>
                  {language}
                </div>
                {male.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <div className="muted" style={{ fontSize: "0.8rem", marginBottom: 4 }}>Male</div>
                    <div className="voice-list">
                      {male.map((voice, idx) => (
                        <div key={`${language}-male-${voice.name}-${idx}`} className="voice-item">
                          <strong>{voice.name}</strong>
                          <span className="muted">{voice.description || "No description"}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {female.length > 0 && (
                  <div>
                    <div className="muted" style={{ fontSize: "0.8rem", marginBottom: 4 }}>Female</div>
                    <div className="voice-list">
                      {female.map((voice, idx) => (
                        <div key={`${language}-female-${voice.name}-${idx}`} className="voice-item">
                          <strong>{voice.name}</strong>
                          <span className="muted">{voice.description || "No description"}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card surface">
        <div className="card-head">
          <h2 className="section-title">Image Generation Stats</h2>
          {imageStats && (
            <span className="badge">
              {imageStats.total_generated + imageStats.total_regenerated} Total
            </span>
          )}
        </div>
        <p className="muted">View usage statistics for AI image generation.</p>
        <button type="button" disabled={loadingStats} onClick={() => void loadStats()}>
          {loadingStats ? "Loading..." : "Load Statistics"}
        </button>

        {!loadingStats && !imageStats && (
          <div className="empty-state" style={{ marginTop: 14 }}>
            <p className="muted" style={{ margin: 0 }}>No stats loaded yet. Click "Load Statistics".</p>
          </div>
        )}

        {imageStats && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: "flex", gap: "16px", marginBottom: "20px" }}>
              <div className="panel" style={{ flex: 1 }}>
                <div className="muted" style={{ fontSize: "0.85rem", marginBottom: 4 }}>Total Generated</div>
                <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "var(--accent)" }}>
                  {imageStats.total_generated}
                </div>
              </div>
              <div className="panel" style={{ flex: 1 }}>
                <div className="muted" style={{ fontSize: "0.85rem", marginBottom: 4 }}>Total Regenerated</div>
                <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>
                  {imageStats.total_regenerated}
                </div>
              </div>
            </div>

            {imageStats.by_course && imageStats.by_course.length > 0 && (
              <div>
                <h3 className="section-title" style={{ fontSize: "1rem", marginBottom: 12 }}>Usage by Course</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {imageStats.by_course.map((course: any, idx: number) => (
                    <div key={idx} className="panel" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{course.course_title || course.course_id || "Unknown Course"}</strong>
                        {course.course_id && <div className="muted" style={{ fontSize: "0.75rem" }}>ID: {course.course_id}</div>}
                      </div>
                      <div style={{ display: "flex", gap: "12px", textAlign: "right", fontSize: "0.85rem" }}>
                        <div>
                          <div className="muted">Generated</div>
                          <strong>{course.generated}</strong>
                        </div>
                        <div>
                          <div className="muted">Regen</div>
                          <strong>{course.regenerated}</strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {imageStats.last_updated && (
              <div className="muted" style={{ fontSize: "0.75rem", marginTop: 16, textAlign: "right" }}>
                Last updated: {new Date(imageStats.last_updated).toLocaleString()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
