"use client";

import React, { useState } from "react";
import { useCourse } from "../context/CourseContext";
import { apiFetch, apiUrl, readApiErrorMessage } from "../lib/api";
import { InfoTip } from "../components/InfoTip";

export default function UploadImagesPage() {
  const { courseData, setCourseData, courseId, setCourseId } = useCourse();
  const [localCourse, setLocalCourse] = useState<any>(courseData || null);

  // Fix C2: keep localCourse in sync with context so image saves use fresh course data
  React.useEffect(() => {
    if (courseData) setLocalCourse(courseData);
  }, [courseData]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [images, setImages] = useState<string[]>([]);
  const [matches, setMatches] = useState<Record<string, any>>({});
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [uiNotice, setUiNotice] = useState<{ type: "error" | "success" | "info"; text: string } | null>(null);
  const [isUploadingCourse, setIsUploadingCourse] = useState(false);
  const [isUploadingImages, setIsUploadingImages] = useState(false);
  const [isSavingImages, setIsSavingImages] = useState(false);

  const uploadCourse = async (file: File) => {
    setIsUploadingCourse(true);
    setUiNotice(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(apiUrl("/api/course/load"), {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await readApiErrorMessage(response));
      }
      const data = await response.json();
      setLocalCourse(data.course_data);
      setCourseData(data.course_data);
      if (data.course_id) {
        setCourseId(data.course_id);
      }
      setUiNotice({ type: "success", text: "Course loaded for image mapping." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to load course file." });
    } finally {
      setIsUploadingCourse(false);
    }
  };

  const MAX_IMAGE_SIZE_MB = 50;

  const uploadImages = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    // Fix C1: enforce client-side file size limit before uploading
    for (const file of Array.from(files)) {
      if (file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024) {
        setUiNotice({ type: "error", text: `"${file.name}" exceeds the ${MAX_IMAGE_SIZE_MB}MB limit. Please compress or resize.` });
        return;
      }
    }
    setIsUploadingImages(true);
    setUiNotice(null);
    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append("files", file));
      const response = await fetch(apiUrl("/api/images/upload"), {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await readApiErrorMessage(response));
      }
      const data = await response.json();
      setSessionId(data.session_id);
      setImages(data.images || []);

      if (localCourse) {
        const matchRes = await apiFetch<any>("/api/images/match", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: data.session_id, course_data: localCourse }),
        });
        setMatches(matchRes.matches || {});
        const initialSelections: Record<string, string> = {};
        Object.entries(matchRes.matches || {}).forEach(([moduleNum, match]: any) => {
          if (match.image_name) {
            initialSelections[moduleNum] = match.image_name;
          }
        });
        setSelections(initialSelections);
      }
      setUiNotice({ type: "success", text: "Images uploaded and auto-matched to modules." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: err?.message || "Failed to upload/match images." });
    } finally {
      setIsUploadingImages(false);
    }
  };

  const approveAll = () => {
    const updated: Record<string, string> = {};
    Object.entries(matches).forEach(([moduleNum, match]: any) => {
      if (match.image_name) {
        updated[moduleNum] = match.image_name;
      }
    });
    setSelections(updated);
  };

  const rejectAll = () => {
    setSelections({});
  };

  const saveImages = async () => {
    if (!sessionId || !localCourse) return;
    const cid = courseId || localCourse?.course?.id;
    if (!cid) {
      setUiNotice({ type: "error", text: "Course ID not found. Save or generate a course first." });
      return;
    }
    if (isSavingImages) return;
    setIsSavingImages(true);
    setUiNotice(null);
    try {
      const res = await apiFetch<any>("/api/images/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, course_id: cid, mappings: selections }),
      });
      setCourseData(res.course_data);
      setLocalCourse(res.course_data);
      setUiNotice({ type: "success", text: "Images successfully saved to the course." });
    } catch (err: any) {
      setUiNotice({ type: "error", text: `Failed to save images: ${err?.message || "Unknown error"}` });
    } finally {
      setIsSavingImages(false);
    }
  };

  const modules = localCourse?.modules || [];

  return (
    <div>
      <div className="card hero">
        <div>
          <div className="hero-pill">Visual Mapping</div>
          <h1>Module Image Matching</h1>
          <p>Upload image sets and align them with modules for richer learning experiences.</p>
        </div>
        <div className="panel">
          <div className="muted">Tips</div>
          <p style={{ margin: 0 }}>Step 1: Upload an xAPI, xAPI Rise 360, or SCORM 1.2 ZIP. Step 2: Upload your images. Step 3: Match them up.</p>
        </div>
      </div>

      {uiNotice && (
        <div className={`notice ${uiNotice.type}`} role={uiNotice.type === "error" ? "alert" : "status"}>
          {uiNotice.text}
        </div>
      )}

      <div className="card surface">
        <div className="card-head">
          <h2 className="section-title">Step 1 · Load Course</h2>
          {localCourse && <span className="badge">Ready</span>}
        </div>
        <p className="muted" style={{ fontSize: "0.85rem", marginBottom: 12 }}>
          Upload a course ZIP to begin mapping images to it.
          <br /><span style={{ fontSize: "0.8rem", opacity: 0.7 }}>Accepted: <code>.zip</code> — xAPI, xAPI Rise 360, or SCORM 1.2 package</span>
        </p>
        {!localCourse && (
          <input
            type="file"
            accept=".zip"
            disabled={isUploadingCourse || isUploadingImages || isSavingImages}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                void uploadCourse(file);
              }
            }}
          />
        )}
        {localCourse && (
          <p className="muted">Loaded: {localCourse.course?.title || "Course"}</p>
        )}
        {isUploadingCourse && <p className="muted">Loading course file...</p>}
      </div>

      {localCourse && (
        <div className="card surface">
          <div className="card-head">
            <h2 className="section-title">Step 2 · Upload Images</h2>
            {images.length > 0 && <span className="badge">{images.length} uploaded</span>}
          </div>
          <p className="muted" style={{ fontSize: "0.82rem", marginBottom: 8 }}>
            Upload <code>.png</code>, <code>.jpg</code> / <code>.jpeg</code> files, or a <code>.zip</code> containing images only.
          </p>
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.zip"
            multiple
            disabled={isUploadingCourse || isUploadingImages || isSavingImages}
            onChange={(e) => {
              void uploadImages(e.target.files);
            }}
          />
          {images.length > 0 && <p className="muted">{images.length} image(s) uploaded.</p>}
          {isUploadingImages && <p className="muted">Uploading images and generating matches...</p>}
        </div>
      )}

      {localCourse && images.length > 0 && (
        <div className="card surface">
          <div className="card-head">
            <h2 className="section-title">Step 3 · Match Images</h2>
            <span className="badge">{modules.length} module(s)</span>
          </div>
          <div className="inline">
            <button type="button" disabled={isUploadingImages || isSavingImages} onClick={approveAll}>
              Approve All Matches
            </button>
            <button type="button" className="secondary" disabled={isUploadingImages || isSavingImages} onClick={rejectAll}>
              Reject All Matches
            </button>
          </div>

          {modules.map((module: any, idx: number) => {
            const moduleNum = module.moduleNumber || idx + 1;
            const selection = selections[String(moduleNum)] || "";
            const autoMatch = matches[String(moduleNum)]?.image_name || "";
            const displayImage = selection || autoMatch;
            const imageUrl = displayImage && sessionId ? apiUrl(`/api/images/${sessionId}/${displayImage}`) : null;

            return (
              <div key={moduleNum} className="mapping-item">
                <div className="card-head">
                  <h3 className="card-title-sm">Module {moduleNum}: {module.moduleTitle}</h3>
                  {autoMatch && <span className="chip-soft">Auto: {autoMatch}</span>}
                </div>
                {autoMatch && (
                  <p className="muted">Confidence: {matches[String(moduleNum)]?.confidence || "-"}</p>
                )}
                {imageUrl && <img src={imageUrl} alt={displayImage} className="mapping-image" />}
                <div className="field">
                  <label>
                    Select Image
                    <InfoTip text="Override or confirm the image mapped to this module." />
                  </label>
                  <select
                    disabled={isUploadingImages || isSavingImages}
                    value={selection}
                    onChange={(e) => setSelections({ ...selections, [String(moduleNum)]: e.target.value })}
                  >
                    <option value="">None</option>
                    {images.map((img) => (
                      <option key={img} value={img}>
                        {img}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}

          <button type="button" disabled={isUploadingImages || isSavingImages} onClick={() => void saveImages()}>
            {isSavingImages ? "Saving..." : "Save Images to Course"}
          </button>
        </div>
      )}
    </div>
  );
}
