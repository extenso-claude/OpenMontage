/**
 * Letter Dynasty — Chapter 1 (Approach C: Editorial Linework Reveal).
 *
 * 11 beats over 80.85s. Each beat is a "page" — paths draw on, fills bloom,
 * gold accent lights last. Map-of-Europe spine for the back half.
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
  FilmGrain,
  FPS,
  LightShaftAcross,
  PeriodTitle,
  Plate,
  TEXT_STROKE,
  Vignette,
  ease,
  easeOut,
  useBeatFrame,
  useBeatProgress,
} from "./beat-helpers";

const CHAPTER1_DURATION_S = 80.85;
export const LETTER_CHAPTER1_V2_DURATION_FRAMES = Math.ceil(
  CHAPTER1_DURATION_S * FPS
);

const BEATS: Record<string, BeatSpec> = {
  C1: { id: "C1-01", start: 0.0, end: 8.92 },
  C2: { id: "C1-02", start: 8.92, end: 15.48 },
  C3: { id: "C1-03", start: 16.24, end: 22.96 },
  C4: { id: "C1-04", start: 23.76, end: 29.28 },
  C5: { id: "C1-05", start: 30.0, end: 37.56 },
  C6: { id: "C1-06", start: 39.36, end: 45.96 },
  C7: { id: "C1-07", start: 45.96, end: 52.82 },
  C8: { id: "C1-08", start: 52.82, end: 61.32 },
  C9: { id: "C1-09", start: 61.32, end: 68.78 },
  C10: { id: "C1-10", start: 69.6, end: 77.56 },
  C11: { id: "C1-11", start: 77.56, end: 80.42 },
};

/**
 * Editorial linework reveal — image fades in with stroke draw-on suggestion,
 * then a subtle gold accent emerges last.
 */
const PageReveal: React.FC<{
  src: string;
  progress: number;
  mode?: Parameters<typeof MMSvg>[0]["mode"];
  scale?: number;
}> = ({ src, progress, mode = "ink-cream", scale = 1 }) => {
  const fadeIn = interpolate(progress, [0, 0.3], [0, 1], { extrapolateRight: "clamp" });
  const goldGlow = interpolate(progress, [0.55, 0.95], [0, 1], { extrapolateRight: "clamp" });
  return (
    <>
      <AbsoluteFill style={{ opacity: fadeIn, transform: `scale(${scale})` }}>
        <MMSvg src={src} mode={mode} />
      </AbsoluteFill>
      {/*  Gold accent overlay at the end */}
      <AbsoluteFill
        style={{
          opacity: goldGlow * 0.18,
          background: `radial-gradient(ellipse at 50% 60%, rgba(201,168,76,1) 0%, transparent 35%)`,
          mixBlendMode: "screen",
          pointerEvents: "none",
        }}
      />
    </>
  );
};

// ── C1-01: Three sub-pages — alley → house → portrait beginning ───────────
const Beat1: React.FC = () => {
  const f = useBeatFrame(BEATS.C1);
  const p = useBeatProgress(BEATS.C1);
  // 0-0.34: alley; 0.34-0.67: house; 0.67-1: Mayer enters
  return (
    <Beat spec={BEATS.C1}>
      <Plate />
      <AbsoluteFill style={{ opacity: interpolate(p, [0, 0.05, 0.30, 0.36], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <PageReveal src={svgLib("bg/frankfurt-judengasse-alley.svg")} progress={p / 0.33} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: interpolate(p, [0.30, 0.38, 0.62, 0.68], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <PageReveal src={svgLib("bg/mayer-house-frankfurt.svg")} progress={(p - 0.34) / 0.33} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: interpolate(p, [0.62, 0.70, 1.0], [0, 1, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "32%", height: "70%" }}>
            <MMSvg src={svgLib("lib/mayer-amschel-portrait.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── C1-02: Mayer name → pavement constraint ───────────────────────────────
const Beat2: React.FC = () => {
  const f = useBeatFrame(BEATS.C2);
  const p = useBeatProgress(BEATS.C2);
  return (
    <Beat spec={BEATS.C2}>
      <Plate />
      <AbsoluteFill style={{ opacity: interpolate(p, [0, 0.05, 0.30, 0.36], [0, 1, 1, 0], { extrapolateRight: "clamp" }) }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <PeriodTitle text="Mayer Amschel" progress={Math.min(1, p / 0.32)} size={88} />
        </AbsoluteFill>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: interpolate(p, [0.30, 0.38, 1.0], [0, 1, 1], { extrapolateRight: "clamp" }) }}>
        <PageReveal src={svgLib("unique/judengasse-pavement-divide.svg")} progress={(p - 0.32) / 0.68} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C1-03: Boundary map → five sons reveal ────────────────────────────────
const Beat3: React.FC = () => {
  const f = useBeatFrame(BEATS.C3);
  const p = useBeatProgress(BEATS.C3);
  return (
    <Beat spec={BEATS.C3}>
      <Plate />
      <AbsoluteFill style={{ opacity: interpolate(p, [0, 0.1, 0.55, 0.65], [0, 1, 1, 0], { extrapolateRight: "clamp" }) }}>
        <PageReveal src={svgLib("unique/frankfurt-map-judengasse-bounded.svg")} progress={p / 0.55} mode="ink-cream" />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: interpolate(p, [0.55, 0.7, 1.0], [0, 1, 1], { extrapolateRight: "clamp" }) }}>
        {/*  Mayer left, five sons sequentially appear right */}
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "20%", height: "55%", transform: "translate(-30%, 0)" }}>
            <MMSvg src={svgLib("lib/mayer-amschel-portrait.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
        {[0, 1, 2, 3, 4].map((i) => {
          const startP = 0.6 + i * 0.07;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.06));
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                top: "50%",
                left: `${48 + i * 8}%`,
                transform: "translateY(-50%)",
                width: "8%",
                height: "32%",
                opacity: localP,
              }}
            >
              <MMSvg src={svgLib("lib/rothschild-son-silhouette.svg")} mode="silhouette" />
            </div>
          );
        })}
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C1-04: General-with-map metaphor + Frankfurt pin ──────────────────────
const Beat4: React.FC = () => {
  const f = useBeatFrame(BEATS.C4);
  const p = useBeatProgress(BEATS.C4);
  const mapOpacity = interpolate(p, [0, 0.4], [0, 0.85], { extrapolateRight: "clamp" });
  const pinGlow = interpolate(p, [0.6, 1], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.C4}>
      <Plate />
      <AbsoluteFill style={{ opacity: mapOpacity }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      {/*  Mayer in foreground at left edge */}
      <AbsoluteFill style={{ alignItems: "flex-start", justifyContent: "center", padding: "0 0 0 5%" }}>
        <div style={{ width: "16%", height: "60%", opacity: 0.7 }}>
          <MMSvg src={svgLib("lib/mayer-amschel-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      {/*  Frankfurt pin (manual placement) */}
      <div
        style={{
          position: "absolute",
          top: "44%",
          left: "55%",
          width: 14,
          height: 14,
          borderRadius: "50%",
          background: MM.gold,
          opacity: pinGlow,
          boxShadow: `0 0 20px ${MM.gold}`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "39%",
          left: "55.5%",
          fontFamily: "Georgia, serif",
          fontWeight: 700,
          fontSize: 22,
          color: MM.gold,
          opacity: pinGlow,
          letterSpacing: "0.15em",
          ...TEXT_STROKE,
        }}
      >
        FRANKFURT
      </div>
      <Vignette intensity={0.6} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C1-05: Four city pins lighting up — London → Paris → Vienna → Naples ──
const Beat5: React.FC = () => {
  const f = useBeatFrame(BEATS.C5);
  const p = useBeatProgress(BEATS.C5);
  const cities = [
    { name: "LONDON", top: "32%", left: "40%", at: 0.05 },
    { name: "PARIS", top: "47%", left: "48%", at: 0.27 },
    { name: "VIENNA", top: "50%", left: "62%", at: 0.55 },
    { name: "NAPLES", top: "65%", left: "60%", at: 0.78 },
    { name: "FRANKFURT", top: "44%", left: "55%", at: 0 }, //  already shown
  ];
  return (
    <Beat spec={BEATS.C5}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.85 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      {cities.map((c) => {
        const localP = Math.max(0, Math.min(1, (p - c.at) / 0.08));
        return (
          <React.Fragment key={c.name}>
            <div
              style={{
                position: "absolute",
                top: c.top,
                left: c.left,
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: MM.gold,
                opacity: localP,
                boxShadow: `0 0 ${20 * localP}px ${MM.gold}`,
              }}
            />
            <div
              style={{
                position: "absolute",
                top: `calc(${c.top} - 30px)`,
                left: c.left,
                fontFamily: "Georgia, serif",
                fontWeight: 700,
                fontSize: 22,
                color: MM.gold,
                opacity: localP,
                letterSpacing: "0.15em",
                ...TEXT_STROKE,
              }}
            >
              {c.name}
            </div>
          </React.Fragment>
        );
      })}
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C1-06: Five arrows fan out → pivot ────────────────────────────────────
const Beat6: React.FC = () => {
  const f = useBeatFrame(BEATS.C6);
  const p = useBeatProgress(BEATS.C6);
  const arrowOpacity = interpolate(p, [0, 0.55], [0, 1], { extrapolateRight: "clamp" });
  const arrowScale = interpolate(p, [0, 0.55], [0.5, 1.0], { easing: easeOut });
  const dimOnPivot = interpolate(p, [0.55, 0.75], [1, 0.5], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.C6}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.4 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: arrowOpacity * dimOnPivot }}>
        <div
          style={{
            width: "55%",
            height: "55%",
            transform: `scale(${arrowScale})`,
          }}
        >
          <MMSvg src={svgLib("unique/five-arrow-fan-diagram.svg")} mode="gold-on-navy" />
        </div>
      </AbsoluteFill>
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C1-07: Network thesis begins — first lines connect cities ─────────────
const Beat7: React.FC = () => {
  const f = useBeatFrame(BEATS.C7);
  const p = useBeatProgress(BEATS.C7);
  const cities = [
    { name: "FRANKFURT", x: 0.55, y: 0.44 },
    { name: "LONDON", x: 0.40, y: 0.32 },
    { name: "PARIS", x: 0.48, y: 0.47 },
    { name: "VIENNA", x: 0.62, y: 0.50 },
    { name: "NAPLES", x: 0.60, y: 0.65 },
  ];
  // Build first-half network lines
  const pairs: [number, number][] = [
    [0, 1],
    [0, 2],
    [0, 3],
  ];
  return (
    <Beat spec={BEATS.C7}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.65 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <svg
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      >
        {pairs.map(([a, b], idx) => {
          const startP = idx * 0.3;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.4));
          const x1 = cities[a].x * 1920;
          const y1 = cities[a].y * 1080;
          const x2 = cities[b].x * 1920;
          const y2 = cities[b].y * 1080;
          const cx = x1 + (x2 - x1) * localP;
          const cy = y1 + (y2 - y1) * localP;
          return (
            <line
              key={idx}
              x1={x1}
              y1={y1}
              x2={cx}
              y2={cy}
              stroke={MM.gold}
              strokeWidth={2.5}
              opacity={0.85}
              style={{ filter: `drop-shadow(0 0 6px ${MM.gold})` }}
            />
          );
        })}
        {cities.map((c) => (
          <circle
            key={c.name}
            cx={c.x * 1920}
            cy={c.y * 1080}
            r={7}
            fill={MM.gold}
            style={{ filter: `drop-shadow(0 0 12px ${MM.gold})` }}
          />
        ))}
      </svg>
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C1-08: Full web build + pulse ─────────────────────────────────────────
const Beat8: React.FC = () => {
  const f = useBeatFrame(BEATS.C8);
  const p = useBeatProgress(BEATS.C8);
  const cities = [
    { x: 0.55, y: 0.44 },
    { x: 0.40, y: 0.32 },
    { x: 0.48, y: 0.47 },
    { x: 0.62, y: 0.50 },
    { x: 0.60, y: 0.65 },
  ];
  const pairs: [number, number][] = [];
  for (let a = 0; a < cities.length; a++) {
    for (let b = a + 1; b < cities.length; b++) pairs.push([a, b]);
  }
  const pulse = 0.7 + 0.3 * Math.sin((f * 2 * Math.PI) / (FPS * 3));
  return (
    <Beat spec={BEATS.C8}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.6 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <svg
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      >
        {pairs.map(([a, b], idx) => {
          const startP = idx * 0.07;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.2));
          const x1 = cities[a].x * 1920;
          const y1 = cities[a].y * 1080;
          const x2 = cities[b].x * 1920;
          const y2 = cities[b].y * 1080;
          const cx = x1 + (x2 - x1) * localP;
          const cy = y1 + (y2 - y1) * localP;
          return (
            <line
              key={idx}
              x1={x1}
              y1={y1}
              x2={cx}
              y2={cy}
              stroke={MM.gold}
              strokeWidth={2}
              opacity={0.6 * pulse}
              style={{ filter: `drop-shadow(0 0 5px ${MM.gold})` }}
            />
          );
        })}
        {cities.map((c, i) => (
          <circle
            key={i}
            cx={c.x * 1920}
            cy={c.y * 1080}
            r={8 + 2 * pulse}
            fill={MM.gold}
            opacity={pulse}
            style={{ filter: `drop-shadow(0 0 ${12 * pulse}px ${MM.gold})` }}
          />
        ))}
      </svg>
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── C1-09: Mayer dies → 5 banks emerge ────────────────────────────────────
const Beat9: React.FC = () => {
  const f = useBeatFrame(BEATS.C9);
  const p = useBeatProgress(BEATS.C9);
  const portraitDim = interpolate(p, [0, 0.4], [1, 0.2], { extrapolateRight: "clamp" });
  const candleOpacity = interpolate(p, [0, 0.35, 0.45, 0.5], [1, 1, 0.3, 0]);
  return (
    <Beat spec={BEATS.C9}>
      <Plate />
      <AbsoluteFill style={{ opacity: portraitDim }}>
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: "30%", height: "65%" }}>
            <MMSvg src={svgLib("lib/mayer-amschel-portrait.svg")} mode="silhouette" />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
      {/*  Candle to the side, flickers out */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", padding: "0 12% 0 0", opacity: candleOpacity }}>
        <div style={{ width: "8%", height: "30%" }}>
          <MMSvg src={svgLib("lib/candle-single.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      {/*  Five banks fade in second half */}
      <AbsoluteFill style={{ opacity: interpolate(p, [0.45, 0.7], [0, 1], { extrapolateRight: "clamp" }) }}>
        {[0, 1, 2, 3, 4].map((i) => {
          const startP = 0.5 + i * 0.06;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.06));
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${8 + i * 18}%`,
                bottom: "20%",
                width: "14%",
                height: "50%",
                opacity: localP,
                transform: `translateY(${(1 - localP) * 40}px)`,
              }}
            >
              <MMSvg src={svgLib("unique/rothschild-bank-facade-generic.svg")} mode="ink-cream" />
            </div>
          );
        })}
      </AbsoluteFill>
      <Vignette intensity={0.7} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C1-10: Five points + ledger glowing ───────────────────────────────────
const Beat10: React.FC = () => {
  const f = useBeatFrame(BEATS.C10);
  const p = useBeatProgress(BEATS.C10);
  const ledgerScale = interpolate(p, [0, 0.4], [0.7, 1], { easing: easeOut });
  const pulse = 0.7 + 0.3 * Math.sin((f * 2 * Math.PI) / (FPS * 2.5));
  const cities = [
    { x: 0.55, y: 0.44 },
    { x: 0.40, y: 0.32 },
    { x: 0.48, y: 0.47 },
    { x: 0.62, y: 0.50 },
    { x: 0.60, y: 0.65 },
  ];
  const pairs: [number, number][] = [];
  for (let a = 0; a < cities.length; a++) {
    for (let b = a + 1; b < cities.length; b++) pairs.push([a, b]);
  }
  return (
    <Beat spec={BEATS.C10}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.45 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <svg
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
      >
        {pairs.map(([a, b], idx) => (
          <line
            key={idx}
            x1={cities[a].x * 1920}
            y1={cities[a].y * 1080}
            x2={cities[b].x * 1920}
            y2={cities[b].y * 1080}
            stroke={MM.gold}
            strokeWidth={1.6}
            opacity={0.5 * pulse}
            style={{ filter: `drop-shadow(0 0 5px ${MM.gold})` }}
          />
        ))}
        {cities.map((c, i) => (
          <circle
            key={i}
            cx={c.x * 1920}
            cy={c.y * 1080}
            r={7 + pulse}
            fill={MM.gold}
            opacity={pulse}
          />
        ))}
      </svg>
      {/*  Ledger emerging center */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "30%",
            height: "30%",
            transform: `scale(${ledgerScale})`,
          }}
        >
          <MMSvg src={svgLib("lib/ledger-book.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(201,168,76,${
            0.25 * pulse
          }) 0%, transparent 28%)`,
          mixBlendMode: "screen",
        }}
      />
      <Vignette intensity={0.55} />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── C1-11: Gold glow seal hold ────────────────────────────────────────────
const Beat11: React.FC = () => {
  const f = useBeatFrame(BEATS.C11);
  const p = useBeatProgress(BEATS.C11);
  return (
    <Beat spec={BEATS.C11}>
      <Plate />
      <AbsoluteFill style={{ opacity: 0.4 }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "26%", height: "26%" }}>
          <MMSvg src={svgLib("lib/ledger-book.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(201,168,76,0.45) 0%, transparent 30%)`,
          mixBlendMode: "screen",
        }}
      />
      <Vignette intensity={0.6} />
      <LightShaftAcross frame={f} intensity={0.4} />
    </Beat>
  );
};

// ── Composition root ──────────────────────────────────────────────────────
export const LetterDynastyChapter1V2: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
      <Audio src={staticFile("letter-dynasty-chapter1.mp3")} volume={1} />
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
