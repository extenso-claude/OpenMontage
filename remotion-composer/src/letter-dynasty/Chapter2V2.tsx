/**
 * Letter Dynasty — Chapter 2 (Approach D: Choreographed Motion System).
 *
 * 12 beats over 78.71s. Multiple synchronized elements per beat —
 * path-along-spline riders, packet boats, particle dust, hop animations.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { MM, MMSvg, svgLib } from "./MMSvg";
import {
  Beat,
  BeatSpec,
  DustParticles,
  FilmGrain,
  FPS,
  LightShaftAcross,
  Plate,
  TEXT_STROKE,
  Vignette,
  ease,
  easeOut,
  useBeatFrame,
  useBeatProgress,
} from "./beat-helpers";

const CHAPTER2_DURATION_S = 78.71;
export const LETTER_CHAPTER2_V2_DURATION_FRAMES = Math.ceil(
  CHAPTER2_DURATION_S * FPS
);

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

// Brussels at ~62% x, 30% y; London at ~38% x, 32% y on the map (approx)
const BRUSSELS = { x: 0.55, y: 0.36 };
const LONDON = { x: 0.40, y: 0.32 };

// ── C2-01: Crown courier slow path Brussels → London ──────────────────────
const Beat1: React.FC = () => {
  const f = useBeatFrame(BEATS.C1);
  const p = useBeatProgress(BEATS.C1);
  const x = interpolate(p, [0, 1], [BRUSSELS.x, LONDON.x]);
  const y = interpolate(p, [0, 1], [BRUSSELS.y, LONDON.y]);
  const dayCount = Math.min(4, Math.floor(p * 4) + 1);
  return (
    <Beat spec={BEATS.C1}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.55 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      {/*  Slow path-line (line drawn so far) */}
      <svg
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      >
        <line
          x1={BRUSSELS.x * 1920}
          y1={BRUSSELS.y * 1080}
          x2={x * 1920}
          y2={y * 1080}
          stroke={MM.cream}
          strokeWidth={2}
          strokeDasharray="6 6"
          opacity={0.5}
        />
        <circle cx={BRUSSELS.x * 1920} cy={BRUSSELS.y * 1080} r={9} fill={MM.cream} />
        <circle cx={LONDON.x * 1920} cy={LONDON.y * 1080} r={9} fill={MM.cream} />
      </svg>
      {/*  Courier sprite at current path position */}
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          transform: "translate(-50%, -50%)",
          width: "8%",
          height: "13%",
        }}
      >
        <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
      </div>
      {/*  Day counter */}
      <div
        style={{
          position: "absolute",
          top: "8%",
          right: "8%",
          fontFamily: "Georgia, serif",
          fontWeight: 700,
          fontSize: 60,
          color: MM.cream,
          ...TEXT_STROKE,
        }}
      >
        DAY {dayCount}
      </div>
      <Vignette intensity={0.6} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C2-02: Channel storm + courier struggling ────────────────────────────
const Beat2: React.FC = () => {
  const f = useBeatFrame(BEATS.C2);
  const p = useBeatProgress(BEATS.C2);
  return (
    <Beat spec={BEATS.C2}>
      <Plate />
      <MMSvg src={svgLib("bg/english-channel-storm.svg")} mode="ink-cream" />
      <Vignette intensity={0.78} />
      {/*  Wave particles */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {Array.from({ length: 50 }).map((_, i) => {
          const seed = i * 71;
          const x = (((seed * 31) % 1920) + ((f * 4 + seed) % 200)) % 1920;
          const y = ((seed * 47) % 1080 + Math.sin((f + seed) * 0.1) * 30) % 1080;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: 540 + (y % 540),
                width: 3,
                height: 3,
                background: MM.cream,
                opacity: 0.4,
                transform: `translate(${(f * 6) % 200}px, 0)`,
              }}
            />
          );
        })}
      </AbsoluteFill>
      {/*  Courier slowing — moves slowly across */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "12%",
            height: "20%",
            transform: `translate(${interpolate(p, [0, 1], [-200, 200])}px, ${
              Math.sin(f * 0.2) * 8
            }px)`,
            opacity: 0.85,
          }}
        >
          <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C2-03: Rothschild courier 4x speed + 32 hours badge ──────────────────
const Beat3: React.FC = () => {
  const f = useBeatFrame(BEATS.C3);
  const p = useBeatProgress(BEATS.C3);
  // 4x speed: same Brussels->London path but in 1/4 the time
  const fastP = Math.min(1, p * 1.6);
  const x = interpolate(fastP, [0, 1], [BRUSSELS.x, LONDON.x]);
  const y = interpolate(fastP, [0, 1], [BRUSSELS.y, LONDON.y]);
  const hours = Math.max(0, Math.min(32, 32 - Math.floor(p * 32)));
  return (
    <Beat spec={BEATS.C3}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.6 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <svg
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      >
        <line
          x1={BRUSSELS.x * 1920}
          y1={BRUSSELS.y * 1080}
          x2={x * 1920}
          y2={y * 1080}
          stroke={MM.gold}
          strokeWidth={3}
          opacity={0.8}
          style={{ filter: `drop-shadow(0 0 8px ${MM.gold})` }}
        />
        <circle cx={BRUSSELS.x * 1920} cy={BRUSSELS.y * 1080} r={10} fill={MM.gold} />
        <circle cx={LONDON.x * 1920} cy={LONDON.y * 1080} r={10} fill={MM.gold} />
      </svg>
      <div
        style={{
          position: "absolute",
          left: `${x * 100}%`,
          top: `${y * 100}%`,
          transform: "translate(-50%, -50%)",
          width: "8%",
          height: "13%",
          filter: `drop-shadow(0 0 12px ${MM.gold})`,
        }}
      >
        <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="gold-on-navy" />
      </div>
      {/*  32 hour badge */}
      <div
        style={{
          position: "absolute",
          top: "8%",
          right: "8%",
          fontFamily: "Georgia, serif",
          fontWeight: 700,
          fontSize: 96,
          color: MM.gold,
          letterSpacing: "0.02em",
          ...TEXT_STROKE,
        }}
      >
        {hours}h
      </div>
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-04: "How?" — single word punch ─────────────────────────────────────
const Beat4: React.FC = () => {
  const f = useBeatFrame(BEATS.C4);
  const p = useBeatProgress(BEATS.C4);
  const scale = interpolate(p, [0, 1], [0.7, 1.1], { easing: easeOut });
  return (
    <Beat spec={BEATS.C4} dissolve={0.2}>
      <Plate />
      <Vignette intensity={0.6} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 280,
            color: MM.cream,
            letterSpacing: "-0.01em",
            transform: `scale(${scale})`,
            ...TEXT_STROKE,
          }}
        >
          How?
        </div>
      </AbsoluteFill>
    </Beat>
  );
};

// ── C2-05: Riders + packet boats ──────────────────────────────────────────
const Beat5: React.FC = () => {
  const f = useBeatFrame(BEATS.C5);
  const p = useBeatProgress(BEATS.C5);
  // First half: multiple riders; second half: transition to packet boats at port
  const ridersFade = interpolate(p, [0, 0.05, 0.42, 0.5], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const portFade = interpolate(p, [0.42, 0.55, 1], [0, 1, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.C5}>
      <Plate />
      <AbsoluteFill style={{ opacity: portFade }}>
        <MMSvg src={svgLib("bg/coastal-port-dock.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      {/*  Multiple riders moving */}
      <AbsoluteFill style={{ opacity: ridersFade }}>
        {[0, 1, 2].map((i) => {
          const speed = 1 + i * 0.3;
          const x = ((f * 8 * speed + i * 600) % 2400) - 200;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: `${30 + i * 22}%`,
                width: "12%",
                height: "20%",
                opacity: 0.85 - i * 0.15,
              }}
            >
              <MMSvg
                src={svgLib(i === 0 ? "lib/courier-rider-horse.svg" : "lib/horse-galloping.svg")}
                mode="silhouette"
              />
            </div>
          );
        })}
      </AbsoluteFill>
      {/*  Packet boat at dock + boat departing */}
      <AbsoluteFill style={{ opacity: portFade }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${15 + i * 30}%`,
              bottom: `${15 + Math.sin((f + i * 30) * 0.08) * 1.5}%`,
              width: "20%",
              height: "30%",
              transform:
                i === 1
                  ? `translate(${interpolate(p, [0.55, 1], [0, 400], { easing: ease })}px, 0)`
                  : "none",
            }}
          >
            <MMSvg src={svgLib("lib/packet-boat.svg")} mode="silhouette" />
          </div>
        ))}
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-06: Clerk at desk + spinning clock ────────────────────────────────
const Beat6: React.FC = () => {
  const f = useBeatFrame(BEATS.C6);
  const p = useBeatProgress(BEATS.C6);
  const clockAngle = (f * 360 * 4) / FPS; //  4 rev/sec
  const flicker = Math.sin(f * 0.5) * 0.2 + 0.85;
  return (
    <Beat spec={BEATS.C6}>
      <Plate />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "40%", height: "65%" }}>
          <MMSvg src={svgLib("lib/clerk-desk-silhouette.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      {/*  Candle flickering at corner */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "flex-end", padding: "8%", opacity: flicker }}>
        <div style={{ width: "8%", height: "26%" }}>
          <MMSvg src={svgLib("lib/candle-single.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      {/*  Clock face top-right with spinning hands */}
      <div
        style={{
          position: "absolute",
          top: "12%",
          right: "12%",
          width: 160,
          height: 160,
          borderRadius: "50%",
          border: `4px solid ${MM.gold}`,
          background: MM.bg,
          boxShadow: `0 0 30px ${MM.gold}66`,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 4,
            height: 60,
            background: MM.gold,
            transform: `translate(-50%, -100%) rotate(${clockAngle}deg)`,
            transformOrigin: "bottom center",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 3,
            height: 45,
            background: MM.cream,
            transform: `translate(-50%, -100%) rotate(${clockAngle * 12}deg)`,
            transformOrigin: "bottom center",
          }}
        />
      </div>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── C2-07: Quill writes letter → mailbag rejected ────────────────────────
const Beat7: React.FC = () => {
  const f = useBeatFrame(BEATS.C7);
  const p = useBeatProgress(BEATS.C7);
  // 0-0.5 quill+letter; 0.5-1 mailbag with X
  const quillFade = interpolate(p, [0, 0.05, 0.42, 0.5], [0, 1, 1, 0]);
  const mailbagFade = interpolate(p, [0.42, 0.55, 1], [0, 1, 1]);
  const xLength = interpolate(p, [0.55, 0.85], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.C7}>
      <Plate />
      <Vignette intensity={0.7} />
      <AbsoluteFill style={{ opacity: quillFade }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "30%", height: "50%", transform: "translate(-25%, 0)" }}>
            <MMSvg src={svgLib("lib/quill-and-inkwell.svg")} mode="navy-cream" />
          </div>
        </AbsoluteFill>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "26%", height: "26%", transform: "translate(25%, 0)" }}>
            <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: mailbagFade }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "32%", height: "55%" }}>
            <MMSvg src={svgLib("unique/public-mailbag-rejected.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
        {/*  X stroke draws on */}
        <svg
          viewBox="0 0 600 600"
          style={{ position: "absolute", left: "30%", top: "20%", width: "40%", height: "60%" }}
        >
          <line
            x1={50}
            y1={50}
            x2={50 + xLength * 500}
            y2={50 + xLength * 500}
            stroke={MM.red}
            strokeWidth={20}
            opacity={0.95}
            style={{ filter: `drop-shadow(0 0 14px ${MM.red})` }}
          />
          <line
            x1={550}
            y1={50}
            x2={550 - xLength * 500}
            y2={50 + xLength * 500}
            stroke={MM.red}
            strokeWidth={20}
            opacity={0.95}
            style={{ filter: `drop-shadow(0 0 14px ${MM.red})` }}
          />
        </svg>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-08: Letter hops between hand → horse → boat ───────────────────────
const Beat8: React.FC = () => {
  const f = useBeatFrame(BEATS.C8);
  const p = useBeatProgress(BEATS.C8);
  // Three "stations" left to right
  const stations = [
    { src: "unique/gloved-hand-icon.svg", label: "HANDS", x: "18%" },
    { src: "lib/horse-galloping.svg", label: "HORSES", x: "50%" },
    { src: "lib/packet-boat.svg", label: "BOATS", x: "82%" },
  ];
  // Letter hops 0-0.3 hand, 0.3-0.6 horse, 0.6-0.9 boat
  const stationIndex = p < 0.3 ? 0 : p < 0.6 ? 1 : 2;
  const xFrac = parseFloat(stations[stationIndex].x) / 100;
  return (
    <Beat spec={BEATS.C8}>
      <Plate />
      <Vignette intensity={0.65} />
      {/*  Three station icons */}
      {stations.map((s, i) => {
        const lit = stationIndex === i ? 1 : 0.35;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: s.x,
              top: "55%",
              transform: "translate(-50%, -50%)",
              width: "14%",
              height: "30%",
              opacity: lit,
              filter:
                stationIndex === i
                  ? `drop-shadow(0 0 16px ${MM.gold})`
                  : "none",
              transition: "none",
            }}
          >
            <MMSvg src={svgLib(s.src)} mode={stationIndex === i ? "navy-gold" : "silhouette"} />
          </div>
        );
      })}
      {stations.map((s, i) => (
        <div
          key={s.label}
          style={{
            position: "absolute",
            left: s.x,
            top: "78%",
            transform: "translateX(-50%)",
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 22,
            color: stationIndex === i ? MM.gold : MM.cream,
            opacity: stationIndex === i ? 1 : 0.5,
            letterSpacing: "0.18em",
            ...TEXT_STROKE,
          }}
        >
          {s.label}
        </div>
      ))}
      {/*  Letter sprite hops between */}
      <div
        style={{
          position: "absolute",
          left: `${xFrac * 100}%`,
          top: "30%",
          transform: "translate(-50%, -50%)",
          width: "10%",
          height: "10%",
          filter: `drop-shadow(0 0 18px ${MM.gold})`,
        }}
      >
        <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
      </div>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-09: Three figures struck through in sequence ───────────────────────
const Beat9: React.FC = () => {
  const f = useBeatFrame(BEATS.C9);
  const p = useBeatProgress(BEATS.C9);
  const figs = [
    { src: "unique/customs-officer.svg", label: "CUSTOMS OFFICER", at: 0 },
    { src: "unique/competing-banker.svg", label: "BANKER", at: 0.34 },
    { src: "unique/kings-spy.svg", label: "KING'S SPY", at: 0.68 },
  ];
  return (
    <Beat spec={BEATS.C9}>
      <Plate />
      <Vignette intensity={0.7} />
      {figs.map((fig, i) => {
        const startP = fig.at;
        const localP = Math.max(0, Math.min(1, (p - startP) / 0.32));
        const fadeIn = interpolate(localP, [0, 0.25], [0, 1], { extrapolateRight: "clamp" });
        const slashLength = interpolate(localP, [0.4, 0.85], [0, 1], { extrapolateRight: "clamp" });
        const dimAfter = interpolate(localP, [0.85, 1], [1, 0.35], { extrapolateRight: "clamp" });
        return (
          <div
            key={fig.label}
            style={{
              position: "absolute",
              left: `${15 + i * 28}%`,
              top: "20%",
              width: "22%",
              height: "70%",
              opacity: fadeIn * dimAfter,
            }}
          >
            <MMSvg src={svgLib(fig.src)} mode="silhouette" />
            <div
              style={{
                position: "absolute",
                left: 0,
                top: "50%",
                width: `${slashLength * 100}%`,
                height: 12,
                background: MM.red,
                transform: "rotate(-20deg)",
                transformOrigin: "left center",
                opacity: 0.9,
                boxShadow: `0 0 14px ${MM.red}`,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: 0,
                bottom: -40,
                width: "100%",
                fontFamily: "Georgia, serif",
                fontWeight: 700,
                fontSize: 18,
                color: MM.cream,
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
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-10: Roworth at Waterloo ────────────────────────────────────────────
const Beat10: React.FC = () => {
  const f = useBeatFrame(BEATS.C10);
  const p = useBeatProgress(BEATS.C10);
  return (
    <Beat spec={BEATS.C10}>
      <Plate />
      <MMSvg src={svgLib("bg/waterloo-aftermath.svg")} mode="ink-cream" />
      <Vignette intensity={0.78} />
      {/*  Cannon smoke drifting */}
      <AbsoluteFill
        style={{
          opacity: 0.6,
          transform: `translate(${(f * 6) % 100}px, 0)`,
        }}
      >
        <MMSvg src={svgLib("lib/cannon-smoke-cloud.svg")} mode="shadow" />
      </AbsoluteFill>
      <DustParticles frame={f} count={50} intensity={0.5} />
      {/*  Roworth on horse, foreground */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingBottom: "8%" }}>
        <div style={{ width: "20%", height: "55%" }}>
          <MMSvg src={svgLib("lib/roworth-courier-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-11: Three "doesn't wait" sub-beats ─────────────────────────────────
const Beat11: React.FC = () => {
  const f = useBeatFrame(BEATS.C11);
  const p = useBeatProgress(BEATS.C11);
  // 0-0.3 Roworth turns; 0.3-0.65 Wellington gestures, Roworth ignores; 0.65-1 wagon arrives empty foreground
  const phase = p < 0.3 ? 0 : p < 0.65 ? 1 : 2;
  return (
    <Beat spec={BEATS.C11}>
      <Plate />
      <MMSvg src={svgLib("bg/waterloo-aftermath.svg")} mode="ink-cream" />
      <Vignette intensity={0.78} />
      {/*  Phase 0: Roworth alone, head-turn */}
      <AbsoluteFill style={{ opacity: phase === 0 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div
            style={{
              width: "22%",
              height: "65%",
              transform: `scaleX(${interpolate(p, [0, 0.3], [-1, 1])})`,
            }}
          >
            <MMSvg src={svgLib("lib/roworth-courier-portrait.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {/*  Phase 1: Wellington in BG + Roworth FG */}
      <AbsoluteFill style={{ opacity: phase === 1 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", paddingLeft: "10%" }}>
          <div style={{ width: "16%", height: "50%", opacity: 0.55 }}>
            <MMSvg src={svgLib("lib/wellington-silhouette.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
        <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingRight: "12%" }}>
          <div style={{ width: "20%", height: "60%" }}>
            <MMSvg src={svgLib("lib/roworth-courier-portrait.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {/*  Phase 2: Wagon arrives, foreground empty */}
      <AbsoluteFill style={{ opacity: phase === 2 ? 1 : 0 }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div
            style={{
              width: "32%",
              height: "40%",
              transform: `translate(${interpolate(p, [0.65, 1], [-1500, 0], {
                easing: ease,
              })}px, 0)`,
            }}
          >
            <MMSvg src={svgLib("lib/dispatch-wagon.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C2-12: Roworth rides north — closer ───────────────────────────────────
const Beat12: React.FC = () => {
  const f = useBeatFrame(BEATS.C12);
  const p = useBeatProgress(BEATS.C12);
  const scale = interpolate(p, [0, 1], [1, 0.4], { easing: ease });
  const y = interpolate(p, [0, 1], [0, -200], { easing: ease });
  return (
    <Beat spec={BEATS.C12}>
      <Plate />
      <MMSvg src={svgLib("bg/waterloo-aftermath.svg")} mode="ink-cream" />
      <Vignette intensity={0.7} />
      {/*  Dust trail */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {Array.from({ length: 40 }).map((_, i) => {
          const seed = i * 89;
          const trailX = (seed * 31) % 1920;
          const trailY = 540 + (((seed * 47) % 400) - 200);
          const opacity = ((seed * 13) % 50) / 100 + 0.1;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: trailX,
                top: trailY + (f * 2) % 50,
                width: 4,
                height: 4,
                background: MM.cream,
                opacity: opacity * (1 - p) * 0.6,
              }}
            />
          );
        })}
      </AbsoluteFill>
      {/*  Roworth shrinks into distance */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "20%",
            height: "55%",
            transform: `translate(0, ${y}px) scale(${scale})`,
          }}
        >
          <MMSvg src={svgLib("lib/roworth-courier-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── Composition root ──────────────────────────────────────────────────────
export const LetterDynastyChapter2V2: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
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
      <FilmGrain frame={frame} opacity={0.045} />
    </AbsoluteFill>
  );
};
