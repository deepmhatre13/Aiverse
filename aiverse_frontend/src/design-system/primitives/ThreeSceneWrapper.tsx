import * as React from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

type FpsLimiterProps = {
  fps: number;
  active: boolean;
};

function FpsLimiter({ fps, active }: FpsLimiterProps) {
  const invalidate = useThree((s) => s.invalidate);

  React.useEffect(() => {
    if (!active) return;
    let raf = 0;
    let last = 0;
    const frame = (t: number) => {
      raf = requestAnimationFrame(frame);
      const min = 1000 / fps;
      if (t - last < min) return;
      last = t;
      invalidate();
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [active, fps, invalidate]);

  return null;
}

export type ThreeSceneWrapperProps = {
  className?: string;
  fpsCap?: number;
  children: React.ReactNode;
  camera?: {
    position?: [number, number, number];
    fov?: number;
  };
};

export function ThreeSceneWrapper({
  className,
  fpsCap = 30,
  children,
  camera,
}: ThreeSceneWrapperProps) {
  const reduce = useReducedMotion();
  const [active, setActive] = React.useState(true);

  React.useEffect(() => {
    const onVis = () => setActive(document.visibilityState === "visible");
    onVis();
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  return (
    <div className={cn("absolute inset-0", className)}>
      <Canvas
        frameloop="demand"
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        camera={{
          position: camera?.position ?? [0, 0, 8],
          fov: camera?.fov ?? 55,
        }}
      >
        {!reduce && active ? <FpsLimiter fps={fpsCap} active={active} /> : null}
        {children}
      </Canvas>
    </div>
  );
}

