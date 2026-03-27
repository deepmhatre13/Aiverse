import * as React from "react";
import { ThreeSceneWrapper } from "@/design-system";
import { NeuralFieldScene } from "./NeuralFieldScene";

export default function NeuralFieldHero() {
  return (
    <ThreeSceneWrapper fpsCap={30} className="pointer-events-none">
      <NeuralFieldScene density="normal" interactive />
    </ThreeSceneWrapper>
  );
}

