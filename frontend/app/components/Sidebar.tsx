"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCourse } from "../context/CourseContext";
import {
  Sparkles,
  BookOpen,
  Image,
  Clock,
  Settings,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Course Generation", Icon: Sparkles },
  { href: "/view", label: "Course Preview", Icon: BookOpen },
  { href: "/images", label: "Upload Images", Icon: Image },
  { href: "/history", label: "History", Icon: Clock },
  { href: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { jobState } = useCourse();
  const isGenerating = jobState.status === "queued" || jobState.status === "running";
  const isFailed = jobState.status === "failed";
  const isCompleted = jobState.status === "completed";

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand">Kartavya</div>
        <div className="brand-sub">AI Course Platform</div>
      </div>

      {jobState.status && (
        <div className="status-card">
          <div className="status-title">Generation</div>
          <div className="status-row">
            {isGenerating ? (
              <Loader2 size={13} className="status-icon spinning" style={{ color: "#1b5aa6" }} />
            ) : isCompleted ? (
              <CheckCircle2 size={13} className="status-icon" style={{ color: "#15803d" }} />
            ) : isFailed ? (
              <AlertCircle size={13} className="status-icon" style={{ color: "#b91c1c" }} />
            ) : (
              <span className={`status-dot ${isCompleted ? "done" : ""}`} />
            )}
            <span style={{ textTransform: "capitalize" }}>{jobState.status}</span>
          </div>
          <div className="progress-track small">
            <div className="progress-bar" style={{ width: `${Number(jobState.progress) || 0}%` }} />
          </div>
          {jobState.message && (
            <div className="muted" style={{ fontSize: "0.75rem", marginTop: 6 }}>
              {jobState.message}
            </div>
          )}
        </div>
      )}

      <nav className="sidebar-nav">
        {navItems.map(({ href, label, Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`nav-link${active ? " active" : ""}`}
            >
              <Icon
                size={17}
                className="nav-icon"
                strokeWidth={active ? 2.2 : 1.8}
              />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
