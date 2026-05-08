/**
 * Letter Dynasty v3 — Cold Open (vivid_shapes, bold flat color).
 *
 * Each beat is a full-frame vivid_shapes scene. Motion: subtle parallax/zoom,
 * dynamic transitions between beats, paper storm at panic moment, chart drop.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { MM, MMSvgV3, v3lib } from "./MMSvgV3";
import {
  Beat,
  BeatSpec,
  FilmGrain,
  FPS,
  TEXT_STROKE,
  Vignette,
  ease,
  easeOut,
  microZoom,
  useBeatFrame,
  useBeatProgress,
} from "../beat-helpers";

const COLD_OPEN_DURATION_S = 103.47;
export const LETTER_COLD_OPEN_V3_DURATION_FRAMES = Math.ceil(COLD_OPEN_DURATION_S * FPS);

const BEATS: Record<string, BeatSpec> = {
  CO1: { id: "CO-01", start: 0.0, end: 8.12 },
  CO2: { id: "CO-02", start: 8.12, end: 15.76 },
  CO3: { id: "CO-03", start: 15.76, end: 25.46 },
  CO4: { id: "CO-04", start: 26.02, end: 33.22 },
  CO5: { id: "CO-05", start: 34.14, end: 43.16 },
  CO6: { id: "CO-06", start: 43.86, end: 51.0 },
  CO7: { id: "CO-07", start: 51.0, end: 58.22 },
  CO8: { id: "CO-08", start: 59.0, end: 66.7 },
  CO9: { id: "CO-09", start: 66.7, end: 73.22 },
  CO10: { id: "CO-10", start: 73.22, end: 80.28 },
  CO11: { id: "CO-11", start: 80.28, end: 88.5 },
  CTA1: { id: "CO-12-CTA", start: 88.5, end: 95.78 },
  CTA2: { id: "CO-13-CTA", start: 95.78, end: 102.92 },
};

const Scene: React.FC<{
  spec: BeatSpec;
  src: string;
  zoom?: number;
  drift?: { x: number; y: number };
  vignetteIntensity?: number;
  preserveAspect?: string;
}> = ({ spec, src, zoom = 0.05, drift, vignetteIntensity = 0.45, preserveAspect = "xMidYMid slice" }) => {
  const p = useBeatProgress(spec);
  const scale = microZoom(p, zoom);
  const tx = drift ? drift.x * p : 0;
  const ty = drift ? drift.y * p : 0;
  return (
    <Beat spec={spec}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ transform: `translate(${tx}px, ${ty}px) scale(${scale})` }}>
        <MMSvgV3 src={src} preserveAspect={preserveAspect} />
      </AbsoluteFill>
      <Vignette intensity={vignetteIntensity} />
    </Beat>
  );
};

// CO-04 chart drop with arrow rise-fail
const Beat4: React.FC = () => {
  const p = useBeatProgress(BEATS.CO4);
  const arrowY = interpolate(p, [0, 0.35, 0.55, 1.0], [50, -40, -50, 80], { easing: ease });
  const arrowOpacity = interpolate(p, [0.1, 0.25, 0.85, 1.0], [0, 1, 1, 0.3]);
  return (
    <Beat spec={BEATS.CO4}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <MMSvgV3 src={v3lib("lib/bond-paper-vivid.svg")} preserveAspect="xMidYMid meet" />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `translate(0, ${arrowY}px)`, opacity: arrowOpacity }}>
        <div
          style={{
            width: 0,
            height: 0,
            borderLeft: "26px solid transparent",
            borderRight: "26px solid transparent",
            borderBottom: `42px solid ${MM.red}`,
            filter: `drop-shadow(0 0 18px ${MM.red})`,
          }}
        />
      </AbsoluteFill>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

// CO-06 market collapse — three-step chart drop
const Beat6: React.FC = () => {
  const p = useBeatProgress(BEATS.CO6);
  return (
    <Beat spec={BEATS.CO6}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <Vignette intensity={0.3} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width="60%" height="60%" viewBox="0 0 600 600">
          <polyline
            points={`50,100 200,100 250,${100 + Math.max(0, 70 * (p > 0.05 ? 1 : 0))} 350,${
              100 + Math.max(0, 140 * (p > 0.3 ? 1 : 0))
            } 450,${100 + Math.max(0, 210 * (p > 0.55 ? 1 : 0))} 550,${100 + Math.max(0, 210 * (p > 0.55 ? 1 : 0))}`}
            fill="none"
            stroke={MM.red}
            strokeWidth={6}
            style={{ filter: `drop-shadow(0 0 8px ${MM.red})` }}
          />
        </svg>
      </AbsoluteFill>
    </Beat>
  );
};

const BeatCTA1: React.FC = () => {
  const p = useBeatProgress(BEATS.CTA1);
  return (
    <Beat spec={BEATS.CTA1}>
      <AbsoluteFill style={{ backgroundColor: MM.bg }} />
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 38,
            color: MM.cream,
            textAlign: "center",
            padding: "0 12%",
            lineHeight: 1.5,
            opacity: interpolate(p, [0, 0.2], [0, 1], { extrapolateRight: "clamp" }),
            ...TEXT_STROKE,
          }}
        >
          If these stories speak to you,
          <br />
          if you find comfort in the lessons found
          <br />
          in the quiet corners of history…
        </div>
      </AbsoluteFill>
    </Beat>
  );
};

const BeatCTA2: React.FC = () => {
  const p = useBeatProgress(BEATS.CTA2);
  const fadeToBlack = interpolate(p, [0.7, 1], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <Beat spec={BEATS.CTA2}>
      <AbsoluteFill style={{ backgroundColor: MM.bg }} />
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", opacity: fadeToBlack }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 78,
            color: MM.gold,
            letterSpacing: "0.06em",
            ...TEXT_STROKE,
          }}
        >
          MIDNIGHT MAGNATES
        </div>
        <div
          style={{
            marginTop: 18,
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 28,
            color: MM.cream,
            letterSpacing: "0.18em",
            ...TEXT_STROKE,
          }}
        >
          JOIN THE CIRCLE OF DREAMERS
        </div>
      </AbsoluteFill>
    </Beat>
  );
};

export const LetterDynastyColdOpenV3: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.cream }}>
      <Audio src={staticFile("letter-dynasty-cold-open.mp3")} volume={1} />
      <Scene spec={BEATS.CO1} src={v3lib("bg/cold-open-trading-floor-wide.svg")} preserveAspect="xMidYMid slice" zoom={0.04} drift={{ x: -40, y: 0 }} />
      <Scene spec={BEATS.CO2} src={v3lib("lib/nathan-vivid.svg")} zoom={0.08} />
      <Scene spec={BEATS.CO3} src={v3lib("scenes/cold-open/co-brokers-panic.svg")} zoom={0.04} />
      <Beat4 />
      <Scene spec={BEATS.CO5} src={v3lib("scenes/cold-open/co-brokers-panic.svg")} zoom={0.06} drift={{ x: 30, y: 0 }} />
      <Beat6 />
      <Scene spec={BEATS.CO7} src={v3lib("lib/anonymous-agent-vivid.svg")} zoom={0.05} />
      <Scene spec={BEATS.CO8} src={v3lib("lib/anonymous-agent-vivid.svg")} zoom={0.06} drift={{ x: 50, y: -20 }} />
      <Scene spec={BEATS.CO9} src={v3lib("scenes/cold-open/co-courier-arriving-whitehall.svg")} zoom={0.04} />
      <Scene spec={BEATS.CO10} src={v3lib("scenes/cold-open/co-letter-table-candle.svg")} zoom={0.05} />
      <Scene spec={BEATS.CO11} src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} zoom={0.06} drift={{ x: 0, y: -20 }} preserveAspect="xMidYMid meet" />
      <BeatCTA1 />
      <BeatCTA2 />
      <FilmGrain frame={frame} opacity={0.035} />
    </AbsoluteFill>
  );
};
