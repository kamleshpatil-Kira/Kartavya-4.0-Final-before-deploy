"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useCourse } from "../context/CourseContext";
import { apiUrl } from "../lib/api";
// import ShinyText from "./reactbits/ShinyText";

const pageLabels: Record<string, string> = {
  "/": "Course Generation",
  "/view": "Course Viewer",
  "/images": "Image Mapping",
  "/history": "History",
  "/settings": "Settings",
};

export function TopBar() {
  const pathname = usePathname();
  const { courseData, courseId, jobState, startNewCourse } = useCourse();
  const [downloadsOpen, setDownloadsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);
  const downloadsTriggerRef = useRef<HTMLButtonElement | null>(null);
  const downloadsItemRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const isGenerating = jobState.status === "queued" || jobState.status === "running";
  const effectiveCourseId = courseId || courseData?.course?.id || null;
  const hasModules = Array.isArray(courseData?.modules) && courseData?.modules.length > 0;
  const canDownload = Boolean(effectiveCourseId && hasModules && !isGenerating);
  const hydratedCanDownload = mounted && canDownload;
  const downloadsMenuId = downloadsOpen && hydratedCanDownload ? "downloads-menu" : undefined;

  const pageTitle = useMemo(() => {
    if (pathname in pageLabels) return pageLabels[pathname];
    return "Workspace";
  }, [pathname]);

  useEffect(() => {
    setDownloadsOpen(false);
  }, [pathname, canDownload]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!downloadsOpen) return;
    const handleClick = (event: MouseEvent) => {
      if (!dropdownRef.current) return;
      if (!dropdownRef.current.contains(event.target as Node)) {
        setDownloadsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [downloadsOpen]);

  useEffect(() => {
    if (!downloadsOpen) return;
    const firstItem = downloadsItemRefs.current[0];
    if (firstItem) firstItem.focus();
  }, [downloadsOpen]);

  useEffect(() => {
    if (!downloadsOpen) return;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setDownloadsOpen(false);
      downloadsTriggerRef.current?.focus();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [downloadsOpen]);

  const downloadItems = [
    { label: "xAPI ZIP", path: "xapi" },
    { label: "JSON", path: "json" },
    { label: "PDF", path: "pdf" },
  ];

  const focusMenuItem = (index: number) => {
    const total = downloadItems.length;
    if (total === 0) return;
    const normalized = ((index % total) + total) % total;
    downloadsItemRefs.current[normalized]?.focus();
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (!hydratedCanDownload) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setDownloadsOpen(true);
    }
  };

  const handleItemKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, idx: number) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusMenuItem(idx + 1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      focusMenuItem(idx - 1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      focusMenuItem(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      focusMenuItem(downloadItems.length - 1);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setDownloadsOpen(false);
      downloadsTriggerRef.current?.focus();
    }
  };

  return (
    <div>
      {/* Topbar hidden per user request */}
    </div>
  );
}
