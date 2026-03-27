import * as React from "react";
import { cn } from "@/lib/utils";

export type ProgressRingProps = {
  value: number; // 0..100
  size?: number;
  strokeWidth?: number;
  className?: string;
  label?: string;
};

export function ProgressRing({
  value,
  size = 56,
  strokeWidth = 6,
  className,
  label,
}: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const radius = (size - strokeWidth) / 2;
  const c = 2 * Math.PI * radius;
  const dash = (clamped / 100) * c;

  return (
    <div className={cn("inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="rgb(var(--border-muted) / 0.35)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="rgb(var(--accent-primary) / 1)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      {label ? (
        <span className="sr-only">
          {label}: {clamped}%
        </span>
      ) : null}
    </div>
  );
}

