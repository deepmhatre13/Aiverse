import * as React from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export type SectionRevealProps = React.HTMLAttributes<HTMLDivElement> & {
  once?: boolean;
  threshold?: number;
  direction?: "up" | "left" | "right" | "none";
  delay?: number;
};

export function SectionReveal({
  className,
  once = true,
  threshold = 0.25,
  direction = "up",
  delay = 0,
  ...props
}: SectionRevealProps) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const inView = useInView(ref, { once, amount: threshold });
  const reduce = useReducedMotion();

  if (reduce) {
    return <div ref={ref} className={cn(className)} {...props} />;
  }

  const initial =
    direction === "up"
      ? { opacity: 0, y: 22, filter: "blur(10px)" }
      : direction === "left"
        ? { opacity: 0, x: 18, filter: "blur(10px)" }
        : direction === "right"
          ? { opacity: 0, x: -18, filter: "blur(10px)" }
          : { opacity: 0, filter: "blur(10px)" };

  return (
    <motion.div
      ref={ref}
      className={cn("will-change-transform", className)}
      initial={initial}
      animate={
        inView
          ? { opacity: 1, x: 0, y: 0, filter: "blur(0px)" }
          : initial
      }
      transition={{
        duration: 0.32,
        delay,
        ease: [0.22, 0.61, 0.36, 1],
      }}
      {...(props as any)}
    />
  );
}

