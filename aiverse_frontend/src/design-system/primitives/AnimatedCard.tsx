import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export type AnimatedCardProps = React.HTMLAttributes<HTMLDivElement> & {
  interactive?: boolean;
};

export function AnimatedCard({
  className,
  interactive = true,
  ...props
}: AnimatedCardProps) {
  const reduce = useReducedMotion();

  if (!interactive || reduce) {
    return (
      <div
        className={cn(
          "rounded-lg border border-border/40 bg-glass/70 backdrop-blur-xl",
          className
        )}
        {...props}
      />
    );
  }

  return (
    <motion.div
      className={cn(
        "rounded-lg border border-border/40 bg-glass/70 backdrop-blur-xl",
        "transition-shadow",
        className
      )}
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.22, ease: [0.22, 0.61, 0.36, 1] }}
      {...(props as any)}
    />
  );
}

