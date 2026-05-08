/**
 * Letter Dynasty v3 — Chapter 2 (line_art map + bold_stroke figures, choreographed motion).
 *
 * Path-along-spline routes between Brussels and London;
 * speed-contrast (slow Crown vs fast Rothschild);
 * letter hop between hand → horse → boat stations;
 * three figures struck through with red diagonal slashes;
 * Roworth ride sequence at Waterloo with dust trail.
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

const CHAPTER2_DURATION_S = 78.71;
export const LETTER_CHAPTER2_V3_DURATION_FRAMES = Math.ceil(CHAPTER2_DURATION_S * FPS);

const BEATS: Record<string, BeatSpec> = {
  C1: { id: "C2-01", start: 0.0, end: 6.28 },
  C2: { id: "C2-02", start: 7.44, end: 14.18 },
  C3: { id: "C2-03", start: 15.34, end: 22.72 },
  C4: { id: "C2-04", start: 23.74, end: 24.46 },
  C5: { id: "C2-05", start: 25.72, end: 31.36 },
  C6: { id: "C2-06", start: 32.0, end: 35.98 },
  C7: { id: "C2-07", start: 36.4, end: 42.28 },
  C8: { id: "C2-08", start: 42.94, end: 50.02 },
  C9: { id: "C2-09", start: 50.02, end: 57.88 },
  C10: { id: "C2-10", start: 58.92, end: 66.56 },
  C11: { id: "C2-11", start: 67.24, end: 74.06 },
  C12: { id: "C2-12", start: 74.06, end: 78.24 },
};

const BRUSSELS = { x: 0.53, y: 0.38 };
const LONDON = { x: 0.40, y: 0.32 };

// ── C2-01: Crown courier slow path Brussels → London with day counter ────
const Beat1: React.FC = () => {
  const p = useBeatProgress(BEATS.C1);
  const x = interpolate(p, [0, 1], [BRUSSELS.x, LONDON.x]);
  const y = interpolate(p, [0, 1], [BRUSSELS.y, LONDON.y]);
  const dayCount = Math.min(4, Math.floor(p * 4) + 1);
  return (
    <Beat spec={BEATS.C1}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ opacity: 0.7 }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
      </AbsoluteFill>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <line x1={BRUSSELS.x * 1920} y1={BRUSSELS.y * 1080} x2={x * 1920} y2={y * 1080} stroke={MM.red} strokeWidth={3} strokeDasharray="8 8" opacity={0.7} />
        <circle cx={BRUSSELS.x * 1920} cy={BRUSSELS.y * 1080} r={10} fill={MM.gold} />
        <circle cx={LONDON.x * 1920} cy={LONDON.y * 1080} r={10} fill={MM.gold} />
      </svg>
      <div style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, transform: "translate(-50%, -50%)", width: "10%", height: "13%" }}>
        <MMSvgV3 src={v3lib("lib/crown-courier-bold.svg")} />
      </div>
      <div style={{ position: "absolute", top: "8%", right: "8%", fontFamily: "Georgia, serif", fontWeight: 700, fontSize: 60, color: MM.ink, ...TEXT_STROKE }}>
        DAY {dayCount}
      </div>
      <Vignette intensity={0.35} />
    </Beat>
  );
};

// ── C2-02: Channel storm ─────────────────────────────────────────────────
const Beat2: React.FC = () => {
  const f = useBeatFrame(BEATS.C2);
  return (
    <Beat spec={BEATS.C2}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-channel-storm.svg")} preserveAspect="xMidYMid slice" />
      </AbsoluteFill>
      <Vignette intensity={0.5} />
      <FilmGrain frame={f} opacity={0.06} />
    </Beat>
  );
};

// ── C2-03: Rothschild courier 4x speed + 32h badge ───────────────────────
const Beat3: React.FC = () => {
  const p = useBeatProgress(BEATS.C3);
  const fastP = Math.min(1, p * 1.6);
  const x = interpolate(fastP, [0, 1], [BRUSSELS.x, LONDON.x]);
  const y = interpolate(fastP, [0, 1], [BRUSSELS.y, LONDON.y]);
  const hours = Math.max(0, Math.min(32, 32 - Math.floor(p * 32)));
  return (
    <Beat spec={BEATS.C3}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ opacity: 0.7 }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
      </AbsoluteFill>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <line x1={BRUSSELS.x * 1920} y1={BRUSSELS.y * 1080} x2={x * 1920} y2={y * 1080} stroke={MM.gold} strokeWidth={4} opacity={0.9} style={{ filter: `drop-shadow(0 0 10px ${MM.gold})` }} />
        <circle cx={BRUSSELS.x * 1920} cy={BRUSSELS.y * 1080} r={11} fill={MM.gold} />
        <circle cx={LONDON.x * 1920} cy={LONDON.y * 1080} r={11} fill={MM.gold} />
      </svg>
      <div style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, transform: "translate(-50%, -50%)", width: "10%", height: "13%", filter: `drop-shadow(0 0 14px ${MM.gold})` }}>
        <MMSvgV3 src={v3lib("lib/rothschild-courier-bold.svg")} />
      </div>
      <div style={{ position: "absolute", top: "8%", right: "8%", fontFamily: "Georgia, serif", fontWeight: 700, fontSize: 96, color: MM.gold, letterSpacing: "0.02em", ...TEXT_STROKE }}>
        {hours}h
      </div>
      <Vignette intensity={0.35} />
    </Beat>
  );
};

// ── C2-04: "How?" punch ──────────────────────────────────────────────────
const Beat4: React.FC = () => {
  const p = useBeatProgress(BEATS.C4);
  const scale = interpolate(p, [0, 1], [0.7, 1.1], { easing: easeOut });
  return (
    <Beat spec={BEATS.C4} dissolve={0.2}>
      <AbsoluteFill style={{ backgroundColor: MM.bg }} />
      <Vignette intensity={0.6} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: 280, color: MM.cream, transform: `scale(${scale})`, ...TEXT_STROKE }}>
          How?
        </div>
      </AbsoluteFill>
    </Beat>
  );
};

// ── C2-05: Coastal port + multiple riders ─────────────────────────────────
const Beat5: React.FC = () => {
  const p = useBeatProgress(BEATS.C5);
  // First half: riders moving on roads; second half: port + boats
  const ridersFade = interpolate(p, [0, 0.05, 0.42, 0.5], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const portFade = interpolate(p, [0.42, 0.55, 1], [0, 1, 1], { extrapolateRight: "clamp" });
  const f = useBeatFrame(BEATS.C5);
  return (
    <Beat spec={BEATS.C5}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      {/*  Port background fades in second half */}
      <AbsoluteFill style={{ opacity: portFade }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-coastal-port.svg")} preserveAspect="xMidYMid slice" />
      </AbsoluteFill>
      {/*  Riders moving in first half */}
      <AbsoluteFill style={{ opacity: ridersFade }}>
        {[0, 1, 2].map((i) => {
          const speed = 1 + i * 0.3;
          const x = ((f * 8 * speed + i * 600) % 2400) - 200;
          return (
            <div key={i} style={{ position: "absolute", left: x, top: `${30 + i * 20}%`, width: "12%", height: "20%", opacity: 0.9 - i * 0.15 }}>
              <MMSvgV3 src={v3lib(i === 0 ? "lib/rothschild-courier-bold.svg" : "lib/horse-galloping-bold.svg")} />
            </div>
          );
        })}
      </AbsoluteFill>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

// ── C2-06: Clerk + spinning clock ────────────────────────────────────────
const Beat6: React.FC = () => {
  const f = useBeatFrame(BEATS.C6);
  const clockAngle = (f * 360 * 4) / FPS;
  const flicker = Math.sin(f * 0.5) * 0.2 + 0.85;
  return (
    <Beat spec={BEATS.C6}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill>
        <MMSvgV3 src={v3lib("lib/clerk-desk-bold.svg")} preserveAspect="xMidYMid meet" />
      </AbsoluteFill>
      <Vignette intensity={0.45} />
      {/*  Clock face top-right with spinning hands */}
      <div
        style={{
          position: "absolute",
          top: "12%",
          right: "12%",
          width: 180,
          height: 180,
          borderRadius: "50%",
          border: `5px solid ${MM.gold}`,
          background: MM.cream,
          boxShadow: `0 0 30px ${MM.gold}66`,
        }}
      >
        {/*  hour hand */}
        <div style={{ position: "absolute", left: "50%", top: "50%", width: 4, height: 60, background: MM.ink, transform: `translate(-50%, -100%) rotate(${clockAngle}deg)`, transformOrigin: "bottom center" }} />
        {/*  minute hand */}
        <div style={{ position: "absolute", left: "50%", top: "50%", width: 3, height: 50, background: MM.gold, transform: `translate(-50%, -100%) rotate(${clockAngle * 12}deg)`, transformOrigin: "bottom center" }} />
        <div style={{ position: "absolute", left: "50%", top: "50%", width: 10, height: 10, borderRadius: "50%", background: MM.ink, transform: "translate(-50%, -50%)" }} />
      </div>
    </Beat>
  );
};

// ── C2-07: Paris son writing letter + mailbag X overlay ──────────────────
const Beat7: React.FC = () => {
  const p = useBeatProgress(BEATS.C7);
  const xLength = interpolate(p, [0.55, 0.85], [0, 1], { extrapolateRight: "clamp" });
  const xOpacity = interpolate(p, [0.5, 0.6], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.C7}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-paris-son-writing-letter.svg")} preserveAspect="xMidYMid meet" />
      </AbsoluteFill>
      {/*  X strike overlay (red diagonal) */}
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: xOpacity }}>
        <line x1={1300} y1={300} x2={1300 + xLength * 400} y2={300 + xLength * 400} stroke={MM.red} strokeWidth={20} style={{ filter: `drop-shadow(0 0 14px ${MM.red})` }} />
        <line x1={1700} y1={300} x2={1700 - xLength * 400} y2={300 + xLength * 400} stroke={MM.red} strokeWidth={20} style={{ filter: `drop-shadow(0 0 14px ${MM.red})` }} />
      </svg>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

// ── C2-08: Letter hops between hand → horse → boat ───────────────────────
const Beat8: React.FC = () => {
  const p = useBeatProgress(BEATS.C8);
  const stations = [
    { src: "lib/gloved-hand-bold.svg", label: "HANDS", x: "18%" },
    { src: "lib/horse-galloping-bold.svg", label: "HORSES", x: "50%" },
    { src: "lib/packet-boat-bold.svg", label: "BOATS", x: "82%" },
  ];
  const stationIdx = p < 0.3 ? 0 : p < 0.6 ? 1 : 2;
  const xFrac = parseFloat(stations[stationIdx].x) / 100;
  return (
    <Beat spec={BEATS.C8}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <Vignette intensity={0.35} />
      {stations.map((s, i) => {
        const lit = stationIdx === i ? 1 : 0.35;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: s.x,
              top: "55%",
              transform: "translate(-50%, -50%)",
              width: "16%",
              height: "32%",
              opacity: lit,
              filter: stationIdx === i ? `drop-shadow(0 0 16px ${MM.gold})` : "none",
            }}
          >
            <MMSvgV3 src={v3lib(s.src)} />
          </div>
        );
      })}
      {stations.map((s, i) => (
        <div
          key={s.label}
          style={{
            position: "absolute",
            left: s.x,
            top: "82%",
            transform: "translateX(-50%)",
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 22,
            color: stationIdx === i ? MM.gold : MM.ink,
            opacity: stationIdx === i ? 1 : 0.5,
            letterSpacing: "0.18em",
            ...TEXT_STROKE,
          }}
        >
          {s.label}
        </div>
      ))}
      {/*  Letter sprite hopping */}
      <div
        style={{
          position: "absolute",
          left: `${xFrac * 100}%`,
          top: "25%",
          transform: "translate(-50%, -50%)",
          width: "10%",
          height: "10%",
          filter: `drop-shadow(0 0 18px ${MM.gold})`,
        }}
      >
        <MMSvgV3 src={v3lib("lib/letter-isolated.svg")} />
      </div>
    </Beat>
  );
};

// ── C2-09: Three figures struck through ───────────────────────────────────
const Beat9: React.FC = () => {
  const p = useBeatProgress(BEATS.C9);
  const figs = [
    { src: "lib/customs-officer-bold.svg", label: "CUSTOMS OFFICER", at: 0 },
    { src: "lib/competing-banker-bold.svg", label: "BANKER", at: 0.34 },
    { src: "lib/kings-spy-bold.svg", label: "KING'S SPY", at: 0.68 },
  ];
  return (
    <Beat spec={BEATS.C9}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <Vignette intensity={0.45} />
      {figs.map((fig, i) => {
        const localP = Math.max(0, Math.min(1, (p - fig.at) / 0.32));
        const fadeIn = interpolate(localP, [0, 0.25], [0, 1], { extrapolateRight: "clamp" });
        const slashLength = interpolate(localP, [0.4, 0.85], [0, 1], { extrapolateRight: "clamp" });
        const dimAfter = interpolate(localP, [0.85, 1], [1, 0.4], { extrapolateRight: "clamp" });
        return (
          <div
            key={fig.label}
            style={{
              position: "absolute",
              left: `${10 + i * 30}%`,
              top: "20%",
              width: "23%",
              height: "65%",
              opacity: fadeIn * dimAfter,
            }}
          >
            <MMSvgV3 src={v3lib(fig.src)} />
            <div
              style={{
                position: "absolute",
                left: 0,
                top: "50%",
                width: `${slashLength * 100}%`,
                height: 14,
                background: MM.red,
                transform: "rotate(-20deg)",
                transformOrigin: "left center",
                opacity: 0.92,
                boxShadow: `0 0 14px ${MM.red}`,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: 0,
                bottom: -50,
                width: "100%",
                fontFamily: "Georgia, serif",
                fontWeight: 700,
                fontSize: 18,
                color: MM.ink,
                textAlign: "center",
                letterSpacing: "0.15em",
                ...TEXT_STROKE,
              }}
            >
              {fig.label}
            </div>
          </div>
        );
      })}
    </Beat>
  );
};

// ── C2-10: Roworth at Waterloo ────────────────────────────────────────────
const Beat10: React.FC = () => {
  const f = useBeatFrame(BEATS.C10);
  const p = useBeatProgress(BEATS.C10);
  return (
    <Beat spec={BEATS.C10}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #d4944a 0%, #8b5a2b 50%, #3a2a1a 100%)", opacity: 0.55 }} />
      <Vignette intensity={0.6} />
      {/*  Smoke drift particles */}
      <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
        {Array.from({ length: 30 }).map((_, i) => {
          const seed = i * 43;
          const x = ((seed * 31) % 1920 + (f * 6) % 200) % 1920;
          const y = 200 + (seed * 17) % 400;
          const size = 80 + (seed % 50);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: y,
                width: size,
                height: size,
                borderRadius: "50%",
                background: "rgba(180, 170, 150, 0.25)",
                filter: "blur(40px)",
              }}
            />
          );
        })}
      </AbsoluteFill>
      {/*  Roworth foreground */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingBottom: "8%" }}>
        <div style={{ width: "22%", height: "55%" }}>
          <MMSvgV3 src={v3lib("lib/roworth-bold.svg")} />
        </div>
      </AbsoluteFill>
      <FilmGrain frame={f} opacity={0.08} />
    </Beat>
  );
};

// ── C2-11: Three "doesn't wait" sub-beats ─────────────────────────────────
const Beat11: React.FC = () => {
  const p = useBeatProgress(BEATS.C11);
  const phase = p < 0.33 ? 0 : p < 0.65 ? 1 : 2;
  return (
    <Beat spec={BEATS.C11}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #d4944a 0%, #8b5a2b 50%, #3a2a1a 100%)", opacity: 0.45 }} />
      <Vignette intensity={0.55} />
      {/*  Phase 0: Roworth alone */}
      <AbsoluteFill style={{ opacity: phase === 0 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "26%", height: "70%" }}>
            <MMSvgV3 src={v3lib("lib/roworth-bold.svg")} />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {/*  Phase 1: Wellington in BG, Roworth in FG */}
      <AbsoluteFill style={{ opacity: phase === 1 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", paddingLeft: "10%" }}>
          <div style={{ width: "18%", height: "55%", opacity: 0.65 }}>
            <MMSvgV3 src={v3lib("lib/wellington-bold.svg")} />
          </div>
        </AbsoluteFill>
        <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingRight: "12%" }}>
          <div style={{ width: "22%", height: "65%" }}>
            <MMSvgV3 src={v3lib("lib/roworth-bold.svg")} />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {/*  Phase 2: Dispatch wagon arrives empty foreground */}
      <AbsoluteFill style={{ opacity: phase === 2 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "32%", height: "40%", transform: `translate(${interpolate(p, [0.65, 1], [-1500, 0], { easing: ease })}px, 0)` }}>
            <MMSvgV3 src={v3lib("lib/dispatch-wagon-bold.svg")} />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    </Beat>
  );
};

// ── C2-12: Roworth riding north, dust trail ──────────────────────────────
const Beat12: React.FC = () => {
  const f = useBeatFrame(BEATS.C12);
  const p = useBeatProgress(BEATS.C12);
  const scale = interpolate(p, [0, 1], [1, 0.4], { easing: ease });
  const y = interpolate(p, [0, 1], [0, -200], { easing: ease });
  return (
    <Beat spec={BEATS.C12}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #f5d8a8 0%, #d4944a 50%, #8b5a2b 100%)", opacity: 0.55 }} />
      <Vignette intensity={0.5} />
      {/*  Dust trail particles */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {Array.from({ length: 40 }).map((_, i) => {
          const seed = i * 89;
          const trailX = (seed * 31) % 1920;
          const trailY = 540 + ((seed * 47) % 400) - 200;
          const op = ((seed * 13) % 50) / 100 + 0.1;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: trailX,
                top: trailY + (f * 2) % 50,
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#d4a574",
                opacity: op * (1 - p) * 0.7,
                filter: "blur(3px)",
              }}
            />
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "22%", height: "55%", transform: `translate(0, ${y}px) scale(${scale})` }}>
          <MMSvgV3 src={v3lib("lib/roworth-bold.svg")} />
        </div>
      </AbsoluteFill>
    </Beat>
  );
};

export const LetterDynastyChapter2V3: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.cream }}>
      <Audio src={staticFile("letter-dynasty-chapter2.mp3")} volume={1} />
      <Beat1 />
      <Beat2 />
      <Beat3 />
      <Beat4 />
      <Beat5 />
      <Beat6 />
      <Beat7 />
      <Beat8 />
      <Beat9 />
      <Beat10 />
      <Beat11 />
      <Beat12 />
      <FilmGrain frame={frame} opacity={0.04} />
    </AbsoluteFill>
  );
};
