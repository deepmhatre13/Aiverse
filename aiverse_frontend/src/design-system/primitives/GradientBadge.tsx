import * as React from "react";
import { cn } from "@/lib/utils";

export type GradientBadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "default" | "muted" | "danger";
};

export const GradientBadge = React.forwardRef<HTMLSpanElement, GradientBadgeProps>(
  ({ className, tone = "default", ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium tracking-wide",
          "backdrop-blur",
          tone === "default" &&
            "border-primary/25 bg-primary/10 text-primary",
          tone === "muted" &&
            "border-border/40 bg-glass/60 text-muted-foreground",
          tone === "danger" &&
            "border-primary/30 bg-primary/15 text-foreground",
          className
        )}
        {...props}
      />
    );
  }
);
GradientBadge.displayName = "GradientBadge";

