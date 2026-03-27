import * as React from "react";
import { motion, type HTMLMotionProps, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

type Variant = "fadeUp" | "fadeIn" | "scaleIn" | "slideLeft" | "slideRight";

const variants: Record<Variant, any> = {
  fadeUp: {
    hidden: { opacity: 0, y: 20, filter: "blur(8px)" },
    show: { opacity: 1, y: 0, filter: "blur(0px)" },
  },
  fadeIn: {
    hidden: { opacity: 0 },
    show: { opacity: 1 },
  },
  scaleIn: {
    hidden: { opacity: 0, scale: 0.98, filter: "blur(8px)" },
    show: { opacity: 1, scale: 1, filter: "blur(0px)" },
  },
  slideLeft: {
    hidden: { opacity: 0, x: 18, filter: "blur(8px)" },
    show: { opacity: 1, x: 0, filter: "blur(0px)" },
  },
  slideRight: {
    hidden: { opacity: 0, x: -18, filter: "blur(8px)" },
    show: { opacity: 1, x: 0, filter: "blur(0px)" },
  },
};

export type MotionContainerProps = HTMLMotionProps<"div"> & {
  variant?: Variant;
  delay?: number;
  durationMs?: number;
};

export function MotionContainer({
  className,
  variant = "fadeUp",
  delay = 0,
  durationMs = 280,
  ...props
}: MotionContainerProps) {
  const reduce = useReducedMotion();

  if (reduce) {
    return (
      <div className={cn(className)} {...(props as any)}>
        {props.children}
      </div>
    );
  }

  return (
    <motion.div
      className={cn("will-change-transform", className)}
      variants={variants[variant]}
      initial="hidden"
      animate="show"
      transition={{
        duration: durationMs / 1000,
        delay,
        ease: [0.22, 0.61, 0.36, 1],
      }}
      {...props}
    />
  );
}

