// YUGA previs: author a 4-second hero-introduction orbit with Sirio Berati's
// MIT-licensed camera-control engine. The figure is a stand-in, not Hanuman.
import type { Piece } from "../piece";
import type { ActorSpec } from "../kit/actors";
import { rig } from "../kit/rigs";
import { make, type TemplateInfo } from "./cameras";

const info: TemplateInfo = {
  id: "YUGA01-MountainPulse",
  name: "Mountain Pulse · camera study",
  says: "A slow orbit introduces the hero before the marked impact.",
  use: "A previsualization for Hanuman's Mountain Pulse, not game footage.",
  numbers: "35 mm, full shot, 20 to 110 degrees over 4 seconds, eased holds.",
  avoid: "Treating a placeholder body or generated video as a rigged game asset.",
};

const actors: ActorSpec[] = [{
  id: "HANUMAN_STANDIN", name: "Hanuman stand-in", kind: "human", tint: "ochre",
  path: [{ t: 0, at: [0, 0], yaw: 0 }],
}];

export const YUGA_TEMPLATES: Piece[] = [
  make(info, actors, (P) => [{
    start: 0, end: 4, label: "35mm  YUGA HERO ORBIT", rig: "ORBIT",
    subject: "HANUMAN_STANDIN", size: "FS", stop: 2.8,
    cam: rig.orbit(P("HANUMAN_STANDIN"), { size: "FS", mm: 35, rise: 0 }, 20, 110, 0, 4, 0, 0.4),
    cut: "Opens the hero study", flags: ["compound"],
  }]),
];
