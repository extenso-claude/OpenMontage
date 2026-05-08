/**
 * Letter Dynasty — Hook (Approach A: Single Plate Slow Breath).
 *
 * 11 beats, 71.08s VO, sub-shaft of light, micro-zoom, drift, stroke draw-on,
 * gold accents via MMSvg recolor.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
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
  microZoom,
  parallax,
  PeriodTitle,
  Plate,
  TEXT_STROKE,
  Vignette,
  driftTransform,
  ease,
  easeOut,
  useBeatFrame,
  useBeatProgress,
} from "./beat-helpers";

const HOOK_DURATION_S = 71.08;
export const LETTER_HOOK_V2_DURATION_FRAMES = Math.ceil(HOOK_DURATION_S * FPS);

const BEATS: Record<string, BeatSpec> = {
  H1: { id: "H-01", start: 0.0, end: 9.3 },
  H2: { id: "H-02", start: 10.36, end: 15.82 },
  H3: { id: "H-03", start: 16.94, end: 18.12 },
  H4: { id: "H-04", start: 19.1, end: 21.66 },
  H5: { id: "H-05", start: 22.74, end: 29.12 },
  H6: { id: "H-06", start: 29.12, end: 37.62 },
  H7: { id: "H-07", start: 38.8, end: 42.02 },
  H8: { id: "H-08", start: 42.58, end: 47.98 },
  H9: { id: "H-09", start: 48.7, end: 55.42 },
  H10: { id: "H-10", start: 55.42, end: 62.28 },
  H11: { id: "H-11", start: 63.02, end: 70.58 },
};

const HeroPlate: React.FC<{
  src: string;
  mode?: Parameters<typeof MMSvg>[0]["mode"];
  scale?: number;
  translate?: { x: number; y: number };
  width?: string;
  height?: string;
}> = ({ src, mode = "navy-cream", scale = 1, translate = { x: 0, y: 0 }, width = "70%", height = "70%" }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
    <div
      style={{
        width,
        height,
        transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
      }}
    >
      <MMSvg src={src} mode={mode} />
    </div>
  </AbsoluteFill>
);

// ── Beat 1 — Channel dawn + letter slide-in ───────────────────────────────
const Beat1: React.FC = () => {
  const f = useBeatFrame(BEATS.H1);
  const p = useBeatProgress(BEATS.H1);
  // Letter slides in from left over frames 60-150 (2.5s-6.25s)
  const letterX = interpolate(f, [60, 150], [-1400, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  const letterScale = microZoom(p, 0.04);
  return (
    <Beat spec={BEATS.H1}>
      <Plate />
      <AbsoluteFill style={{ opacity: interpolate(p, [0, 0.4], [0, 1], { extrapolateRight: "clamp" }) }}>
        <MMSvg src={svgLib("bg/english-channel-dawn.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "55%",
            height: "55%",
            transform: `translate(${letterX}px, 0) scale(${letterScale})`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.45} />
    </Beat>
  );
};

// ── Beat 2 — Crown rider + Admiralty parallax ─────────────────────────────
const Beat2: React.FC = () => {
  const f = useBeatFrame(BEATS.H2);
  const p = useBeatProgress(BEATS.H2);
  // Letter glides left-to-right faster than rider
  const letterX = interpolate(p, [0, 1], [-1100, 1100], { easing: ease });
  const riderX = interpolate(p, [0, 1], [-300, 300], { easing: ease });
  // Admiralty emblem appears at "Admiralty" word (~5s in, p~0.92)
  const admOpacity = interpolate(p, [0.85, 0.95, 1.0], [0, 1, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <Beat spec={BEATS.H2}>
      <Plate />
      <Vignette intensity={0.75} />
      {/*  Background — distant rider, slower */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "30%",
            height: "30%",
            opacity: 0.55,
            transform: `translate(${riderX}px, 80px)`,
          }}
        >
          <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      {/*  Foreground — letter, faster */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "32%",
            height: "32%",
            transform: `translate(${letterX}px, -40px)`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      {/*  Admiralty emblem fades up at end */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", padding: "0 8% 0 0", opacity: admOpacity }}>
        <div style={{ width: "22%", height: "30%" }}>
          <MMSvg src={svgLib("lib/admiralty-emblem.svg")} mode="gold-on-navy" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── Beat 3 — Foreign Office quick flash ───────────────────────────────────
const Beat3: React.FC = () => {
  const f = useBeatFrame(BEATS.H3);
  const p = useBeatProgress(BEATS.H3);
  const letterX = interpolate(p, [0, 1], [-700, 700], { easing: easeOut });
  return (
    <Beat spec={BEATS.H3} dissolve={0.3}>
      <Plate />
      <Vignette intensity={0.7} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "30%", height: "40%" }}>
          <MMSvg src={svgLib("lib/foreign-office-emblem.svg")} mode="gold-on-navy" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "28%",
            height: "28%",
            transform: `translate(${letterX}px, 0)`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── Beat 4 — King silhouette ──────────────────────────────────────────────
const Beat4: React.FC = () => {
  const f = useBeatFrame(BEATS.H4);
  const p = useBeatProgress(BEATS.H4);
  // King fades in 0->0.3, holds, throne dissolves at 0.7->1
  const kingOpacity = interpolate(p, [0, 0.25, 0.7, 1.0], [0, 1, 1, 0.4], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const letterX = interpolate(p, [0.2, 0.85], [-700, 700], { easing: ease });
  return (
    <Beat spec={BEATS.H4}>
      <Plate />
      <Vignette intensity={0.78} />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", opacity: kingOpacity }}
      >
        <div style={{ width: "55%", height: "70%" }}>
          <MMSvg src={svgLib("lib/king-george-iii-silhouette.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "26%",
            height: "26%",
            transform: `translate(${letterX}px, -30px)`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.4} />
    </Beat>
  );
};

// ── Beat 5 — London skyline + couriers ────────────────────────────────────
const Beat5: React.FC = () => {
  const f = useBeatFrame(BEATS.H5);
  const p = useBeatProgress(BEATS.H5);
  const skylineX = -parallax(f, 18); //  slow drift
  const courier1X = interpolate(p, [0.2, 1], [1500, -200], { easing: ease });
  const courier2X = interpolate(p, [0.4, 1], [1500, 200], { easing: ease });
  return (
    <Beat spec={BEATS.H5}>
      <Plate />
      {/*  Far background — drifting skyline */}
      <AbsoluteFill
        style={{ transform: `translate(${skylineX}px, 0)`, opacity: 0.85 }}
      >
        <MMSvg src={svgLib("bg/london-skyline-dawn.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.6} />
      {/*  Couriers riding in */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center" }}>
        <div
          style={{
            width: "22%",
            height: "25%",
            transform: `translate(${courier1X}px, -50px)`,
          }}
        >
          <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center" }}>
        <div
          style={{
            width: "18%",
            height: "20%",
            transform: `translate(${courier2X}px, 20px)`,
            opacity: 0.7,
          }}
        >
          <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <DustParticles frame={f} count={20} intensity={0.3} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── Beat 6 — Stock Exchange + Nathan revealed (long beat, sub-tempo) ──────
const Beat6: React.FC = () => {
  const f = useBeatFrame(BEATS.H6);
  const p = useBeatProgress(BEATS.H6);
  // 0-3s dolly-in 1.0->1.15
  const dollyScale = interpolate(p, [0, 0.4], [1.0, 1.15], { easing: ease });
  // Nathan visible from 1s onward
  const nathanOpacity = interpolate(p, [0.05, 0.25], [0, 1], { extrapolateRight: "clamp" });
  // Light grows 0.4->1
  const lightI = interpolate(p, [0.4, 1.0], [0.3, 0.8], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.H6}>
      <Plate />
      <AbsoluteFill style={{ transform: `scale(${dollyScale})` }}>
        <MMSvg src={svgLib("bg/london-stock-exchange-interior.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <AbsoluteFill
        style={{ alignItems: "center", justifyContent: "center", opacity: nathanOpacity }}
      >
        <div style={{ width: "32%", height: "70%" }}>
          <MMSvg src={svgLib("lib/nathan-rothschild-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={lightI} />
    </Beat>
  );
};

// ── Beat 7 — Name reveal: "Nathan Mayer Rothschild" ───────────────────────
const Beat7: React.FC = () => {
  const f = useBeatFrame(BEATS.H7);
  const p = useBeatProgress(BEATS.H7);
  return (
    <Beat spec={BEATS.H7}>
      <Plate />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: 0.4 }}>
        <div style={{ width: "28%", height: "70%" }}>
          <MMSvg src={svgLib("lib/nathan-rothschild-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <Vignette intensity={0.6} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <PeriodTitle text="Nathan Mayer Rothschild" progress={p} size={86} />
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.4} />
    </Beat>
  );
};

// ── Beat 8 — Sun arc + coin stack growing ─────────────────────────────────
const Beat8: React.FC = () => {
  const f = useBeatFrame(BEATS.H8);
  const p = useBeatProgress(BEATS.H8);
  return (
    <Beat spec={BEATS.H8}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.85 }}>
        <MMSvg src={svgLib("unique/sun-arc-with-coins.svg")} mode="navy-gold" />
      </AbsoluteFill>
      <Vignette intensity={0.65} />
      <LightShaftAcross frame={f} intensity={0.3 + p * 0.3} />
    </Beat>
  );
};

// ── Beat 9 — Calendar time-jump (procedural — year roll-back 1815→1795) ───
const Beat9: React.FC = () => {
  const f = useBeatFrame(BEATS.H9);
  const p = useBeatProgress(BEATS.H9);
  const year = Math.round(1815 - p * 20);
  return (
    <Beat spec={BEATS.H9}>
      <Plate />
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 220,
            color: MM.cream,
            letterSpacing: "0.04em",
            ...TEXT_STROKE,
          }}
        >
          {year}
        </div>
        <div
          style={{
            marginTop: 24,
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 28,
            color: MM.gold,
            letterSpacing: "0.2em",
            ...TEXT_STROKE,
          }}
        >
          TWENTY YEARS BACK
        </div>
      </AbsoluteFill>
      {/*  Subtle particle drift like dust */}
      <DustParticles frame={f} count={40} intensity={0.5} />
    </Beat>
  );
};

// ── Beat 10 — Frankfurt alley → Five arrows ───────────────────────────────
const Beat10: React.FC = () => {
  const f = useBeatFrame(BEATS.H10);
  const p = useBeatProgress(BEATS.H10);
  // 0-0.45 = alley dolly-in; 0.45-1.0 = five arrows
  const showAlley = p < 0.5;
  const alleyScale = interpolate(p, [0, 0.45], [1.0, 1.18], { extrapolateRight: "clamp", easing: ease });
  const alleyOpacity = interpolate(p, [0, 0.05, 0.4, 0.5], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const arrowsOpacity = interpolate(p, [0.5, 0.6], [0, 1], {
    extrapolateRight: "clamp",
  });
  const arrowDraw = interpolate(p, [0.5, 1.0], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.H10}>
      <Plate />
      <AbsoluteFill style={{ transform: `scale(${alleyScale})`, opacity: alleyOpacity }}>
        <MMSvg src={svgLib("bg/frankfurt-judengasse-alley.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <AbsoluteFill style={{ opacity: arrowsOpacity }}>
        <AbsoluteFill style={{ opacity: 0.4 }}>
          <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
        </AbsoluteFill>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div
            style={{
              width: "50%",
              height: "50%",
              opacity: arrowDraw,
              transform: `scale(${0.7 + arrowDraw * 0.3})`,
            }}
          >
            <MMSvg src={svgLib("unique/five-arrow-fan-diagram.svg")} mode="gold-on-navy" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── Beat 11 — Coin + letter merge (thesis statement) ──────────────────────
const Beat11: React.FC = () => {
  const f = useBeatFrame(BEATS.H11);
  const p = useBeatProgress(BEATS.H11);
  // 0->0.55 letter+coin slide together; 0.55->1.0 hold + glow
  const coinX = interpolate(p, [0, 0.55], [-300, -10], { easing: ease });
  const letterX = interpolate(p, [0, 0.55], [300, 10], { easing: ease });
  const glow = interpolate(p, [0.5, 1.0], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.H11}>
      <Plate />
      <Vignette intensity={0.7} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "22%",
            height: "55%",
            transform: `translate(${coinX}px, 0)`,
          }}
        >
          <MMSvg src={svgLib("lib/coin-stack.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "28%",
            height: "28%",
            transform: `translate(${letterX}px, 0)`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      {/*  Gold glow burst at center */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(201,168,76,${
            glow * 0.5
          }) 0%, rgba(201,168,76,0) 30%)`,
          mixBlendMode: "screen",
        }}
      />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── Composition root ──────────────────────────────────────────────────────
export const LetterDynastyHookV2: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
      <Audio src={staticFile("letter-dynasty-hook.wav")} volume={1} />
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
      <FilmGrain frame={frame} opacity={0.045} />
    </AbsoluteFill>
  );
};
