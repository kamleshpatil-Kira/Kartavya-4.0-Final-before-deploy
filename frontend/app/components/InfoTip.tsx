"use client";

interface InfoTipProps {
  text: string;
}

export function InfoTip({ text }: InfoTipProps) {
  return (
    <span
      className="tip"
      data-tooltip={text}
      tabIndex={0}
      aria-label={text}
      title={text}
    >
      i
    </span>
  );
}
