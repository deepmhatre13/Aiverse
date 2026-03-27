import * as React from "react";
import { cn } from "@/lib/utils";

export type GlassPanelProps = React.HTMLAttributes<HTMLDivElement> & {
  padding?: "sm" | "md" | "lg";
};

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
  ({ className, padding = "md", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border/40 bg-glass/75 backdrop-blur-xl",
          padding === "sm" && "p-3",
          padding === "md" && "p-4 md:p-5",
          padding === "lg" && "p-6 md:p-7",
          className
        )}
        {...props}
      />
    );
  }
);
GlassPanel.displayName = "GlassPanel";

