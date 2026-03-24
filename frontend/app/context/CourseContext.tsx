"use client";

import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, redactBackendProviderDetails } from "../lib/api";

export type CourseData = Record<string, any> | null;

export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled" | null;

export interface JobState {
  id: string | null;
  status: JobStatus;
  progress: number;
  message: string | null;
  error: string | null;
}

interface CourseContextValue {
  courseData: CourseData;
  setCourseData: (data: CourseData) => void;
  courseId: string | null;
  setCourseId: (id: string | null) => void;
  jobState: JobState;
  setJobState: React.Dispatch<React.SetStateAction<JobState>>;
  autoRedirect: boolean;
  setAutoRedirect: (value: boolean) => void;
  clearCourse: () => void;
  resetJob: () => void;
  startNewCourse: () => void;
}

const CourseContext = createContext<CourseContextValue | undefined>(undefined);

const DEFAULT_JOB_STATE: JobState = {
  id: null,
  status: null,
  progress: 0,
  message: null,
  error: null,
};

export function CourseProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [courseData, setCourseData] = useState<CourseData>(null);
  const [courseId, setCourseId] = useState<string | null>(null);
  const [jobState, setJobState] = useState<JobState>(DEFAULT_JOB_STATE);
  const [autoRedirect, setAutoRedirect] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const redirectRef = useRef(false);

  // Note: localStorage is NOT cleared on mount intentionally.
  // Clearing it here caused in-progress job IDs to be wiped on hard refresh,
  // breaking job tracking. Cleanup now only happens in startNewCourse(). (Fix E1)

  useEffect(() => {
    if (!courseId && courseData?.course?.id) {
      setCourseId(courseData.course.id);
    }
  }, [courseData, courseId]);

  useEffect(() => {
    if (jobState.id) {
      redirectRef.current = false;
    }
  }, [jobState.id]);

  useEffect(() => {
    const isActive = jobState.id && (jobState.status === "queued" || jobState.status === "running");
    if (!isActive) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
      return;
    }

    let cancelled = false;

    const pollJob = async () => {
      try {
        const job = await apiFetch<any>(`/api/jobs/${jobState.id}`);
        if (cancelled) return;

        setJobState((prev) => ({
          ...prev,
          status: job.status || prev.status,
          progress: typeof job.progress === "number" ? job.progress : prev.progress,
          message:
            typeof job.message === "string"
              ? redactBackendProviderDetails(job.message)
              : prev.message,
          error:
            typeof job.error === "string"
              ? redactBackendProviderDetails(job.error)
              : null,
        }));

        if (job.status === "completed") {
          setCourseData(job.course_data);
          setCourseId(job.course_id || job.course_data?.course?.id || null);
          if (autoRedirect && !redirectRef.current) {
            redirectRef.current = true;
            if (typeof window !== "undefined") {
              const currentPath = window.location.pathname;
              if (currentPath !== "/view") {
                router.push("/view");
              }
            }
            setAutoRedirect(false);
          }
        }
        if (job.status === "failed" || job.status === "cancelled") {
          setAutoRedirect(false);
        }
      } catch (err: any) {
        if (cancelled) return;
        setJobState((prev) => ({
          ...prev,
          status: "failed",
          error: redactBackendProviderDetails(err?.message || "Failed to poll job status"),
          message: "Failed",
        }));
      }
    };

    pollJob();
    pollRef.current = setInterval(pollJob, 1500);

    return () => {
      cancelled = true;
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, [jobState.id, jobState.status, autoRedirect, router]);

  const clearCourse = () => {
    setCourseData(null);
    setCourseId(null);
  };

  const resetJob = () => {
    setJobState(DEFAULT_JOB_STATE);
  };

  const startNewCourse = () => {
    setCourseData(null);
    setCourseId(null);
    setJobState(DEFAULT_JOB_STATE);
    setAutoRedirect(false);
    if (typeof window !== "undefined") {
      localStorage.removeItem("courseData");
      localStorage.removeItem("courseId");
      localStorage.removeItem("jobState");
      localStorage.removeItem("autoRedirect");
      router.push("/");
    }
  };

  return (
    <CourseContext.Provider
      value={{
        courseData,
        setCourseData,
        courseId,
        setCourseId,
        jobState,
        setJobState,
        autoRedirect,
        setAutoRedirect,
        clearCourse,
        resetJob,
        startNewCourse,
      }}
    >
      {children}
    </CourseContext.Provider>
  );
}

export function useCourse() {
  const ctx = useContext(CourseContext);
  if (!ctx) {
    throw new Error("useCourse must be used within CourseProvider");
  }
  return ctx;
}
