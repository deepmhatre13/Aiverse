import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export type FloatingOrbProps = React.HTMLAttributes<HTMLDivElement> & {
  size?: number;
};

export function FloatingOrb({ className, size = 56, ...props }: FloatingOrbProps) {
  const reduce = useReducedMotion();

  if (reduce) {
    return (
      <div
        className={cn("rounded-full", className)}
        style={{
          width: size,
          height: size,
          background:
            "radial-gradient(circle at 30% 30%, rgb(var(--accent-glow) / 0.85), rgb(var(--accent-primary) / 0.35) 40%, transparent 70%)",
        }}
        {...props}
      />
    );
  }

  return (
    <motion.div
      className={cn("rounded-full", className)}
      style={{
        width: size,
        height: size,
        background:
          "radial-gradient(circle at 30% 30%, rgb(var(--accent-glow) / 0.85), rgb(var(--accent-primary) / 0.35) 40%, transparent 70%)",
        boxShadow:
          "0 0 35px rgb(var(--accent-primary) / 0.25), 0 0 80px rgb(var(--accent-primary) / 0.12)",
      }}
      animate={{ scale: [1, 1.06, 1], opacity: [0.85, 1, 0.9] }}
      transition={{
        duration: 3.2,
        repeat: Infinity,
        ease: [0.22, 0.61, 0.36, 1],
      }}
      {...(props as any)}
    />
  );
}

