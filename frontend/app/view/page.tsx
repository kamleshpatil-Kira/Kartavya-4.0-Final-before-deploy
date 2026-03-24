"use client";

import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import ReactMarkdown from "react-markdown";
import { useRouter } from "next/navigation";
import { useCourse } from "../context/CourseContext";
import { apiFetch, apiFetchBlob, apiUrl } from "../lib/api";
import { COURSE_LANGUAGES, getVoicePreviewText, toTtsAccent } from "../lib/languages";
import { InfoTip } from "../components/InfoTip";
import { BookOpen, ChevronDown, Loader2, Info, AlertTriangle, Lightbulb, RefreshCw, Edit2, Wand2, ImageIcon } from "lucide-react";
import { OutlineEditor } from "../components/OutlineEditor";
import { QuizEditor } from "../components/QuizEditor";
import { Slider, Card, CardBody, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from "@heroui/react";
import dynamic from "next/dynamic";
import rehypeRaw from "rehype-raw";
import { marked } from "marked";
import { motion } from "framer-motion";
import "react-quill-new/dist/quill.snow.css";
import TurndownService from 'turndown';

const ReactQuill = dynamic(() => import("react-quill-new"), { ssr: false });

function AccordionPlainItem({ title, body }: { title: string; body: string }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div style={{ borderBottom: "1px solid #e2e8f0" }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 4px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left", fontWeight: 600, fontSize: "0.95rem", color: "#1e293b" }}
      >
        <span>{title}</span>
        <span style={{ fontSize: "1.2rem", color: "#94a3b8", lineHeight: 1, flexShrink: 0, marginLeft: "12px" }}>
          {open ? "−" : "+"}
        </span>
      </button>
      {open && (
        <div style={{ padding: "0 4px 16px 4px", color: "#475569", lineHeight: 1.7 }}>
          <ReactMarkdown>{body}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

function InteractiveBlockPreview({ block }: { block: any }) {
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});
  const [activeTab, setActiveTab] = useState(0);

  if (!block || !block.type || !block.data) return null;
  const { type: rawType, data } = block;
  const type = rawType?.toLowerCase() ?? "";

  const toggleFlip = (i: number) => {
    setFlipped((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  if (type === "tabs") {
    const tabs = data.tabs || [];
    return (
      <div style={{ margin: "24px 0" }}>
        <div style={{ display: "flex", gap: 0, borderBottom: "2px solid #e2e8f0", marginBottom: 0, flexWrap: "wrap" }}>
          {tabs.map((t: any, i: number) => (
            <button key={i} type="button" onClick={() => setActiveTab(i)} style={{ padding: "10px 20px", border: "none", background: "transparent", cursor: "pointer", fontSize: "0.95rem", fontWeight: activeTab === i ? 600 : 400, color: activeTab === i ? "var(--accent, #1b5aa6)" : "#64748b", borderBottom: activeTab === i ? "2px solid var(--accent, #1b5aa6)" : "2px solid transparent", marginBottom: "-2px", transition: "all 0.15s ease", whiteSpace: "nowrap" }}>
              {t.title || `Tab ${i + 1}`}
            </button>
          ))}
        </div>
        {tabs[activeTab] && (
          <div style={{ padding: "20px", background: "#fff", border: "1px solid #e2e8f0", borderTop: "none", borderRadius: "0 0 10px 10px", lineHeight: 1.7, color: "#374151" }}>
            <ReactMarkdown>{tabs[activeTab].content || ""}</ReactMarkdown>
          </div>
        )}
      </div>
    );
  }

  if (type === "accordion") {
    return (
      <div style={{ margin: "24px 0", border: "1px solid #e2e8f0", borderRadius: "10px", overflow: "hidden" }}>
        {(data.items || []).map((item: any, i: number) => <AccordionPlainItem key={i} title={item.question || item.heading || `Item ${i + 1}`} body={item.answer || item.body || ""} />)}
      </div>
    );
  }

  if (type === "note") {
    const variant = data.variant || data.type || "info";
    const themeClasses: Record<string, string> = { tip: "bg-success-50 border-success-200 text-success-900", warning: "bg-warning-50 border-warning-200 text-warning-900", important: "bg-danger-50 border-danger-200 text-danger-900", info: "bg-primary-50 border-primary-200 text-primary-900" };
    const iconColors: Record<string, string> = { tip: "text-success-600", warning: "text-warning-600", important: "text-danger-600", info: "text-primary-600" };
    const iconMap: Record<string, React.ReactNode> = { tip: <Lightbulb size={24} className={`mt-0.5 flex-shrink-0 ${iconColors.tip}`} />, warning: <AlertTriangle size={24} className={`mt-0.5 flex-shrink-0 ${iconColors.warning}`} />, important: <AlertTriangle size={24} className={`mt-0.5 flex-shrink-0 ${iconColors.important}`} />, info: <Info size={24} className={`mt-0.5 flex-shrink-0 ${iconColors.info}`} /> };
    return (
      <Card className={`my-8 shadow-sm border ${themeClasses[variant] || themeClasses.info}`}>
        <CardBody className="p-5">
          <div className="flex gap-4">
            {iconMap[variant] || iconMap.info}
            <div className="text-gray-800 font-medium leading-relaxed">
              <ReactMarkdown>{data.text || ""}</ReactMarkdown>
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (type === "table") {
    return (
      <div className="my-8 rounded-xl border border-gray-200 overflow-hidden bg-white shadow-sm">
        <div className="overflow-x-auto">
          <Table aria-label="Interactive Table" removeWrapper className="min-w-full">
            <TableHeader className="bg-gray-50 border-b border-gray-200">
              {(data.headers || []).map((h: string, i: number) => <TableColumn key={`h-${i}`} className="py-4 px-6 text-sm font-semibold text-gray-600 uppercase tracking-wider bg-gray-50">{h}</TableColumn>)}
            </TableHeader>
            <TableBody className="divide-y divide-gray-100">
              {(data.rows || []).map((row: string[], r: number) => (
                <TableRow key={r} className="hover:bg-gray-50/50 transition-colors">
                  {(row || []).map((cell: string, c: number) => <TableCell key={c} className="py-4 px-6 text-sm text-gray-700">{cell}</TableCell>)}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  if (type === "flipcard") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 my-8">
        {(data.cards || data.flashcards || []).map((c: any, i: number) => (
          <div key={i} className="h-56" style={{ perspective: "1200px" }}>
            <motion.div onClick={() => toggleFlip(i)} initial={false} animate={{ rotateY: flipped[i] ? 180 : 0 }} transition={{ duration: 0.5, type: "spring", stiffness: 260, damping: 20 }} style={{ cursor: "pointer", transformStyle: "preserve-3d", width: "100%", height: "100%" }}>
              <div className="relative w-full h-full" style={{ transformStyle: "preserve-3d" }}>
                <Card className={`absolute w-full h-full shadow-md hover:shadow-lg transition-shadow border border-gray-100 bg-white`} style={{ backfaceVisibility: "hidden" }}>
                  <CardBody className="flex flex-col items-center justify-center p-6 text-center h-full">
                    <div className="font-semibold text-xl text-gray-800 tracking-tight">{c.front}</div>
                    <div className="absolute bottom-4 flex items-center justify-center w-full left-0 opacity-60">
                      <span className="text-[11px] font-medium text-gray-400 uppercase tracking-widest bg-gray-50 px-3 py-1 rounded-full border border-gray-100">Click to flip</span>
                    </div>
                  </CardBody>
                </Card>
                <Card className={`absolute w-full h-full shadow-md border-t-4 border-t-primary border-x border-x-gray-100 border-b border-b-gray-100 bg-gray-50/80`} style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}>
                  <CardBody className="flex items-center justify-center p-6 text-center h-full overflow-y-auto custom-scrollbar">
                    <div className="text-gray-700 leading-relaxed font-medium">
                      <ReactMarkdown>{c.back}</ReactMarkdown>
                    </div>
                  </CardBody>
                </Card>
              </div>
            </motion.div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <pre style={{ fontSize: "13px", color: "var(--text-muted)", background: "var(--background-alt)", padding: "12px", borderRadius: "6px", overflowX: "auto" }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function formatModuleContent(content: any): string {
  if (!content) {
    return "";
  }
  if (typeof content === "string") {
    return content;
  }
  if (content.html) {
    return content.html;
  }

  const formatted: string[] = [];
  if (content.sections) {
    for (const section of content.sections) {
      if (section.sectionTitle) {
        formatted.push(`### ${section.sectionTitle}`);
      }
      if (section.content) {
        formatted.push(section.content);
      }
      if (section.concepts) {
        for (const concept of section.concepts) {
          if (concept.conceptTitle) {
            formatted.push(`#### ${concept.conceptTitle}`);
          }
          if (concept.explanation) {
            formatted.push(concept.explanation);
          }
          if (concept.scenario) {
            if (concept.scenario.description) {
              formatted.push(`**Scenario:** ${concept.scenario.description}`);
            }
            if (concept.scenario.whatToDo) {
              formatted.push(`**What to do:** ${concept.scenario.whatToDo}`);
            }
            if (concept.scenario.whyItMatters) {
              formatted.push(`**Why it matters:** ${concept.scenario.whyItMatters}`);
            }
            if (concept.scenario.howToPrevent) {
              formatted.push(`**How to prevent:** ${concept.scenario.howToPrevent}`);
            }
          }
        }
      }
      if (section.subsections) {
        for (const sub of section.subsections) {
          if (sub.subsectionTitle) {
            formatted.push(`#### ${sub.subsectionTitle}`);
          }
          if (sub.subsectionContent) {
            formatted.push(sub.subsectionContent);
          }
        }
      }
    }
  }

  if (content.learningObjectives) {
    formatted.push("**Learning Objectives:**");
    for (const obj of content.learningObjectives) {
      formatted.push(`- ${obj}`);
    }
  }

  if (content.keyPoints) {
    formatted.push("**Key Points:**");
    for (const point of content.keyPoints) {
      formatted.push(`- ${point}`);
    }
  }

  if (content.summary) {
    formatted.push("**Module Summary:**");
    formatted.push(content.summary);
  }

  return formatted.join("\n\n");
}

function fileNameFromPath(path?: string): string | null {
  if (!path) return null;
  const normalized = path.replace(/\\/g, "/").split("?")[0].split("#")[0];
  const parts = normalized.split("/");
  return parts[parts.length - 1] || null;
}

function resolveMediaUrl(path?: string): string | null {
  if (!path) return null;
  const trimmed = path.trim();
  if (!trimmed) return null;
  if (/^data:/i.test(trimmed) || /^https?:\/\//i.test(trimmed)) return trimmed;
  const file = fileNameFromPath(trimmed);
  return file ? apiUrl(`/api/media/${file}`) : null;
}

function ModalPortal({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted || typeof document === "undefined") return null;
  return createPortal(children, document.body);
}

function truncateTitle(title: string, maxWords = 6): string {
  if (!title) return title;
  const words = title.trim().split(/\s+/);
  if (words.length <= maxWords) return title;
  return words.slice(0, maxWords).join(' ') + '\u2026';
}

function estimateReadingTime(module: any): string {
  // Collect all text from the module's content structure
  const parts: string[] = [];
  const content = module.content;
  if (content) {
    if (typeof content === "string") {
      parts.push(content);
    } else if (content.html) {
      parts.push(content.html);
    } else if (content.sections) {
      for (const s of content.sections) {
        if (s.content) parts.push(s.content);
        if (s.concepts) {
          for (const c of s.concepts) {
            if (c.explanation) parts.push(c.explanation);
          }
        }
      }
    }
    if (content.summary) parts.push(content.summary);
  }
  // Strip HTML tags and count words
  const raw = parts.join(" ").replace(/<[^>]+>/g, " ");
  const wordCount = raw.trim().split(/\s+/).filter(Boolean).length;
  if (wordCount === 0) return "1–2 min";
  const mins = Math.max(1, Math.round(wordCount / 200));
  return `${mins}–${mins + 1} min`;
}

export default function ViewCoursePage() {
  const { courseData, setCourseData, courseId, jobState, startNewCourse } = useCourse();
  const router = useRouter();
  const effectiveCourseId = courseId || courseData?.course?.id || null;
  const [audioSettings, setAudioSettings] = useState({
    language: "English",
    gender: "male",
    speed: 1.0,
  });
  const [audioCacheBuster, setAudioCacheBuster] = useState(Date.now());
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [editModules, setEditModules] = useState<Record<number, boolean>>({});
  const [editIB, setEditIB] = useState<Record<number, boolean>>({});
  const [editKC, setEditKC] = useState<Record<number, boolean>>({});
  const [editFC, setEditFC] = useState<Record<number, boolean>>({});
  const [editCache, setEditCache] = useState<Record<number, any>>({});
  const [uiNotice, setUiNotice] = useState<{ type: "error" | "success" | "info"; text: string } | null>(null);
  const [audioActionBusy, setAudioActionBusy] = useState<"preview" | "regenerate-all" | null>(null);
  const [moduleActionBusy, setModuleActionBusy] = useState<number | null>(null);
  const [savingModuleNum, setSavingModuleNum] = useState<number | null>(null);
  const [sectionActionBusy, setSectionActionBusy] = useState<string | null>(null);
  const [editSections, setEditSections] = useState<Record<string, boolean>>({});
  const [sectionEditCache, setSectionEditCache] = useState<Record<string, any>>({});
  const [collapsedModules, setCollapsedModules] = useState<Record<number, boolean>>({});
  const [newIbType, setNewIbType] = useState<Record<number, string>>({});
  const [draggedModule, setDraggedModule] = useState<number | null>(null);
  const [dragOverModule, setDragOverModule] = useState<number | null>(null);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  // Image feature state
  const [imageRegen, setImageRegen] = useState<Record<number, boolean>>({});
  const [imageEdit, setImageEdit] = useState<Record<number, boolean>>({});
  const [imageEditPrompt, setImageEditPrompt] = useState<Record<number, string>>({});
  const [imageEditBusy, setImageEditBusy] = useState<Record<number, boolean>>({});
  const [previewImage, setPreviewImage] = useState<{
    url: string;
    title: string;
    moduleNum: number;
    moduleIndex: number;
    filename: string;
  } | null>(null);

  const toggleCollapse = (moduleNum: number) => {
    setCollapsedModules((prev) => ({ ...prev, [moduleNum]: !prev[moduleNum] }));
  };
  const modules = useMemo(() => courseData?.modules || [], [courseData]);

  useEffect(() => {
    if (modules.length > 0) {
      setCollapsedModules((prev) =>
        Object.keys(prev).length === 0
          ? Object.fromEntries(modules.map((m: any, i: number) => [m.moduleNumber || i + 1, true]))
          : prev
      );
    }
  }, [modules]);

  useEffect(() => {
    if (!previewImage) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPreviewImage(null);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [previewImage]);

  const hasModules = Array.isArray(modules) && modules.length > 0;
  const isOutlineOnly = !hasModules && !!courseData?.outline;
  const isGenerating = jobState.status === "queued" || jobState.status === "running";
  const progressValue = Math.max(0, Math.min(100, Number(jobState.progress) || 0));
  const visibleProgress = isGenerating ? Math.max(progressValue, 6) : progressValue;
  const statusMessage = jobState.message || (isGenerating ? "Generating course..." : "No active generation");
  const selectedAccent = toTtsAccent(audioSettings.language);
  const hasActiveRequest = audioActionBusy !== null || moduleActionBusy !== null || savingModuleNum !== null || sectionActionBusy !== null;

  useEffect(() => {
    const language = courseData?.course?.courseLanguage || "English";
    setAudioSettings((prev) => ({ ...prev, language }));
  }, [courseData?.course?.courseLanguage]);

  // Track active section via IntersectionObserver for outline highlighting
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const key = entry.target.id.replace('section-', '');
            setActiveSection(key);
            break;
          }
        }
      },
      { rootMargin: '-8% 0px -75% 0px', threshold: 0 }
    );
    const sectionEls = document.querySelectorAll('[id^="section-"]');
    sectionEls.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [modules, collapsedModules]);

  if (!courseData || !effectiveCourseId) {
    return (
      <div className="card hero">
        <div>
          <div className="hero-pill">Course Preview</div>
          <h1>Course Preview</h1>
          <p>Generate a course to preview it here. You'll see exactly how your learners will experience the content.</p>
          {isGenerating ? (
            <div className="notice info" role="status" style={{ marginTop: 14, marginBottom: 0 }}>
              Generation is still running. Open Course Generation to track live progress and status updates.
            </div>
          ) : (
            <div className="empty-state">
              <BookOpen size={52} className="empty-state-icon" />
              <h3>No course to preview</h3>
              <p>Generate or select a course from history to preview it here.</p>
            </div>
          )}
          {isGenerating && (
            <div className="loading-shell" role="status" aria-live="polite" style={{ marginTop: 12 }}>
              <div className="loading-head">
                <span className="loading-spinner" aria-hidden />
                <div>
                  <div className="muted" style={{ fontSize: "0.8rem" }}>Generation status</div>
                  <div className="loading-title">{statusMessage}</div>
                </div>
              </div>
              <div className="progress-track small" style={{ marginTop: 10 }}>
                <div className="progress-bar indeterminate" style={{ width: `${visibleProgress}%` }} />
              </div>
              <div className="inline" style={{ marginTop: 8 }}>
                <span className="badge">Progress {progressValue}%</span>
                {jobState.status && <span className="pill">Status: {jobState.status}</span>}
              </div>
            </div>
          )}
          <div className="inline" style={{ marginTop: 12 }}>
            <button type="button" onClick={() => router.push("/")}>Open Course Generation</button>
            <button type="button" className="secondary" onClick={() => router.push("/history")}>Open Course History</button>
          </div>
        </div>
        <div className="panel">
          <div className="muted">Tip</div>
          <p style={{ margin: 0 }}>
            Create a course using the Course Generation wizard, then come back here to preview and fine-tune it before exporting.
          </p>
        </div>
      </div>
    );
  }

  const saveCourse = async (updated: any) => {
    await apiFetch("/api/course/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });
    setCourseData(updated);
  };

  const reorderModules = (fromNum: number, toNum: number) => {
    if (fromNum === toNum) return;
    if (hasActiveRequest || savingModuleNum !== null || sectionActionBusy !== null) {
      setUiNotice({ type: "error", text: "Please wait for current saves or generations to finish before reordering." });
      return;
    }
    const updated = { ...courseData } as any;
    const arr = [...updated.modules];
    const fromIdx = arr.findIndex((m: any) => (m.moduleNumber || 0) === fromNum);
    const toIdx = arr.findIndex((m: any) => (m.moduleNumber || 0) === toNum);
    if (fromIdx === -1 || toIdx === -1) return;
    const [moved] = arr.splice(fromIdx, 1);
    arr.splice(toIdx, 0, moved);
    // Reassign moduleNumber sequentially after reorder
    arr.forEach((m: any, i: number) => { m.moduleNumber = i + 1; });
    updated.modules = arr;
    void saveCourse(updated);
  };

  const regenerateAllAudio = async () => {
    if (audioActionBusy || moduleActionBusy !== null || savingModuleNum !== null || sectionActionBusy !== null) return;
    setAudioActionBusy("regenerate-all");
    setUiNotice(null);
    try {
      const res = await apiFetch<any>(`/api/course/${effectiveCourseId}/audio/regenerate-all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audioOptions: { accent: selectedAccent, gender: audioSettings.gender, speed: audioSettings.speed } }),
      });
      setCourseData(res.course_data);
      setAudioCacheBuster(Date.now());
      setUiNotice({ type: "success", text: "Audio regenerated for all modules." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Audio regeneration failed: ${err?.message || "Unknown error"}` });
    } finally {
      setAudioActionBusy(null);
    }
  };

  const previewAudio = async () => {
    if (audioActionBusy || moduleActionBusy !== null || savingModuleNum !== null || sectionActionBusy !== null) return;
    setAudioActionBusy("preview");
    setPreviewUrl(null);
    setUiNotice(null);
    try {
      const blob = await apiFetchBlob("/api/audio/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: getVoicePreviewText(audioSettings.language),
          language: audioSettings.language,
          accent: selectedAccent,
          gender: audioSettings.gender,
          speed: audioSettings.speed,
        }),
      });
      setPreviewUrl(URL.createObjectURL(blob));
      setUiNotice({ type: "success", text: "Voice preview generated." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Voice preview failed: ${err?.message || "Unknown error"}` });
    } finally {
      setAudioActionBusy(null);
    }
  };

  const regenerateModule = async (moduleNum: number) => {
    if (audioActionBusy || moduleActionBusy !== null || savingModuleNum !== null || sectionActionBusy !== null) return;
    setModuleActionBusy(moduleNum);
    setUiNotice(null);
    try {
      const res = await apiFetch<any>(`/api/course/${effectiveCourseId}/module/${moduleNum}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audioOptions: { accent: selectedAccent, gender: audioSettings.gender, speed: audioSettings.speed } }),
      });
      // Add _imgTs to the regenerated module so the browser busts the image cache
      const ts = Date.now();
      const updatedModules = (res.course_data.modules || []).map((m: any) =>
        (m.moduleNumber ?? 0) === moduleNum ? { ...m, _imgTs: ts } : m
      );
      setCourseData({ ...res.course_data, modules: updatedModules });
      setUiNotice({ type: "success", text: `Module ${moduleNum} regenerated.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Module regeneration failed: ${err?.message || "Unknown error"}` });
    } finally {
      setModuleActionBusy(null);
    }
  };

  const regenerateModuleAudio = async (moduleNum: number) => {
    if (audioActionBusy || moduleActionBusy !== null || savingModuleNum !== null || sectionActionBusy !== null) return;
    setModuleActionBusy(moduleNum);
    setUiNotice(null);
    try {
      const res = await apiFetch<any>(`/api/course/${effectiveCourseId}/module/${moduleNum}/audio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audioOptions: { accent: selectedAccent, gender: audioSettings.gender, speed: audioSettings.speed } }),
      });
      setCourseData(res.course_data);
      setAudioCacheBuster(Date.now());
      setUiNotice({ type: "success", text: `Audio regenerated for module ${moduleNum}.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Module audio regeneration failed: ${err?.message || "Unknown error"}` });
    } finally {
      setModuleActionBusy(null);
    }
  };

  async function regenerateModuleImage(moduleNum: number, moduleIndex: number) {
    setImageRegen(prev => ({ ...prev, [moduleNum]: true }));
    try {
      const data = await apiFetch<any>(`/api/course/${effectiveCourseId}/image/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ moduleIndex }),
      });
      const ts = Date.now();
      setCourseData((prev: any) => {
        if (!prev) return prev;
        const mods = [...prev.modules];
        mods[moduleIndex] = { ...mods[moduleIndex], imagePath: data.imagePath, _imgTs: ts };
        return { ...prev, modules: mods };
      });
    } catch (e: any) {
      alert(`Image regeneration failed: ${e.message}`);
    } finally {
      setImageRegen(prev => ({ ...prev, [moduleNum]: false }));
    }
  }

  async function editModuleImage(moduleNum: number, moduleIndex: number) {
    const prompt = imageEditPrompt[moduleNum]?.trim();
    if (!prompt) return;
    setImageEditBusy(prev => ({ ...prev, [moduleNum]: true }));
    try {
      const data = await apiFetch<any>(`/api/course/${effectiveCourseId}/image/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ moduleIndex, editPrompt: prompt }),
      });
      const ts = Date.now();
      setCourseData((prev: any) => {
        if (!prev) return prev;
        const mods = [...prev.modules];
        mods[moduleIndex] = { ...mods[moduleIndex], imagePath: data.imagePath, _imgTs: ts };
        return { ...prev, modules: mods };
      });
      setImageEdit(prev => ({ ...prev, [moduleNum]: false }));
      setImageEditPrompt(prev => ({ ...prev, [moduleNum]: "" }));
    } catch (e: any) {
      alert(`Image edit failed: ${e.message}`);
    } finally {
      setImageEditBusy(prev => ({ ...prev, [moduleNum]: false }));
    }
  }

  const regenerateSectionAudio = async (moduleNum: number, sectionIdx: number) => {
    if (hasActiveRequest) return;
    const key = `${moduleNum}-${sectionIdx}-audio`;
    setSectionActionBusy(key);
    setUiNotice(null);
    try {
      const res = await apiFetch<any>(`/api/course/${effectiveCourseId}/module/${moduleNum}/section/${sectionIdx + 1}/audio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audioOptions: { accent: selectedAccent, gender: audioSettings.gender, speed: audioSettings.speed } }),
      });
      setCourseData(res.course_data);
      setAudioCacheBuster(Date.now());
      setUiNotice({ type: "success", text: `Audio regenerated for section.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Section audio regeneration failed: ${err?.message || "Unknown error"}` });
    } finally {
      setSectionActionBusy(null);
    }
  };

  const toggleSectionEdit = (moduleNum: number, sectionIdx: number, section: any) => {
    const key = `${moduleNum}-${sectionIdx}`;
    const editing = !editSections[key];
    setEditSections({ ...editSections, [key]: editing });
    if (editing) {
      // Phase 1: Deep copy the section object to protect the schema structure
      const structuredObject = JSON.parse(JSON.stringify(section));

      const prepareHtml = (text: string) => {
        if (!text) return "";
        const isHtml = text.includes('<') && text.includes('>');
        return isHtml ? text : marked.parse(text) as string;
      };

      structuredObject.content = prepareHtml(structuredObject.content);

      if (structuredObject.concepts && Array.isArray(structuredObject.concepts)) {
        structuredObject.concepts = structuredObject.concepts.map((c: any) => ({
          ...c,
          explanation: prepareHtml(c.explanation)
        }));
      }

      setSectionEditCache({
        ...sectionEditCache,
        [key]: structuredObject,
      });
    }
  };

  const saveSectionEdit = async (moduleNum: number, moduleIdx: number, sectionIdx: number) => {
    const key = `${moduleNum}-${sectionIdx}`;
    const cache = sectionEditCache[key];
    if (!cache) return;

    if (hasActiveRequest) return;
    setSectionActionBusy(key);
    setUiNotice(null);
    try {
      const updated = { ...courseData } as any;
      updated.modules = [...updated.modules];
      const module = { ...updated.modules[moduleIdx] };
      const content = { ...module.content };
      const sections = [...content.sections];

      // Strip HTML back to markdown for proper xAPI display
      const turndownService = new TurndownService({ headingStyle: 'atx' });
      const cleanContent = cache.content ? turndownService.turndown(cache.content).replace(/\u00A0/g, ' ') : "";
      const cleanConcepts = (cache.concepts || []).map((c: any) => ({
        ...c,
        explanation: c.explanation ? turndownService.turndown(c.explanation).replace(/\u00A0/g, ' ') : ""
      }));

      // Save the entirely preserved object directly into the sections array
      sections[sectionIdx] = {
        ...sections[sectionIdx],
        ...cache,
        content: cleanContent,
        concepts: cleanConcepts
      };

      content.sections = sections;
      module.content = content;
      updated.modules[moduleIdx] = module;
      await saveCourse(updated);
      setEditSections({ ...editSections, [key]: false });
      setUiNotice({ type: "success", text: `Section changes saved.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Failed to save section: ${err?.message || "Unknown error"}` });
    } finally {
      setSectionActionBusy(null);
    }
  };

  const ensureEditCache = (moduleNum: number, module: any) => {
    if (!editCache[moduleNum]) {
      const isStructured = Array.isArray(module.content?.sections) && module.content.sections.length > 0;
      let htmlContent = "";
      if (!isStructured) {
        const initialContent = formatModuleContent(module.content).trim();
        const isHtml = initialContent.includes('<') && initialContent.includes('>');
        htmlContent = isHtml ? initialContent : marked.parse(initialContent) as string;
      }
      setEditCache(prev => ({
        ...prev, [moduleNum]: {
          title: module.moduleTitle,
          content: htmlContent,
          knowledgeCheck: module.knowledgeCheck ? JSON.parse(JSON.stringify(module.knowledgeCheck)) : { question: "", options: { A: "", B: "", C: "", D: "" }, correctAnswer: "A", feedback: { correct: "", incorrect: "" } },
          flashcards: module.flashcards ? JSON.parse(JSON.stringify(module.flashcards)) : [],
          interactiveBlock: typeof module.content === 'object' && module.content?.interactiveBlock ? JSON.parse(JSON.stringify(module.content.interactiveBlock)) : null,
        }
      }));
    }
  };
  const toggleEdit = (moduleNum: number, module: any) => {
    const editing = !editModules[moduleNum];
    setEditModules({ ...editModules, [moduleNum]: editing });
    if (editing) { ensureEditCache(moduleNum, module); }
    if (editing) {
      const isStructured = Array.isArray(module.content?.sections) && module.content.sections.length > 0;
      let htmlContent = "";
      if (!isStructured) {
        const initialContent = formatModuleContent(module.content).trim();
        const isHtml = initialContent.includes('<') && initialContent.includes('>');
        htmlContent = isHtml ? initialContent : marked.parse(initialContent) as string;
      }

      setEditCache({
        ...editCache,
        [moduleNum]: {
          title: module.moduleTitle,
          content: htmlContent,
          knowledgeCheck: module.knowledgeCheck ? JSON.parse(JSON.stringify(module.knowledgeCheck)) : { question: "", options: { A: "", B: "", C: "", D: "" }, correctAnswer: "A", feedback: { correct: "", incorrect: "" } },
          flashcards: module.flashcards ? JSON.parse(JSON.stringify(module.flashcards)) : [],
          interactiveBlock: typeof module.content === 'object' && module.content?.interactiveBlock
            ? JSON.parse(JSON.stringify(module.content.interactiveBlock))
            : null,
        },
      });
    }
  };

  const saveModule = async (moduleNum: number, moduleIdx: number) => {
    const cache = editCache[moduleNum];
    if (!cache) return;

    if (hasActiveRequest) return;
    setSavingModuleNum(moduleNum);
    setUiNotice(null);
    try {
      const updated = { ...courseData } as any;
      updated.modules = [...updated.modules];
      updated.modules[moduleIdx] = {
        ...updated.modules[moduleIdx],
        moduleTitle: cache.title,
        content: (() => {
          const existingContent =
            typeof updated.modules[moduleIdx].content === 'object' && updated.modules[moduleIdx].content !== null
              ? updated.modules[moduleIdx].content
              : {};
          const hasSections =
            Array.isArray(existingContent.sections) && existingContent.sections.length > 0;
          const updatedInteractiveBlock =
            cache.interactiveBlock && !cache.interactiveBlock.__jsonError
              ? cache.interactiveBlock.data
                ? { type: cache.interactiveBlock.type, data: cache.interactiveBlock.data }
                : { type: cache.interactiveBlock.type }
              : (existingContent.interactiveBlock ?? null);
          if (hasSections) {
            // Module has structured sections — preserve them entirely so the xAPI
            // generator can render its full layout (audio, continue buttons, IB injection).
            // Writing html here causes the generator to short-circuit and dump flat HTML.
            return {
              ...existingContent,
              interactiveBlock: updatedInteractiveBlock,
            };
          }
          // No sections (raw/legacy module) — safe to write html directly.
          return {
            ...existingContent,
            html: cache.content,
            interactiveBlock: updatedInteractiveBlock,
          };
        })(),
        knowledgeCheck: cache.knowledgeCheck,
        flashcards: cache.flashcards,
      };

      // Ensure we don't accidentally leave __jsonError in the actual saved block
      if (updated.modules[moduleIdx].content?.interactiveBlock?.__jsonError !== undefined) {
        delete updated.modules[moduleIdx].content.interactiveBlock.__jsonError;
      }
      await saveCourse(updated);
      setEditModules({ ...editModules, [moduleNum]: false });
      setUiNotice({ type: "success", text: `Module ${moduleNum} changes saved.` });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Failed to save module: ${err?.message || "Unknown error"}` });
    } finally {
      setSavingModuleNum(null);
    }
  };

  return (
    <div>
      {/* ── Course Preview Hero Banner ── */}
      <div className="preview-hero">
        <div className="preview-hero-pill">{hasModules ? "Course Preview" : "Outline Preview"}</div>
        <h1>{courseData.course?.title || courseData.outline?.courseTitle || "Course Overview"}</h1>
        <p className="preview-hero-sub">
          Preview your course content below. Edit modules, adjust audio, and export when ready.
        </p>
        <div className="preview-hero-badges">
          <span className="preview-badge">
            <span className="preview-badge-icon">📚</span>
            {modules.length} Module{modules.length !== 1 ? "s" : ""}
          </span>
          <span className="preview-badge">
            <span className="preview-badge-icon">🌐</span>
            {courseData.course?.courseLanguage || "English"}
          </span>
          {courseData.course?.courseLevel && (
            <span className="preview-badge">
              <span className="preview-badge-icon">📊</span>
              {courseData.course.courseLevel}
            </span>
          )}
        </div>
        <div className="preview-hero-actions">
          <button type="button" onClick={startNewCourse}>
            Create New Course
          </button>
        </div>
      </div>

      {/* ── Two-Column Course Overview ── */}
      <div className="preview-overview">
        {/* Left Column: About + Objectives */}
        <div className="preview-about">
          <h2 className="preview-about-title">About this Course</h2>
          <p className="preview-description">
            {courseData.course?.description || courseData.outline?.courseDescription || "No description available."}
          </p>

          {(courseData.course?.overview || courseData.outline?.courseOverview) && (
            <div style={{ marginBottom: 16, color: "#475569", lineHeight: 1.7, fontSize: "0.92rem" }}>
              <ReactMarkdown>{courseData.course?.overview || courseData.outline?.courseOverview}</ReactMarkdown>
            </div>
          )}

          {(courseData.course?.learningObjectives || courseData.outline?.courseLearningObjectives) && (
            <>
              <h3 className="preview-objectives-title">What You&apos;ll Learn</h3>
              <ul className="preview-objectives">
                {(courseData.course?.learningObjectives || courseData.outline?.courseLearningObjectives || []).map((obj: string, idx: number) => (
                  <li key={idx}>{obj}</li>
                ))}
              </ul>
            </>
          )}
        </div>

        {/* Right Column: Course Outline */}
        {hasModules && (
          <div className="preview-outline-card">
            <h2 className="preview-outline-title">Course Outline</h2>
            <div className="preview-module-list">
              {modules.map((module: any, mIdx: number) => {
                const mNum = module.moduleNumber || mIdx + 1;
                return (
                  <a
                    key={mNum}
                    href={`#module-${mNum}`}
                    className="preview-module-row"
                    onClick={(e) => {
                      e.preventDefault();
                      document.getElementById(`module-${mNum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
                      setCollapsedModules((prev) => ({ ...prev, [mNum]: false }));
                    }}
                  >
                    <span className="preview-module-num">{mNum}</span>
                    <span className="preview-module-info">
                      <span className="preview-module-name">{module.moduleTitle}</span>
                    </span>
                    <span className="preview-module-time">
                      {module.estimatedTime && module.estimatedTime !== "N/A" ? module.estimatedTime : estimateReadingTime(module)}
                    </span>
                  </a>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {courseData.abbreviations && Object.keys(courseData.abbreviations).length > 0 && (
        <div className="glossary-box">
          <div className="glossary-header">
            <span>Key Terms & Abbreviations</span>
            <span className="glossary-count">{Object.keys(courseData.abbreviations).length} terms</span>
          </div>
          <div className="glossary-chips">
            {Object.entries(courseData.abbreviations).map(([abbr, fullForm]) => (
              <div key={abbr} className="glossary-chip">
                <span className="chip-abbr">{abbr}</span>
                <span className="chip-sep">·</span>
                <span className="chip-full">{fullForm as string}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {uiNotice && (
        <div className={`notice ${uiNotice.type}`} role={uiNotice.type === "error" ? "alert" : "status"}>
          {uiNotice.text}
        </div>
      )}

      {effectiveCourseId && !isGenerating && (
        <div className="card surface">
          <h2 className="section-title">Exports</h2>
          <div className="inline">
            {hasModules && (
              <button type="button" onClick={() => window.open(apiUrl(`/api/course/${effectiveCourseId}/download/xapi`), "_blank")}>
                Download xAPI ZIP
              </button>
            )}
            <button type="button" className={hasModules ? "secondary" : ""} onClick={() => window.open(apiUrl(`/api/course/${effectiveCourseId}/download/json`), "_blank")}>
              Download JSON
            </button>
            <button type="button" className="secondary" onClick={() => window.open(apiUrl(`/api/course/${effectiveCourseId}/download/pdf`), "_blank")}>
              Download PDF
            </button>
          </div>
        </div>
      )}

      {isGenerating && (
        <div className="card surface">
          <h2 className="section-title">Exports</h2>
          <p className="muted">Exports are locked while a new generation is running. They will unlock when the job completes.</p>
        </div>
      )}

      {!isOutlineOnly && (
        <div className="card surface">
          <h2 className="section-title">Audio Settings</h2>
          <div className="grid">
            <div className="field">
              <label>
                Language
                <InfoTip text="Audio voice language for preview and regeneration." />
              </label>
              <select
                value={audioSettings.language}
                onChange={(e) => setAudioSettings({ ...audioSettings, language: e.target.value })}
              >
                {COURSE_LANGUAGES.map((language) => (
                  <option key={language} value={language}>
                    {language}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>
                Voice Gender
                <InfoTip text="Voice style for module narration." />
              </label>
              <select
                value={audioSettings.gender}
                onChange={(e) => setAudioSettings({ ...audioSettings, gender: e.target.value })}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
            <div className="field">
              <label>
                Speed
                <InfoTip text="Playback speed. 1.0 is normal." />
              </label>
              <Slider
                aria-label="Audio Speed"
                step={0.1}
                minValue={0.5}
                maxValue={2.0}
                value={audioSettings.speed}
                onChange={(val) => setAudioSettings({ ...audioSettings, speed: Number(val) })}
                color="primary"
                size="md"
                showTooltip
                tooltipValueFormatOptions={{ style: "decimal", minimumFractionDigits: 1 }}
                startContent={<span style={{ fontSize: "0.75rem", color: "var(--muted, #94a3b8)", whiteSpace: "nowrap" }}>Slow</span>}
                endContent={<span style={{ fontSize: "0.75rem", color: "var(--muted, #94a3b8)", whiteSpace: "nowrap" }}>Fast</span>}
                getValue={(val) => `${Number(val).toFixed(1)}x`}
                className="max-w-md"
              />
            </div>
          </div>
          <div className="inline">
            <button type="button" className="secondary" disabled={hasActiveRequest} onClick={previewAudio}>
              {audioActionBusy === "preview" ? "Generating Preview..." : "Preview Voice"}
            </button>
            <button type="button" disabled={hasActiveRequest} onClick={regenerateAllAudio}>
              {audioActionBusy === "regenerate-all" ? "Regenerating..." : "Regenerate All Audio"}
            </button>
          </div>
          {previewUrl && <audio controls src={previewUrl} style={{ display: "block", marginTop: 12 }} />}
        </div>
      )}

      {modules.length === 0 && courseData.outline && (
        <OutlineEditor
          courseData={courseData}
          saveCourse={saveCourse}
          setUiNotice={setUiNotice}
        />
      )}

      {modules.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", margin: "4px 0 8px 0" }}>
          <span style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--muted)" }}>
            {modules.length} Module{modules.length !== 1 ? "s" : ""}
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="secondary"
              style={{ fontSize: "0.8rem", padding: "5px 12px" }}
              onClick={() =>
                setCollapsedModules(
                  Object.fromEntries(modules.map((m: any, i: number) => [m.moduleNumber || i + 1, false]))
                )
              }
            >
              Expand All
            </button>
            <button
              type="button"
              className="secondary"
              style={{ fontSize: "0.8rem", padding: "5px 12px" }}
              onClick={() =>
                setCollapsedModules(
                  Object.fromEntries(modules.map((m: any, i: number) => [m.moduleNumber || i + 1, true]))
                )
              }
            >
              Collapse All
            </button>
          </div>
        </div>
      )}

      {modules.map((module: any, index: number) => {
        const moduleNum = module.moduleNumber || index + 1;
        const editing = editModules[moduleNum];
        const cache = editCache[moduleNum] || {};
        const audioFile = fileNameFromPath(module.audioPath);
        const audioUrl = audioFile ? apiUrl(`/api/media/${audioFile}`) : null;
        const audioChunks: string[] = Array.isArray(module.audioPaths) ? module.audioPaths : [];
        const imageFile =
          module.imagePath && !/^data:/i.test(module.imagePath) && !/^https?:\/\//i.test(module.imagePath)
            ? fileNameFromPath(module.imagePath)
            : null;
        const imageUrl = resolveMediaUrl(module.imagePath);
        const imagePreviewUrl = imageUrl ? `${imageUrl}${module._imgTs ? `?t=${module._imgTs}` : ""}` : null;

        return (
          <div
            className={`module-card${dragOverModule === moduleNum && draggedModule !== moduleNum ? " drag-over" : ""}`}
            key={moduleNum}
            id={`module-${moduleNum}`}
            draggable
            onDragStart={() => setDraggedModule(moduleNum)}
            onDragOver={(e) => { e.preventDefault(); setDragOverModule(moduleNum); }}
            onDrop={() => { if (draggedModule !== null) reorderModules(draggedModule, moduleNum); setDraggedModule(null); setDragOverModule(null); }}
            onDragEnd={() => { setDraggedModule(null); setDragOverModule(null); }}
          >
            <div className="module-accent-strip" />
            <div
              className="module-header"
              onClick={() => toggleCollapse(moduleNum)}
              aria-expanded={!collapsedModules[moduleNum]}
            >
              <span onClick={(e) => e.stopPropagation()} style={{ cursor: "grab", color: "var(--muted)", fontSize: "1.1rem", lineHeight: 1, padding: "0 4px", flexShrink: 0 }} title="Drag to reorder">⠿</span>
              <span className="module-num-badge">{String(moduleNum).padStart(2, "0")}</span>
              <span className="module-title-text" title={module.moduleTitle}>
                {truncateTitle(editing ? (cache.title || module.moduleTitle) : module.moduleTitle, 6)}
              </span>
              <div className="inline" style={{ gap: 8 }} onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="secondary"
                  disabled={hasActiveRequest}
                  onClick={() => { void regenerateModule(moduleNum); }}
                  style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                >
                  {moduleActionBusy === moduleNum ? "Regenerating..." : "Regenerate"}
                </button>
                <button
                  type="button"
                  className="secondary"
                  disabled={hasActiveRequest}
                  onClick={() => toggleEdit(moduleNum, module)}
                  style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                >
                  {editing ? "Cancel" : "Edit"}
                </button>
                {editing && <span style={{ fontSize: "0.82rem", background: "rgba(27,90,166,0.1)", color: "var(--accent)", padding: "4px 10px", borderRadius: "100px", fontWeight: 600 }}>💡 Press Enter to save</span>}
              </div>
              <ChevronDown
                size={18}
                className={`module-collapse-icon${collapsedModules[moduleNum] ? "" : " open"}`}
              />
            </div>

            {!collapsedModules[moduleNum] && (
              <div className="module-body">
                {editing ? (
                  <>
                    <div className="field">
                      <label>Module Title</label>
                      <input
                        value={cache.title || ""}
                        onChange={(e) =>
                          setEditCache({
                            ...editCache,
                            [moduleNum]: { ...cache, title: e.target.value },
                          })
                        }
                        onKeyDown={(e) => { if (e.key === 'Enter') { void saveModule(moduleNum, index); } }}
                      />
                    </div>
                    <div className="field">
                      <label>Module Content</label>
                      <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                        {modules.find((m: any) => (m.moduleNumber || 0) === moduleNum)?.content?.sections?.length > 0 ? (
                          <span style={{ display: "block", marginTop: 4, color: "var(--accent)", fontWeight: 600 }}>
                            Note: This module has structured sections. Please edit content directly in the sections view below instead. This content box is disabled to avoid corrupting sections.
                          </span>
                        ) : (
                          "Edit the module content using the rich text editor."
                        )}
                      </p>
                      {modules.find((m: any) => (m.moduleNumber || 0) === moduleNum)?.content?.sections?.length > 0 ? (
                        <div className="editor-container" style={{ opacity: 0.6, pointerEvents: "none" }}>
                          <ReactQuill
                            theme="snow"
                            value={"Expand the module to edit individual sections."}
                            readOnly={true}
                            style={{ background: "#f8fafc", color: "#64748b", fontFamily: "var(--font-sans)" }}
                          />
                        </div>
                      ) : (
                        <div className="editor-container">
                          <ReactQuill
                            theme="snow"
                            value={cache.content || ""}
                            onChange={(val) =>
                              setEditCache({
                                ...editCache,
                                [moduleNum]: { ...cache, content: val },
                              })
                            }
                            style={{ background: "#fff", color: "#000", fontFamily: "var(--font-sans)" }}
                          />
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <h3>{module.moduleTitle}</h3>
                    <p><strong>Estimated Time:</strong> {module.estimatedTime && module.estimatedTime !== "N/A" ? module.estimatedTime : estimateReadingTime(module)}</p>

                    {module.content && (!module.content.sections || module.content.sections.length === 0) && (
                      <div style={{ marginTop: "20px" }}>
                        <h4>Content</h4>
                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{formatModuleContent(module.content)}</ReactMarkdown>
                      </div>
                    )}

                    {(!module.content?.sections || module.content.sections.length === 0) && (
                      <div style={{ marginTop: "16px", padding: "12px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                          {audioUrl ? (
                            <audio controls src={audioUrl} style={{ height: "36px", flex: 1, minWidth: "250px" }} />
                          ) : (
                            <div style={{ fontSize: "0.9rem", color: "#64748b", flex: 1, minWidth: "250px" }}>No module-level audio</div>
                          )}
                          <button
                            type="button"
                            className="secondary"
                            disabled={hasActiveRequest}
                            onClick={() => void regenerateModuleAudio(moduleNum)}
                            style={{ margin: 0, fontSize: "0.85rem", padding: "6px 14px", height: "auto" }}
                          >
                            {moduleActionBusy === moduleNum ? "Generating..." : audioUrl ? "Regenerate Audio" : "Generate Audio"}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {module.content?.sections && module.content.sections.length > 0 && (
                  <div style={{ marginTop: "24px", display: "flex", flexDirection: "column", gap: "24px" }}>
                    {module.content.sections.map((section: any, sIdx: number) => {
                      const sKey = `${moduleNum}-${sIdx}`;
                      const targetSectionCache = sectionEditCache[sKey] || {};
                      const sEditing = editSections[sKey];
                      const sAudioFile = fileNameFromPath(section.audioPath);
                      const sAudioUrl = sAudioFile ? apiUrl(`/api/media/${sAudioFile}?cb=${audioCacheBuster}`) : null;

                      return (
                        <div key={sIdx} id={`section-${moduleNum}-${sIdx}`} style={{ padding: "20px", background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", boxShadow: "0 2px 8px rgba(0,0,0,0.02)" }}>
                          {sEditing ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                              <div className="field" style={{ margin: 0 }}>
                                <label style={{ fontSize: "1.1rem", fontWeight: 600 }}>Section Title</label>
                                <input
                                  value={targetSectionCache.sectionTitle || ""}
                                  onChange={(e) =>
                                    setSectionEditCache({
                                      ...sectionEditCache,
                                      [sKey]: { ...targetSectionCache, sectionTitle: e.target.value },
                                    })
                                  }
                                />
                              </div>

                              <div className="field" style={{ margin: 0 }}>
                                <label style={{ fontSize: "1.05rem", fontWeight: 600 }}>Introduction / Content</label>
                                <div className="editor-container" style={{ border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden" }}>
                                  <ReactQuill
                                    theme="snow"
                                    value={targetSectionCache.content || ""}
                                    onChange={(val) => {
                                      // Prevent infinite loop by strictly checking if the stripped tags value actually changed
                                      const oldVal = targetSectionCache.content || "";
                                      if (val !== oldVal && val !== "<p><br></p>" && oldVal !== "<p><br></p>") {
                                        setSectionEditCache(prev => ({
                                          ...prev,
                                          [sKey]: { ...prev[sKey], content: val },
                                        }));
                                      } else if (val === "<p><br></p>" && oldVal !== "") {
                                        setSectionEditCache(prev => ({
                                          ...prev,
                                          [sKey]: { ...prev[sKey], content: "" },
                                        }));
                                      }
                                    }}
                                  />
                                </div>
                              </div>

                              {targetSectionCache.concepts && targetSectionCache.concepts.length > 0 && (
                                <div style={{ padding: "16px", background: "#f8fafc", borderRadius: "12px", border: "1px solid #e2e8f0" }}>
                                  <h4 style={{ margin: "0 0 16px 0", fontSize: "1.05rem", color: "#1e293b", display: "flex", justifyContent: "space-between" }}>
                                    <span>Concepts</span>
                                    <span style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 400 }}>{targetSectionCache.concepts.length} items</span>
                                  </h4>
                                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                                    {targetSectionCache.concepts.map((concept: any, cIdx: number) => (
                                      <div key={cIdx} style={{ background: "#fff", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.02)" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                                          <span style={{ fontWeight: 600, color: "#475569", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Concept {cIdx + 1}</span>
                                          <button
                                            type="button"
                                            className="secondary"
                                            style={{ padding: "4px 8px", fontSize: "0.75rem", height: "auto", margin: 0, color: "#ef4444", borderColor: "#fca5a5", background: "#fef2f2" }}
                                            onClick={() => {
                                              const newConcepts = [...targetSectionCache.concepts];
                                              newConcepts.splice(cIdx, 1);
                                              setSectionEditCache({
                                                ...sectionEditCache,
                                                [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                              });
                                            }}
                                          >
                                            Remove
                                          </button>
                                        </div>
                                        <div className="field" style={{ margin: "0 0 12px 0" }}>
                                          <label style={{ fontSize: "0.9rem" }}>Concept Title</label>
                                          <input
                                            value={concept.conceptTitle || ""}
                                            onChange={(e) => {
                                              const newConcepts = [...targetSectionCache.concepts];
                                              newConcepts[cIdx] = { ...concept, conceptTitle: e.target.value };
                                              setSectionEditCache({
                                                ...sectionEditCache,
                                                [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                              });
                                            }}
                                          />
                                        </div>
                                        <div className="field" style={{ margin: 0 }}>
                                          <label style={{ fontSize: "0.9rem" }}>Explanation</label>
                                          <div className="editor-container" style={{ borderRadius: "6px", overflow: "hidden" }}>
                                            <ReactQuill
                                              theme="snow"
                                              value={concept.explanation || ""}
                                              onChange={(val) => {
                                                const oldVal = concept.explanation || "";
                                                if (val !== oldVal && val !== "<p><br></p>" && oldVal !== "<p><br></p>") {
                                                  const newConcepts = [...targetSectionCache.concepts];
                                                  newConcepts[cIdx] = { ...concept, explanation: val };
                                                  setSectionEditCache(prev => ({
                                                    ...prev,
                                                    [sKey]: { ...prev[sKey], concepts: newConcepts },
                                                  }));
                                                } else if (val === "<p><br></p>" && oldVal !== "") {
                                                  const newConcepts = [...targetSectionCache.concepts];
                                                  newConcepts[cIdx] = { ...concept, explanation: "" };
                                                  setSectionEditCache(prev => ({
                                                    ...prev,
                                                    [sKey]: { ...prev[sKey], concepts: newConcepts },
                                                  }));
                                                }
                                              }}
                                            />
                                          </div>
                                        </div>

                                        <div style={{ marginTop: "16px", padding: "16px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px" }}>
                                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                                            <span style={{ fontWeight: 600, color: "#166534", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "6px" }}>
                                              <Lightbulb size={16} /> Real-World Scenario
                                            </span>
                                            {!concept.scenario && (
                                              <button
                                                type="button"
                                                className="secondary"
                                                style={{ padding: "4px 8px", fontSize: "0.75rem", height: "auto", margin: 0, background: "#fff", borderColor: "#bbf7d0", color: "#166534" }}
                                                onClick={() => {
                                                  const newConcepts = [...targetSectionCache.concepts];
                                                  newConcepts[cIdx] = { ...concept, scenario: { description: "", whatToDo: "", whyItMatters: "", howToPrevent: "" } };
                                                  setSectionEditCache({
                                                    ...sectionEditCache,
                                                    [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                                  });
                                                }}
                                              >
                                                Add Scenario
                                              </button>
                                            )}
                                          </div>

                                          {concept.scenario && (
                                            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                                              <div className="field" style={{ margin: 0 }}>
                                                <label style={{ fontSize: "0.85rem", color: "#166534" }}>Scenario Description</label>
                                                <textarea
                                                  rows={2}
                                                  style={{ padding: "8px", fontSize: "0.9rem", borderColor: "#bbf7d0" }}
                                                  value={concept.scenario.description || ""}
                                                  onChange={(e) => {
                                                    const newConcepts = [...targetSectionCache.concepts];
                                                    newConcepts[cIdx] = {
                                                      ...concept,
                                                      scenario: { ...concept.scenario, description: e.target.value }
                                                    };
                                                    setSectionEditCache({
                                                      ...sectionEditCache,
                                                      [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                                    });
                                                  }}
                                                />
                                              </div>
                                              <div className="field" style={{ margin: 0 }}>
                                                <label style={{ fontSize: "0.85rem", color: "#166534" }}>What to do</label>
                                                <textarea
                                                  rows={2}
                                                  style={{ padding: "8px", fontSize: "0.9rem", borderColor: "#bbf7d0" }}
                                                  value={concept.scenario.whatToDo || ""}
                                                  onChange={(e) => {
                                                    const newConcepts = [...targetSectionCache.concepts];
                                                    newConcepts[cIdx] = {
                                                      ...concept,
                                                      scenario: { ...concept.scenario, whatToDo: e.target.value }
                                                    };
                                                    setSectionEditCache({
                                                      ...sectionEditCache,
                                                      [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                                    });
                                                  }}
                                                />
                                              </div>
                                              <div className="field" style={{ margin: 0 }}>
                                                <label style={{ fontSize: "0.85rem", color: "#166534" }}>Why it matters</label>
                                                <textarea
                                                  rows={2}
                                                  style={{ padding: "8px", fontSize: "0.9rem", borderColor: "#bbf7d0" }}
                                                  value={concept.scenario.whyItMatters || ""}
                                                  onChange={(e) => {
                                                    const newConcepts = [...targetSectionCache.concepts];
                                                    newConcepts[cIdx] = {
                                                      ...concept,
                                                      scenario: { ...concept.scenario, whyItMatters: e.target.value }
                                                    };
                                                    setSectionEditCache({
                                                      ...sectionEditCache,
                                                      [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                                    });
                                                  }}
                                                />
                                              </div>
                                              <div className="field" style={{ margin: 0 }}>
                                                <label style={{ fontSize: "0.85rem", color: "#166534" }}>How to prevent</label>
                                                <textarea
                                                  rows={2}
                                                  style={{ padding: "8px", fontSize: "0.9rem", borderColor: "#bbf7d0" }}
                                                  value={concept.scenario.howToPrevent || ""}
                                                  onChange={(e) => {
                                                    const newConcepts = [...targetSectionCache.concepts];
                                                    newConcepts[cIdx] = {
                                                      ...concept,
                                                      scenario: { ...concept.scenario, howToPrevent: e.target.value }
                                                    };
                                                    setSectionEditCache({
                                                      ...sectionEditCache,
                                                      [sKey]: { ...targetSectionCache, concepts: newConcepts },
                                                    });
                                                  }}
                                                />
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                                <button
                                  type="button"
                                  disabled={hasActiveRequest}
                                  onClick={() => void saveSectionEdit(moduleNum, index, sIdx)}
                                  style={{ padding: "10px 20px" }}
                                >
                                  {sectionActionBusy === `${moduleNum}-${sIdx}` ? "Saving..." : "Save Content Changes"}
                                </button>
                                <button
                                  type="button"
                                  className="secondary"
                                  disabled={hasActiveRequest}
                                  onClick={() => toggleSectionEdit(moduleNum, sIdx, section)}
                                >
                                  Discard Changes
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="section-preview" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e2e8f0", paddingBottom: "12px" }}>
                                <h4 style={{ margin: 0, fontSize: "1.1rem", color: "#1e293b", fontWeight: 700 }}>{section.sectionTitle}</h4>
                                <button type="button" className="secondary" style={{ fontSize: "0.85rem", padding: "6px 16px", height: "auto", margin: 0, borderRadius: "6px" }} disabled={hasActiveRequest} onClick={() => toggleSectionEdit(moduleNum, sIdx, section)}>
                                  Edit Section
                                </button>
                              </div>

                              {section.content && (
                                <div className="section-content-body" style={{ color: "#334155", lineHeight: 1.6, fontSize: "0.95rem" }}>
                                  <ReactMarkdown rehypePlugins={[rehypeRaw]}>{section.content}</ReactMarkdown>
                                </div>
                              )}

                              {section.concepts && section.concepts.length > 0 && (
                                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "8px" }}>
                                  {section.concepts.map((concept: any, cIdx: number) => (
                                    <div key={cIdx} style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px" }}>
                                      <h5 style={{ margin: "0 0 8px 0", fontSize: "1.05rem", color: "#0f172a" }}>{concept.conceptTitle}</h5>
                                      <div style={{ color: "#475569", fontSize: "0.95rem", lineHeight: 1.6 }}>
                                        <ReactMarkdown rehypePlugins={[rehypeRaw]}>{concept.explanation}</ReactMarkdown>
                                      </div>
                                      {concept.scenario && (
                                        <div style={{ marginTop: "16px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "8px", padding: "16px" }}>
                                          <div style={{ fontWeight: 600, color: "#166534", fontSize: "0.9rem", display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                                            <Lightbulb size={18} /> Real-World Scenario
                                          </div>
                                          <div style={{ display: "flex", flexDirection: "column", gap: "8px", color: "#15803d", fontSize: "0.9rem" }}>
                                            {concept.scenario.description && <div><strong style={{ opacity: 0.9 }}>Scenario:</strong> {concept.scenario.description}</div>}
                                            {concept.scenario.whatToDo && <div><strong style={{ opacity: 0.9 }}>Action:</strong> {concept.scenario.whatToDo}</div>}
                                            {concept.scenario.whyItMatters && <div><strong style={{ opacity: 0.9 }}>Why it matters:</strong> {concept.scenario.whyItMatters}</div>}
                                            {concept.scenario.howToPrevent && <div><strong style={{ opacity: 0.9 }}>How to prevent:</strong> {concept.scenario.howToPrevent}</div>}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}

                              <div style={{ marginTop: "16px", padding: "12px", background: "#f1f5f9", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                                  {sAudioUrl ? (
                                    <audio controls src={sAudioUrl} style={{ height: "36px", flex: 1, minWidth: "250px" }} />
                                  ) : (
                                    <div style={{ fontSize: "0.9rem", color: "#64748b", flex: 1, minWidth: "250px" }}>No section audio</div>
                                  )}
                                  <button
                                    type="button"
                                    className="secondary"
                                    disabled={hasActiveRequest}
                                    onClick={() => void regenerateSectionAudio(moduleNum, sIdx)}
                                    style={{ margin: 0, fontSize: "0.85rem", padding: "6px 14px", height: "auto", borderRadius: "6px" }}
                                  >
                                    {sectionActionBusy === `${moduleNum}-${sIdx}-audio` ? "Generating..." : sAudioUrl ? "Regenerate Audio" : "Generate Audio"}
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}


                {/* Audio chunks for section-based modules */}
                {module.content?.sections && module.content.sections.length > 0 && audioUrl && (
                  <div style={{ marginTop: 16 }}>
                    <h4>Audio</h4>
                    <audio controls src={audioUrl} />
                    {audioChunks.length > 1 && (
                      <div style={{ marginTop: 8 }}>
                        {audioChunks.map((chunkPath: string, idx: number) => {
                          const chunkFile = fileNameFromPath(chunkPath);
                          if (!chunkFile) return null;
                          return (
                            <div key={`${moduleNum}-chunk-${idx}`} style={{ marginBottom: 6 }}>
                              <div className="muted">Chunk {idx + 1}</div>
                              <audio controls src={resolveMediaUrl(chunkPath) || apiUrl(`/api/media/${chunkFile}`)} />
                            </div>
                          );
                        })}
                      </div>
                    )}
                    <button type="button" className="secondary" disabled={hasActiveRequest} onClick={() => void regenerateModuleAudio(moduleNum)}>
                      {moduleActionBusy === moduleNum ? "Regenerating..." : "Regenerate Audio"}
                    </button>
                  </div>
                )}
                {module.content?.sections && module.content.sections.length > 0 && !audioUrl && audioChunks.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <h4>Audio</h4>
                    {audioChunks.map((chunkPath: string, idx: number) => {
                      const chunkFile = fileNameFromPath(chunkPath);
                      if (!chunkFile) return null;
                      return (
                        <div key={`${moduleNum}-chunk-only-${idx}`} style={{ marginBottom: 6 }}>
                          <div className="muted">Chunk {idx + 1}</div>
                          <audio controls src={resolveMediaUrl(chunkPath) || apiUrl(`/api/media/${chunkFile}`)} />
                        </div>
                      );
                    })}
                  </div>
                )}

                {editIB[moduleNum] ? (
                  <div style={{ marginTop: "32px", padding: "20px", background: "#f8fafc", border: "1px solid var(--border)", borderRadius: "12px" }}>
                    {cache.interactiveBlock && (
                      <div className="field" style={{ border: "1px solid var(--border)", padding: "16px", borderRadius: "8px", marginTop: "16px" }}>
                        <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "flex", justifyContent: "space-between" }}>
                          <span>Interactive Block ({cache.interactiveBlock.type})</span>
                          <button type="button" className="secondary" style={{ padding: "4px 8px", fontSize: "0.8rem", height: "auto" }} onClick={() => setEditCache({ ...editCache, [moduleNum]: { ...cache, interactiveBlock: null } })}>Remove Block</button>
                        </label>
                        <div className="muted" style={{ fontSize: "0.85rem", marginBottom: 12 }}>
                          <p>Edit the data payload for this interactive block. Ensure valid JSON.</p>
                          {cache.interactiveBlock.type === "tabs" && <p className="text-gray-400 mt-1">Schema expected: {`{ "tabs": [{ "title": "...", "content": "..." }] }`}</p>}
                          {cache.interactiveBlock.type === "accordion" && <p className="text-gray-400 mt-1">Schema expected: {`{ "items": [{ "question": "...", "answer": "..." }] }`}</p>}
                          {cache.interactiveBlock.type === "flipcard" && <p className="text-gray-400 mt-1">Schema expected: {`{ "cards": [{ "front": "...", "back": "..." }] }`}</p>}
                          {cache.interactiveBlock.type === "note" && <p className="text-gray-400 mt-1">Schema expected: {`{ "variant": "tip|warning|important|info", "text": "..." }`}</p>}
                          {cache.interactiveBlock.type === "table" && <p className="text-gray-400 mt-1">Schema expected: {`{ "headers": ["A", "B"], "rows": [["1", "2"]] }`}</p>}
                        </div>
                        {cache.interactiveBlock.__jsonError && (
                          <div style={{ color: "var(--danger, #ef4444)", fontSize: "0.85rem", marginBottom: "8px", background: "rgba(239,68,68,0.1)", padding: "8px", borderRadius: "4px", border: "1px solid rgba(239,68,68,0.2)" }}>
                            Invalid JSON syntax. Changes won't save until fixed.
                          </div>
                        )}
                        <textarea
                          rows={12}
                          style={{ fontFamily: "monospace", fontSize: "0.9rem", lineHeight: 1.4, borderColor: cache.interactiveBlock.__jsonError ? "var(--danger, #ef4444)" : "var(--border)" }}
                          defaultValue={JSON.stringify(cache.interactiveBlock.data, null, 2)}
                          onChange={(e) => {
                            try {
                              const parsed = JSON.parse(e.target.value);
                              setEditCache({
                                ...editCache,
                                [moduleNum]: { ...cache, interactiveBlock: { ...cache.interactiveBlock, data: parsed, __jsonError: false } }
                              });
                            } catch (err) {
                              setEditCache({
                                ...editCache,
                                [moduleNum]: { ...cache, interactiveBlock: { ...cache.interactiveBlock, __jsonError: true } }
                              });
                            }
                          }}
                        />
                      </div>
                    )}
                    {!cache.interactiveBlock && (
                      <div className="field" style={{ border: "1px solid var(--border)", padding: "16px", borderRadius: "8px", marginTop: "16px" }}>
                        <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "block" }}>Interactive Block</label>
                        <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 12 }}>
                          No interactive block on this module. Select a type to add one.
                        </p>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <select
                            value={newIbType[moduleNum] || "tabs"}
                            onChange={(e) => setNewIbType({ ...newIbType, [moduleNum]: e.target.value })}
                            style={{ padding: "8px", borderRadius: "4px", border: "1px solid var(--border)", background: "var(--background)", color: "var(--foreground)", fontSize: "0.95rem" }}
                          >
                            <option value="tabs">Tabs</option>
                            <option value="accordion">Accordion</option>
                            <option value="note">Note</option>
                            <option value="table">Table</option>
                            <option value="flipcard">Flipcard</option>
                          </select>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => {
                              const type = newIbType[moduleNum] || "tabs";
                              const defaults: Record<string, any> = {
                                tabs: { tabs: [{ title: "Tab 1", content: "Content here." }] },
                                accordion: { items: [{ question: "Question?", answer: "Answer here." }] },
                                note: { variant: "info", text: "Note text here." },
                                table: { headers: ["Column A", "Column B"], rows: [["Row 1A", "Row 1B"]] },
                                flipcard: { cards: [{ front: "Term", back: "Definition here." }] },
                              };
                              setEditCache({
                                ...editCache,
                                [moduleNum]: { ...cache, interactiveBlock: { type, data: defaults[type], __jsonError: false } }
                              });
                            }}
                          >
                            + Add Interactive Block
                          </button>
                        </div>
                      </div>
                    )}
                    <div className="field" style={{ border: "1px solid var(--border)", padding: "16px", borderRadius: "8px", marginTop: "16px" }}>
                      <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "block" }}>Knowledge Check</label>
                      <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 12 }}>
                        Each module has one multiple-choice question to verify understanding.
                      </p>
                      <div className="field" style={{ marginBottom: "16px" }}>
                        <label>Question</label>
                        <input
                          value={cache.knowledgeCheck?.question || ""}
                          onChange={(e) => setEditCache({
                            ...editCache,
                            [moduleNum]: { ...cache, knowledgeCheck: { ...cache.knowledgeCheck, question: e.target.value } }
                          })}
                          onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
                        />
                      </div>
                      <div className="responsive-two-col" style={{ marginBottom: "16px" }}>
                        {['A', 'B', 'C', 'D'].map((opt) => (
                          <div className="field" key={opt} style={{ margin: 0 }}>
                            <label>Option {opt}</label>
                            <input
                              value={cache.knowledgeCheck?.options?.[opt] || ""}
                              onChange={(e) => setEditCache({
                                ...editCache,
                                [moduleNum]: {
                                  ...cache,
                                  knowledgeCheck: {
                                    ...cache.knowledgeCheck,
                                    options: { ...cache.knowledgeCheck?.options, [opt]: e.target.value }
                                  }
                                }
                              })}
                              onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
                            />
                          </div>
                        ))}
                      </div>
                      <div className="field" style={{ marginBottom: "16px" }}>
                        <label>Correct Answer</label>
                        <select
                          value={cache.knowledgeCheck?.correctAnswer || "A"}
                          onChange={(e) => setEditCache({
                            ...editCache,
                            [moduleNum]: { ...cache, knowledgeCheck: { ...cache.knowledgeCheck, correctAnswer: e.target.value } }
                          })}
                          style={{ padding: "8px", borderRadius: "4px", border: "1px solid var(--border)", background: "var(--background)", color: "var(--foreground)", width: "100%", maxWidth: "200px", display: "block" }}
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
                            onChange={(e) => setEditCache({
                              ...editCache,
                              [moduleNum]: {
                                ...cache,
                                knowledgeCheck: {
                                  ...cache.knowledgeCheck,
                                  feedback: { ...cache.knowledgeCheck?.feedback, correct: e.target.value }
                                }
                              }
                            })}
                            onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
                          />
                        </div>
                        <div className="field" style={{ margin: 0 }}>
                          <label>Feedback (If Incorrect)</label>
                          <input
                            value={cache.knowledgeCheck?.feedback?.incorrect || ""}
                            onChange={(e) => setEditCache({
                              ...editCache,
                              [moduleNum]: {
                                ...cache,
                                knowledgeCheck: {
                                  ...cache.knowledgeCheck,
                                  feedback: { ...cache.knowledgeCheck?.feedback, incorrect: e.target.value }
                                }
                              }
                            })}
                            onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="field" style={{ border: "1px solid var(--border)", padding: "16px", borderRadius: "8px", marginTop: "16px", marginBottom: "24px" }}>
                      <label style={{ fontSize: "1.1rem", marginBottom: "12px", display: "block" }}>Interactive</label>
                      <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 16 }}>
                        Key terms and definitions for this module.
                      </p>
                      {(cache.flashcards || []).map((fc: any, fcIndex: number) => (
                        <div key={fc.id || fcIndex} className="responsive-flow-grid" style={{ marginBottom: "16px", alignItems: "flex-start", paddingBottom: "16px", borderBottom: fcIndex < (cache.flashcards.length - 1) ? "1px dashed var(--border)" : "none" }}>
                          <div className="field" style={{ flex: 1, margin: 0 }}>
                            <label>Front Context</label>
                            <input
                              value={fc.front || ""}
                              onChange={(e) => {
                                const newFc = [...(cache.flashcards || [])];
                                newFc[fcIndex] = { ...newFc[fcIndex], front: e.target.value };
                                setEditCache({ ...editCache, [moduleNum]: { ...cache, flashcards: newFc } });
                              }}
                              onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
                            />
                          </div>
                          <div className="field" style={{ flex: 1, margin: 0 }}>
                            <label>Back Truth</label>
                            <input
                              value={fc.back || ""}
                              onChange={(e) => {
                                const newFc = [...(cache.flashcards || [])];
                                newFc[fcIndex] = { ...newFc[fcIndex], back: e.target.value };
                                setEditCache({ ...editCache, [moduleNum]: { ...cache, flashcards: newFc } });
                              }}
                              onKeyDown={(e) => { if (e.key === 'Enter') void saveModule(moduleNum, index); }}
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
                              setEditCache({ ...editCache, [moduleNum]: { ...cache, flashcards: newFc } });
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
                          setEditCache({ ...editCache, [moduleNum]: { ...cache, flashcards: newFc } });
                        }}
                      >
                        + Add Interactive
                      </button>
                    </div>
                    <button
                      type="button"
                      disabled={hasActiveRequest}
                      onClick={() => {
                        void saveModule(moduleNum, index);
                      }}
                    >
                      {savingModuleNum === moduleNum ? "Saving..." : "Save Module"}
                    </button>                            <div style={{ marginTop: "24px" }}><button type="button" className="primary" onClick={() => saveModule(moduleNum, index).then(() => setEditIB({ ...editIB, [moduleNum]: false }))} disabled={hasActiveRequest}>{savingModuleNum === moduleNum ? "Saving..." : "Save Block"}</button><button type="button" className="secondary" onClick={() => setEditIB({ ...editIB, [moduleNum]: false })} disabled={hasActiveRequest} style={{ marginLeft: "8px", background: "transparent", color: "var(--text-muted)", border: "none", textDecoration: "underline" }}>Cancel</button></div>
                  </div>
                ) : (
                  <>
                    {module.content?.interactiveBlock && (
                      <div style={{ marginTop: "32px", marginBottom: "8px", padding: "20px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", borderLeft: "4px solid var(--accent, #1b5aa6)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}><div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent, #1b5aa6)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Interactive</span>
                          <span style={{ fontSize: "0.7rem", background: "var(--accent, #1b5aa6)", color: "#fff", padding: "2px 8px", borderRadius: "100px", fontWeight: 600 }}>{module.content.interactiveBlock.type}</span>
                        </div><button type="button" className="secondary tiny" style={{ fontSize: "0.75rem", padding: "4px 8px", height: "auto", margin: 0 }} onClick={() => { ensureEditCache(moduleNum, module); setEditIB({ ...editIB, [moduleNum]: true }); }}>Edit Block</button></div>
                        <InteractiveBlockPreview block={module.content.interactiveBlock} />
                      </div>
                    )}

                  </>
                )}
                {/* ── Module Image Section ── */}
                <div style={{ marginTop: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                    <h4 style={{ margin: 0 }}>Module Image</h4>
                  </div>
                  {imageRegen[moduleNum] ? (
                    <div style={{ width: "100%", maxWidth: 320, aspectRatio: "16/9", background: "var(--surface, #f8fafc)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", borderRadius: 8, border: "2px dashed var(--border, #e2e8f0)", marginTop: 8 }}>
                      <Loader2 size={28} style={{ animation: "spin 2s linear infinite", color: "var(--accent, #1b5aa6)", marginBottom: 12 }} />
                      <span style={{ fontSize: "0.85rem", color: "var(--accent, #1b5aa6)", fontWeight: 600 }}>Rendering high-quality image...</span>
                      <span style={{ fontSize: "0.75rem", color: "var(--muted, #64748b)", marginTop: 4 }}>This might take a moment.</span>
                    </div>
                  ) : imagePreviewUrl ? (
                    <>
                      <img
                        src={imagePreviewUrl}
                        alt={`Module ${moduleNum}`}
                        style={{ maxWidth: 320, borderRadius: 8, cursor: "zoom-in", display: "block" }}
                        onClick={() =>
                          setPreviewImage({
                            url: imagePreviewUrl,
                            title: module.moduleTitle || `Module ${moduleNum}`,
                            moduleNum,
                            moduleIndex: index,
                            filename: imageFile || `module-${moduleNum}-image.png`,
                          })
                        }
                        title="Click to preview full size"
                      />
                      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
                        <button
                          type="button"
                          className="secondary"
                          disabled={imageRegen[moduleNum] || hasActiveRequest}
                          onClick={() => void regenerateModuleImage(moduleNum, index)}
                          style={{ fontSize: "0.8rem", padding: "5px 12px", display: "flex", alignItems: "center", gap: 6 }}
                        >
                          <RefreshCw size={14} /> Regenerate
                        </button>
                        <button
                          type="button"
                          className="secondary"
                          disabled={imageEditBusy[moduleNum] || hasActiveRequest}
                          onClick={() => setImageEdit(prev => ({ ...prev, [moduleNum]: !prev[moduleNum] }))}
                          style={{ fontSize: "0.8rem", padding: "5px 12px", display: "flex", alignItems: "center", gap: 6 }}
                        >
                          <Edit2 size={14} /> Edit Image
                        </button>
                      </div>
                      {imageEdit[moduleNum] && (
                        <div style={{ marginTop: 10, padding: "12px", background: "var(--surface, #f8fafc)", border: "1px solid var(--border, #e2e8f0)", borderRadius: 8 }}>
                          <div style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: 6 }}>Describe the changes to make:</div>
                          <textarea
                            rows={2}
                            placeholder="e.g. Change the background to an outdoor park setting"
                            value={imageEditPrompt[moduleNum] || ""}
                            onChange={e => setImageEditPrompt(prev => ({ ...prev, [moduleNum]: e.target.value }))}
                            style={{ width: "100%", padding: "8px", borderRadius: 6, fontSize: "0.85rem", border: "1px solid var(--border, #e2e8f0)", resize: "vertical", fontFamily: "inherit", boxSizing: "border-box" }}
                          />
                          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                            <button
                              type="button"
                              disabled={imageEditBusy[moduleNum] || !imageEditPrompt[moduleNum]?.trim()}
                              onClick={() => void editModuleImage(moduleNum, index)}
                              style={{ fontSize: "0.8rem", padding: "5px 14px", display: "flex", alignItems: "center", gap: 6 }}
                            >
                              {imageEditBusy[moduleNum] ? <><Loader2 size={14} style={{ animation: "spin 2s linear infinite" }} /> Applying...</> : "Apply Edit"}
                            </button>
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => setImageEdit(prev => ({ ...prev, [moduleNum]: false }))}
                              style={{ fontSize: "0.8rem", padding: "5px 12px" }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: 10, background: "var(--surface, #f8fafc)", border: "1px dashed var(--border, #e2e8f0)", padding: "12px 16px", borderRadius: 8 }}>
                      <ImageIcon size={20} color="var(--muted, #64748b)" />
                      <span style={{ fontSize: "0.85rem", color: "var(--muted)", flex: 1 }}>No image generated</span>
                      <button
                        type="button"
                        className="secondary"
                        disabled={imageRegen[moduleNum] || hasActiveRequest}
                        onClick={() => void regenerateModuleImage(moduleNum, index)}
                        style={{ fontSize: "0.8rem", padding: "5px 12px", display: "flex", alignItems: "center", gap: 6 }}
                      >
                        <Wand2 size={14} /> Generate Image
                      </button>
                    </div>
                  )}
                </div>

                {editKC[moduleNum] ? (
                  <div style={{ marginTop: "32px", padding: "20px", background: "#f8fafc", border: "1px solid var(--border)", borderRadius: "12px" }}>
                    <div style={{ marginTop: "24px" }}><button type="button" className="primary" onClick={() => saveModule(moduleNum, index).then(() => setEditKC({ ...editKC, [moduleNum]: false }))} disabled={hasActiveRequest}>{savingModuleNum === moduleNum ? "Saving..." : "Save Check"}</button><button type="button" className="secondary" onClick={() => setEditKC({ ...editKC, [moduleNum]: false })} disabled={hasActiveRequest} style={{ marginLeft: "8px", background: "transparent", color: "var(--text-muted)", border: "none", textDecoration: "underline" }}>Cancel</button></div>
                  </div>
                ) : (
                  <>
                    {module.knowledgeCheck && (
                      <div style={{ marginTop: "32px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><h4>Knowledge Check</h4><button type="button" className="secondary tiny" style={{ fontSize: "0.75rem", padding: "4px 8px", height: "auto", margin: 0 }} onClick={() => { ensureEditCache(moduleNum, module); setEditKC({ ...editKC, [moduleNum]: true }); }}>Edit Quiz</button></div>
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

                  </>
                )}
                {editFC[moduleNum] ? (
                  <div style={{ marginTop: "32px", padding: "20px", background: "#f8fafc", border: "1px solid var(--border)", borderRadius: "12px" }}>
                    <div style={{ marginTop: "24px" }}><button type="button" className="primary" onClick={() => saveModule(moduleNum, index).then(() => setEditFC({ ...editFC, [moduleNum]: false }))} disabled={hasActiveRequest}>{savingModuleNum === moduleNum ? "Saving..." : "Save Cards"}</button><button type="button" className="secondary" onClick={() => setEditFC({ ...editFC, [moduleNum]: false })} disabled={hasActiveRequest} style={{ marginLeft: "8px", background: "transparent", color: "var(--text-muted)", border: "none", textDecoration: "underline" }}>Cancel</button></div>
                  </div>
                ) : (
                  <>
                    {module.flashcards && module.flashcards.length > 0 && (
                      <div style={{ marginTop: "32px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><h4>Interactive</h4><button type="button" className="secondary tiny" style={{ fontSize: "0.75rem", padding: "4px 8px", height: "auto", margin: 0 }} onClick={() => { ensureEditCache(moduleNum, module); setEditFC({ ...editFC, [moduleNum]: true }); }}>Edit Cards</button></div>
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
      })}
      {courseData.quiz && (
        <QuizEditor
          courseData={courseData}
          hasActiveRequest={hasActiveRequest}
          saveCourseData={saveCourse}
          setUiNotice={setUiNotice}
        />
      )}

      {/* Full-size image preview modal */}
      {previewImage && (
        <ModalPortal>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 9999, background: "rgba(15, 23, 42, 0.65)", backdropFilter: "blur(6px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}
            onClick={() => setPreviewImage(null)}
            role="dialog"
            aria-modal="true"
            aria-labelledby="module-image-preview-title"
          >
            <div
              style={{ width: "100%", maxWidth: 980, maxHeight: "90vh", background: "#fff", borderRadius: 18, boxShadow: "0 30px 80px rgba(15, 23, 42, 0.35)", display: "flex", flexDirection: "column", overflow: "hidden" }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border, #e2e8f0)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <div style={{ fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--accent, #1b5aa6)" }}>
                    Module {String(previewImage.moduleNum).padStart(2, "0")} Image
                  </div>
                  <h3 id="module-image-preview-title" style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#0f172a" }}>
                    {previewImage.title}
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setPreviewImage(null)}
                  className="secondary"
                  style={{ borderRadius: "999px", padding: "6px 12px" }}
                  aria-label="Close image preview"
                >
                  Close
                </button>
              </div>
              <div style={{ flex: 1, background: "linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
                <img
                  src={previewImage.url}
                  alt={previewImage.title}
                  style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", borderRadius: 12, boxShadow: "0 18px 40px rgba(15, 23, 42, 0.2)" }}
                />
              </div>
              <div style={{ padding: "14px 20px", borderTop: "1px solid var(--border, #e2e8f0)", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                <div style={{ fontSize: "0.85rem", color: "var(--muted, #64748b)" }}>Tip: press Esc or click outside to close.</div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => window.open(previewImage.url, "_blank")}
                    style={{ minHeight: 36, padding: "6px 14px" }}
                  >
                    Open Full Size
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const link = document.createElement("a");
                      link.href = previewImage.url;
                      link.download = previewImage.filename;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    style={{ minHeight: 36, padding: "6px 14px" }}
                  >
                    Download
                  </button>
                </div>
              </div>
            </div>
          </div>
        </ModalPortal>
      )}
    </div>
  );
}
