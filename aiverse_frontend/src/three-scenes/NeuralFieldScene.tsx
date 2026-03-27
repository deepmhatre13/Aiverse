import * as React from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@react-three/fiber";
import { useTheme } from "@/contexts/ThemeContext";

type NeuralFieldSceneProps = {
  density?: "subtle" | "normal" | "dense";
  interactive?: boolean;
};

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function NeuralFieldScene({
  density = "normal",
  interactive = true,
}: NeuralFieldSceneProps) {
  const group = React.useRef<THREE.Group>(null);
  const points = React.useRef<THREE.Points>(null);
  const lines = React.useRef<THREE.LineSegments>(null);

  const { camera } = useThree();
  const { theme } = useTheme();

  const { nodePositions, linePositions } = React.useMemo(() => {
    const rand = mulberry32(1337);
    const count = density === "subtle" ? 140 : density === "dense" ? 320 : 220;

    const nodePositions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const ix = i * 3;
      // A shallow volume field (wide + slightly deep)
      nodePositions[ix + 0] = (rand() - 0.5) * 9.5;
      nodePositions[ix + 1] = (rand() - 0.5) * 5.4;
      nodePositions[ix + 2] = (rand() - 0.5) * 3.2;
    }

    // Connections: capped for perf
    const maxSegments = density === "subtle" ? 520 : density === "dense" ? 1400 : 900;
    const threshold = density === "subtle" ? 1.55 : density === "dense" ? 1.35 : 1.45;

    const seg: number[] = [];
    for (let i = 0; i < count; i++) {
      const ax = nodePositions[i * 3 + 0];
      const ay = nodePositions[i * 3 + 1];
      const az = nodePositions[i * 3 + 2];
      for (let j = i + 1; j < count; j++) {
        const bx = nodePositions[j * 3 + 0];
        const by = nodePositions[j * 3 + 1];
        const bz = nodePositions[j * 3 + 2];
        const dx = ax - bx;
        const dy = ay - by;
        const dz = az - bz;
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d > threshold) continue;
        if (seg.length / 6 >= maxSegments) break;
        // push endpoints (ax,ay,az) -> (bx,by,bz)
        seg.push(ax, ay, az, bx, by, bz);
      }
      if (seg.length / 6 >= maxSegments) break;
    }

    return {
      nodePositions,
      linePositions: new Float32Array(seg),
    };
  }, [density]);

  React.useEffect(() => {
    camera.position.set(0, 0, 8);
    camera.lookAt(0, 0, 0);
  }, [camera]);

  useFrame(({ clock, pointer }) => {
    const t = clock.getElapsedTime();

    if (group.current) {
      group.current.rotation.y = Math.sin(t * 0.12) * 0.12;
      group.current.rotation.x = Math.sin(t * 0.1) * 0.06;
    }

    if (points.current) {
      const mat = points.current.material as THREE.PointsMaterial;
      mat.opacity = 0.65 + Math.sin(t * 0.9) * 0.08;
    }

    if (lines.current) {
      const mat = lines.current.material as THREE.LineBasicMaterial;
      mat.opacity = 0.16 + Math.sin(t * 0.7) * 0.03;
    }

    if (interactive) {
      // Parallax camera drift (subtle)
      const tx = pointer.x * 0.55;
      const ty = pointer.y * 0.35;
      camera.position.x += (tx - camera.position.x) * 0.05;
      camera.position.y += (ty - camera.position.y) * 0.05;
      camera.position.z = 8 + Math.sin(t * 0.18) * 0.08;
      camera.lookAt(0, 0, 0);
    }
  });

  const { accent, glow, fogColor } = React.useMemo(() => {
    const readRgbTriplet = (name: string, fallback: [number, number, number]) => {
      if (typeof window === "undefined") return fallback;
      const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      const parts = raw.split(/\s+/).map((p) => Number(p));
      if (parts.length >= 3 && parts.every((n) => Number.isFinite(n))) {
        return [parts[0], parts[1], parts[2]] as [number, number, number];
      }
      return fallback;
    };

    const accentRgb = readRgbTriplet("--accent-primary", [225, 6, 0]);
    const glowRgb = readRgbTriplet("--accent-glow", [255, 77, 77]);
    const fogRgb = readRgbTriplet("--bg-primary", [11, 11, 15]);

    return {
      accent: new THREE.Color(`rgb(${accentRgb[0]}, ${accentRgb[1]}, ${accentRgb[2]})`),
      glow: new THREE.Color(`rgb(${glowRgb[0]}, ${glowRgb[1]}, ${glowRgb[2]})`),
      fogColor: new THREE.Color(`rgb(${fogRgb[0]}, ${fogRgb[1]}, ${fogRgb[2]})`),
    };
  }, [theme]);

  return (
    <group ref={group}>
      <fog attach="fog" args={[fogColor, 7, 14]} />

      <points ref={points}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={nodePositions.length / 3}
            array={nodePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.055}
          sizeAttenuation
          color={glow}
          transparent
          opacity={0.7}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      <lineSegments ref={lines}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={linePositions.length / 3}
            array={linePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          color={accent}
          transparent
          opacity={0.18}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>

      <ambientLight intensity={0.6} color={accent} />
      <pointLight position={[4, 2, 6]} intensity={1.2} color={glow} />
      <pointLight position={[-6, -2, 6]} intensity={0.7} color={accent} />
    </group>
  );
}

