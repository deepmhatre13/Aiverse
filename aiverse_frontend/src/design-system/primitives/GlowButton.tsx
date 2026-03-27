import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const glowButtonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 rounded-md",
    "transition-[transform,background-color,box-shadow,border-color,opacity] duration-200",
    "ease-[cubic-bezier(0.22,0.61,0.36,1)]",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35 focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "will-change-transform",
  ],
  {
    variants: {
      variant: {
        primary:
          "text-primary-foreground bg-gradient-to-br from-primary to-accent shadow-soft border border-primary/25 hover:shadow-soft hover:scale-[1.02]",
        secondary:
          "text-foreground bg-glass/70 border border-border/45 hover:border-primary/30 hover:bg-glass/80 hover:scale-[1.01]",
        tertiary:
          "text-foreground bg-transparent border border-transparent hover:bg-glass/35 hover:border-border/35",
      },
      size: {
        sm: "h-9 px-3 text-sm",
        md: "h-11 px-4 text-sm",
        lg: "h-12 px-5 text-base",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export type GlowButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof glowButtonVariants> & {
    loading?: boolean;
  };

export const GlowButton = React.forwardRef<HTMLButtonElement, GlowButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(glowButtonVariants({ variant, size }), className)}
        disabled={disabled || loading}
        {...props}
      >
        {children}
      </button>
    );
  }
);
GlowButton.displayName = "GlowButton";

