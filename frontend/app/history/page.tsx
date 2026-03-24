"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useCourse } from "../context/CourseContext";
import { apiFetch } from "../lib/api";
import { Clock, Trash2 } from "lucide-react";

export default function HistoryPage() {
  const { setCourseData, setCourseId } = useCourse();
  const [history, setHistory] = useState<any[]>([]);
  const [uiNotice, setUiNotice] = useState<{ type: "error" | "success" | "info"; text: string } | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [loadingCourseId, setLoadingCourseId] = useState<string | null>(null);
  const router = useRouter();

  const loadHistory = async () => {
    try {
      const res = await apiFetch<{ history: any[] }>("/api/history");
      setHistory(res.history || []);
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to load history." });
    }
  };

  useEffect(() => {
    void loadHistory(); // Fix D1: removed dead .catch — loadHistory already handles its own errors
  }, []);

  const viewCourse = async (id: string) => {
    setLoadingCourseId(id);
    setUiNotice(null);
    try {
      const res = await apiFetch<any>(`/api/course/${id}`);
      setCourseData(res);
      setCourseId(id);
      router.push("/view");
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to load selected course." });
    } finally {
      setLoadingCourseId(null);
    }
  };

  const clearHistory = async () => {
    if (clearingHistory) return;
    setClearingHistory(true);
    setUiNotice(null);
    try {
      await apiFetch("/api/history", { method: "DELETE" });
      setHistory([]);
      setConfirmClear(false);
      setUiNotice({ type: "success", text: "History cleared." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to clear history." });
    } finally {
      setClearingHistory(false);
    }
  };

  const deleteEntry = async (id: string) => {
    try {
      await apiFetch(`/api/history/${id}`, { method: "DELETE" });
      setHistory((prev) => prev.filter((h) => h.id !== id));
      setUiNotice({ type: "success", text: "Entry removed from history." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to delete entry." });
    }
  };

  return (
    <div>
      <div className="card hero">
        <div>
          <div className="hero-pill">Library</div>
          <h1>Course History</h1>
          <p>Reopen previous courses, inspect metadata, and reuse assets.</p>
        </div>
        <div className="panel">
          <div className="muted">Status</div>
          <p style={{ margin: 0 }}>{history.length} course(s) stored</p>
        </div>
      </div>

      {uiNotice && (
        <div className={`notice ${uiNotice.type}`} role={uiNotice.type === "error" ? "alert" : "status"}>
          {uiNotice.text}
        </div>
      )}

      {history.length === 0 && (
        <div className="card surface empty-state">
          <Clock size={48} className="empty-state-icon" />
          <h3>No course history yet</h3>
          <p className="muted">
            Once you generate a course, it will appear here so you can revisit, download, or reuse it.
          </p>
          <button
            type="button"
            onClick={() => router.push("/")}
            style={{ marginTop: 8 }}
          >
            Create First Course
          </button>
        </div>
      )}

      {history.map((course) => (
        <div className="card surface history-card" key={course.id}>
          <div className="card-head">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h3 className="card-title-sm">{course.title || "Untitled"}</h3>
                {course.modules === 0 && <span className="badge" style={{ fontSize: '0.7rem' }}>Outline Only</span>}
              </div>
              <p className="muted" style={{ margin: "4px 0 0" }}>Created: {course.created_at || "-"}</p>
            </div>
            <span className="badge">ID: {String(course.id || "").slice(0, 12) || "-"}</span>
          </div>
          <div className="meta-chip-row">
            <span className="chip-soft">Modules: {course.modules || 0}</span>
            <span className="chip-soft">Level: {course.course_level || "n/a"}</span>
            <span className="chip-soft">{course.has_quiz ? "Quiz: Yes" : "Quiz: No"}</span>
            <span className="chip-soft">{(course.has_interactive || course.has_flashcards) ? "Interactive: Yes" : "Interactive: No"}</span>
          </div>
          <div className="inline">
            <button
              type="button"
              className="secondary"
              disabled={clearingHistory || loadingCourseId !== null}
              onClick={() => { void viewCourse(course.id); }}
            >
              {loadingCourseId === course.id ? "Opening..." : "View"}
            </button>
            <button
              type="button"
              className="secondary"
              disabled={clearingHistory || loadingCourseId !== null}
              onClick={() => { void deleteEntry(course.id); }}
              title="Remove from history"
              style={{ padding: "6px 10px", color: "#b91c1c" }}
            >
              <Trash2 size={15} />
            </button>
          </div>
        </div>
      ))}

      {history.length > 0 && (
        <div className="card surface">
          {!confirmClear ? (
            <button
              type="button"
              className="secondary"
              disabled={clearingHistory || loadingCourseId !== null}
              onClick={() => setConfirmClear(true)}
            >
              Clear History
            </button>
          ) : (
            <div>
              <p className="muted" style={{ marginTop: 0 }}>
                This will permanently delete your full local history list.
              </p>
              <div className="danger-actions">
                <button type="button" disabled={clearingHistory} onClick={() => void clearHistory()}>
                  {clearingHistory ? "Clearing..." : "Confirm Clear"}
                </button>
                <button type="button" className="secondary" disabled={clearingHistory} onClick={() => setConfirmClear(false)}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
