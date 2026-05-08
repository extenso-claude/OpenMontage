/**
 * Letter That Built A Dynasty — CHAPTER 1: The Five Arrows.
 * Style: halftone-textured shapes (Saul Bass / mid-century).
 * 81s, 16 vignettes, 24fps, 1920×1080.
 *
 * Vertical tilt-up + Europe-map zoom-out.  Arrows arc to 5 cities via
 * parametric quadratic curves; pulses travel along network edges.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import mmTheme from "./components/brand/themes/midnight_magnates.json";

const C = {
  bg: mmTheme.bg,             // #080c16
  text: mmTheme.text,         // #f5f0e4
  gold: mmTheme.accent,       // #c9a84c
  goldDim: "#8c6e23",
  red: mmTheme.stampRed,      // #b41e1e
  paper: "#1a1408",
  haze: "#2a1f0e",
};

const FPS = 24;
const DURATION_S = 81;
export const LETTER_CHAPTER1_DURATION_FRAMES = Math.ceil(DURATION_S * FPS);

const ease = Easing.inOut(Easing.cubic);
const easeOut = Easing.out(Easing.cubic);

type V = { name: string; start: number; end: number };
const VIGNETTES: V[] = [
  { name: "frankfurt-skyline", start: 0,  end: 5  },
  { name: "alley-dive",        start: 5,  end: 10 },
  { name: "narrow-street",     start: 10, end: 15 },
  { name: "tilt-window",       start: 15, end: 20 },
  { name: "by-law-pavement",   start: 20, end: 26 },
  { name: "no-land",           start: 26, end: 30 },
  { name: "five-sons",         start: 30, end: 35 },
  { name: "europe-map",        start: 35, end: 42 },
  { name: "arrow-frankfurt",   start: 42, end: 46 },
  { name: "arrow-london",      start: 46, end: 49 },
  { name: "arrow-paris",       start: 49, end: 52 },
  { name: "arrow-vienna",      start: 52, end: 55 },
  { name: "arrow-naples",      start: 55, end: 58 },
  { name: "lines-pulses",      start: 58, end: 65 },
  { name: "envelopes-fly",     start: 65, end: 72 },
  { name: "five-banks-end",    start: 72, end: 81 },
];

const DISSOLVE_S = 0.6;

function vOpacity(frame: number, v: V): number {
  const startF = v.start * FPS;
  const endF = v.end * FPS;
  const dF = DISSOLVE_S * FPS;
  const fadeIn = interpolate(frame, [startF - dF / 2, startF + dF / 2], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease,
  });
  const fadeOut = interpolate(frame, [endF - dF / 2, endF + dF / 2], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease,
  });
  return Math.min(fadeIn, fadeOut);
}

function localFrame(frame: number, v: V): number { return frame - v.start * FPS; }
function localProgress(frame: number, v: V): number {
  const startF = v.start * FPS;
  const endF = v.end * FPS;
  return Math.max(0, Math.min(1, (frame - startF) / (endF - startF)));
}

// ── Halftone defs (SVG patterns) ────────────────────────────────────────────

const HalftoneDefs: React.FC = () => (
  <defs>
    {/* Fine halftone for warm mid-tone */}
    <pattern id="ht-warm" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
      <rect width="10" height="10" fill={C.haze} />
      <circle cx="5" cy="5" r="2.4" fill={C.gold} />
    </pattern>
    {/* Denser halftone for darker bg */}
    <pattern id="ht-dark" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="8" fill={C.bg} />
      <circle cx="4" cy="4" r="1.4" fill={C.goldDim} />
    </pattern>
    {/* Cream highlights */}
    <pattern id="ht-cream" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
      <rect width="9" height="9" fill={C.haze} />
      <circle cx="4.5" cy="4.5" r="2.6" fill={C.text} opacity="0.85" />
    </pattern>
    {/* Sparse halftone for fade-out edges */}
    <pattern id="ht-sparse" x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
      <rect width="14" height="14" fill={C.bg} />
      <circle cx="7" cy="7" r="1.8" fill={C.gold} opacity="0.7" />
    </pattern>
    {/* Vignette */}
    <radialGradient id="vignetteCh1" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stopColor={C.bg} stopOpacity={0} />
      <stop offset="80%" stopColor={C.bg} stopOpacity={0.5} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={1} />
    </radialGradient>
    <linearGradient id="ch1Shaft" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
      <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
    </linearGradient>
  </defs>
);

const ShimmerMotes: React.FC<{ frame: number; count?: number }> = ({ frame, count = 30 }) => (
  <>
    {Array.from({ length: count }).map((_, i) => {
      const seed = i * 137.5;
      const x = (seed * 17) % 1920;
      const y = (seed * 23 + frame * 0.4) % 1080;
      const op = 0.20 + ((seed * 0.31) % 0.20) + Math.sin(frame * 0.05 + i) * 0.1;
      return <circle key={i} cx={x} cy={y} r={1.2 + (i % 3) * 0.5} fill={C.gold} opacity={Math.max(0, op)} />;
    })}
  </>
);

// ── 5 city positions on Europe map (canvas coordinates) ─────────────────────
const CITIES = {
  frankfurt: { x: 1010, y: 480, label: "FRANKFURT" },
  london:    { x: 720,  y: 380, label: "LONDON" },
  paris:     { x: 880,  y: 580, label: "PARIS" },
  vienna:    { x: 1240, y: 540, label: "VIENNA" },
  naples:    { x: 1180, y: 760, label: "NAPLES" },
} as const;

const CITY_KEYS = ["frankfurt", "london", "paris", "vienna", "naples"] as const;

// Quadratic bezier helper: ease point along a curve from origin -> destination via control point
function bezPoint(t: number, p0: [number, number], p1: [number, number], p2: [number, number]): [number, number] {
  const x = (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0];
  const y = (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1];
  return [x, y];
}

// Build a quadratic bezier path string (for stroke-along-path effect)
function bezierPath(p0: [number, number], p1: [number, number], p2: [number, number]): string {
  return `M ${p0[0]},${p0[1]} Q ${p1[0]},${p1[1]} ${p2[0]},${p2[1]}`;
}

// Approximate quadratic bezier length
function bezLength(p0: [number, number], p1: [number, number], p2: [number, number]): number {
  let len = 0;
  let prev = p0;
  for (let i = 1; i <= 32; i++) {
    const t = i / 32;
    const cur = bezPoint(t, p0, p1, p2);
    len += Math.hypot(cur[0] - prev[0], cur[1] - prev[1]);
    prev = cur;
  }
  return len;
}

// ── Reusable map ────────────────────────────────────────────────────────────

/** Halftone-shaded map of Europe with country shapes */
const EuropeMap: React.FC<{ highlightFrankfurt?: boolean }> = ({ highlightFrankfurt }) => (
  <g>
    {/* Sea / void */}
    <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
    {/* Continent body — Europe outline (stylized) */}
    <path d="M 540,300 L 700,260 L 900,250 L 1120,260 L 1350,280 L 1500,330 L 1620,400 L 1700,500 L 1700,640 L 1640,760 L 1500,840 L 1340,890 L 1160,910 L 980,890 L 820,860 L 700,800 L 600,720 L 540,620 L 510,500 L 510,400 Z" fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
    {/* British isles */}
    <path d="M 600,330 L 700,300 L 740,360 L 760,440 L 720,500 L 660,500 L 600,460 L 580,400 Z" fill={highlightFrankfurt ? "url(#ht-warm)" : "url(#ht-cream)"} stroke={C.gold} strokeWidth={2} />
    <path d="M 580,310 L 620,290 L 650,310 L 640,340 L 600,340 Z" fill="url(#ht-warm)" stroke={C.gold} strokeWidth={1.5} />
    {/* Italian peninsula */}
    <path d="M 1100,690 L 1180,700 L 1230,760 L 1240,820 L 1200,860 L 1160,840 L 1130,780 Z" fill="url(#ht-cream)" stroke={C.gold} strokeWidth={2} />
    {/* Frankfurt highlight ring */}
    {highlightFrankfurt && (
      <circle cx={CITIES.frankfurt.x} cy={CITIES.frankfurt.y} r={50} fill="none" stroke={C.red} strokeWidth={3} opacity={0.8} />
    )}
  </g>
);

const CityNode: React.FC<{ city: keyof typeof CITIES; lit: number; pulsePhase?: number }> = ({ city, lit, pulsePhase = 0 }) => {
  const { x, y, label } = CITIES[city];
  const pulseR = 30 + Math.sin(pulsePhase) * 6;
  return (
    <g transform={`translate(${x},${y})`}>
      {/* Lit pulse */}
      <circle cx={0} cy={0} r={pulseR} fill={C.gold} opacity={lit * 0.18} />
      <circle cx={0} cy={0} r={20} fill={C.gold} opacity={lit * 0.55} />
      <circle cx={0} cy={0} r={12} fill={C.gold} opacity={lit} />
      <circle cx={0} cy={0} r={5} fill={C.bg} opacity={lit} />
      {/* Label */}
      <g opacity={lit}>
        <rect x={-72} y={26} width={144} height={28} fill={C.bg} stroke={C.gold} strokeWidth={1.5} />
        <text x={0} y={46} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={16} letterSpacing="3" stroke="#000" strokeWidth={1.2} paintOrder="stroke fill">{label}</text>
      </g>
    </g>
  );
};

// ── Vignette renderers ──────────────────────────────────────────────────────

const V01_FrankfurtSkyline: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Bird's-eye Frankfurt skyline silhouette in halftone
  const drift = (lf * 0.4) % 80;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      {/* Sky fading */}
      <rect x={0} y={0} width={1920} height={680} fill={C.bg} />
      <rect x={0} y={680} width={1920} height={400} fill="url(#ht-warm)" />
      {/* Skyline silhouettes — receding rows */}
      <path d="M 0,750 L 60,720 L 60,680 L 100,680 L 100,640 L 160,640 L 160,700 L 240,700 L 240,620 L 300,620 L 300,580 L 340,580 L 340,540 L 360,540 L 360,580 L 400,580 L 400,640 L 480,640 L 480,700 L 580,700 L 580,660 L 660,660 L 660,720 L 760,720 L 760,640 L 820,640 L 820,580 L 880,580 L 880,520 L 920,520 L 920,500 L 960,500 L 960,520 L 1020,520 L 1020,580 L 1080,580 L 1080,660 L 1180,660 L 1180,720 L 1300,720 L 1300,640 L 1380,640 L 1380,700 L 1500,700 L 1500,620 L 1580,620 L 1580,680 L 1700,680 L 1700,720 L 1840,720 L 1840,750 L 1920,750 L 1920,1080 L 0,1080 Z"
        fill={C.bg} stroke={C.goldDim} strokeWidth={2} />
      {/* Cathedral spire - Frankfurt's Dom */}
      <path d="M 940,500 L 950,440 L 950,400 L 945,360 L 940,320 L 935,360 L 935,400 L 935,440 L 945,500 Z" fill={C.bg} stroke={C.gold} strokeWidth={2} />
      {/* Bird crossing */}
      <g transform={`translate(${300 + drift * 4},${260})`} opacity={0.7}>
        <path d="M -16,0 Q -8,-6 0,0 Q 8,-6 16,0" stroke={C.gold} strokeWidth={2} fill="none" strokeLinecap="round" />
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="3" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">Frankfurt</text>
      <text x={120} y={155} fill={C.gold} fontFamily="Georgia, serif" fontSize={20} letterSpacing="4" opacity={0.85}>imperial free city · 1795</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V02_AlleyDive: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera dives DOWN into the alley — vertical scroll-zoom
  const camY = interpolate(lp, [0, 1], [-200, 200], { easing: ease });
  const zoom = interpolate(lp, [0, 1], [0.85, 1.1], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom + camY}) scale(${zoom})`}>
        {/* Two tall buildings flanking a narrow alley */}
        <rect x={200} y={0} width={620} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
        <rect x={1100} y={0} width={620} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
        {/* Window grids */}
        {Array.from({ length: 6 }).map((_, row) =>
          [0, 1, 2].map(col => (
            <g key={`l-${row}-${col}`}>
              <rect x={250 + col * 180} y={120 + row * 160} width={70} height={90} fill={C.bg} stroke={C.goldDim} strokeWidth={1.5} />
            </g>
          ))
        )}
        {Array.from({ length: 6 }).map((_, row) =>
          [0, 1, 2].map(col => (
            <g key={`r-${row}-${col}`}>
              <rect x={1150 + col * 180} y={120 + row * 160} width={70} height={90} fill={C.bg} stroke={C.goldDim} strokeWidth={1.5} />
            </g>
          ))
        )}
        {/* Single lit window mid-alley (the Rothschild house) */}
        <rect x={1180} y={520} width={70} height={90} fill={C.gold} opacity={0.85} stroke={C.gold} strokeWidth={2} />
        <line x1={1215} y1={520} x2={1215} y2={610} stroke={C.bg} strokeWidth={2} />
        <line x1={1180} y1={565} x2={1250} y2={565} stroke={C.bg} strokeWidth={2} />
        {/* Cobblestones at bottom */}
        <rect x={820} y={900} width={280} height={180} fill="url(#ht-warm)" />
        {[0, 1, 2, 3].map(i => (
          <g key={i}>
            <rect x={830 + i * 70} y={920} width={50} height={50} fill="none" stroke={C.goldDim} strokeWidth={1.2} />
            <rect x={870 + i * 70} y={980} width={50} height={50} fill="none" stroke={C.goldDim} strokeWidth={1.2} />
          </g>
        ))}
        {/* Light shaft */}
        <polygon points="900,540 1020,540 1080,1080 840,1080" fill="url(#ch1Shaft)" />
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.8} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">the Judengasse</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V03_NarrowStreet: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Static alley shot with halftone fog drifting
  const fogDrift = (lf * 0.6) % 80;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <rect x={300} y={0} width={500} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
      <rect x={1120} y={0} width={500} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
      {/* Lit window upper-mid */}
      <rect x={1180} y={400} width={80} height={100} fill={C.gold} stroke={C.gold} strokeWidth={2} />
      <line x1={1220} y1={400} x2={1220} y2={500} stroke={C.bg} strokeWidth={2} />
      <line x1={1180} y1={450} x2={1260} y2={450} stroke={C.bg} strokeWidth={2} />
      {/* Glow halo around lit window */}
      <circle cx={1220} cy={450} r={120} fill={C.gold} opacity={0.18} />
      {/* Window inhabitants suggested */}
      <ellipse cx={1220} cy={485} rx={20} ry={12} fill={C.bg} opacity={0.6} />
      {/* Halftone fog drifting (semi-transparent overlay) */}
      <rect x={-fogDrift} y={500} width={2400} height={300} fill="url(#ht-sparse)" opacity={0.4} />
      {/* Caption */}
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">a single dim street, a single cramped house</text>
      <ShimmerMotes frame={lf} count={18} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V04_TiltWindow: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tilt up into the lit window; Mayer's silhouette appears
  const camY = interpolate(lp, [0, 1], [80, -40], { easing: ease });
  const zoom = interpolate(lp, [0, 1], [1.0, 1.5], { easing: ease });
  const candleFlicker = 0.85 + Math.sin(lf * 0.6) * 0.1;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom + camY}) scale(${zoom})`}>
        {/* Building wall */}
        <rect x={400} y={0} width={1120} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
        {/* Window frame — large, central */}
        <rect x={760} y={300} width={400} height={460} fill={C.haze} stroke={C.gold} strokeWidth={4} />
        <line x1={960} y1={300} x2={960} y2={760} stroke={C.gold} strokeWidth={3} />
        <line x1={760} y1={530} x2={1160} y2={530} stroke={C.gold} strokeWidth={3} />
        {/* Inner lit room — warm halftone */}
        <rect x={780} y={320} width={360} height={420} fill={C.gold} opacity={candleFlicker} />
        <rect x={780} y={320} width={360} height={420} fill="url(#ht-cream)" opacity={0.4} />
        {/* Mayer's silhouette inside */}
        <g transform={`translate(960,560)`}>
          {/* Coat */}
          <path d="M -50,40 L -30,-30 L 30,-30 L 50,40 L 56,140 L -56,140 Z" fill={C.bg} stroke={C.bg} strokeWidth={2} />
          {/* Head with skullcap */}
          <ellipse cx={0} cy={-40} rx={24} ry={28} fill={C.bg} />
          <path d="M -22,-58 Q 0,-78 22,-58 L 22,-50 L -22,-50 Z" fill={C.bg} />
          {/* Beard */}
          <path d="M -16,-26 Q 0,-4 16,-26 L 14,-12 L -14,-12 Z" fill={C.bg} />
        </g>
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">a coin dealer named Mayer Amschel</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V05_ByLawPavement: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Mayer steps DOWN off pavement; another silhouette walks past on raised stone
  const stepP = interpolate(lp, [0.15, 0.55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stampP = interpolate(lp, [0.45, 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stampScale = interpolate(stampP, [0, 0.6, 1], [0.6, 1.2, 1.0], { easing: easeOut });
  // Other figure walks past
  const otherX = interpolate(lp, [0, 1], [200, 1700]);
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      {/* Sky glow above */}
      <rect x={0} y={0} width={1920} height={500} fill={C.bg} />
      <rect x={0} y={300} width={1920} height={300} fill="url(#ht-sparse)" opacity={0.5} />
      {/* Raised pavement (mid-frame) */}
      <rect x={0} y={620} width={1920} height={50} fill="url(#ht-cream)" stroke={C.gold} strokeWidth={2} />
      {/* Lower street level */}
      <rect x={0} y={670} width={1920} height={410} fill="url(#ht-warm)" />
      {/* Mayer steps DOWN — at lower level */}
      <g transform={`translate(${600},${670 + stepP * 60})`}>
        {/* Coat */}
        <path d="M -40,40 L -28,-30 L 28,-30 L 40,40 L 46,180 L -46,180 Z" fill={C.bg} stroke={C.bg} strokeWidth={2} />
        {/* Head */}
        <ellipse cx={0} cy={-44} rx={20} ry={24} fill={C.bg} />
        <path d="M -18,-60 Q 0,-78 18,-60 L 18,-52 L -18,-52 Z" fill={C.bg} />
        {/* Beard */}
        <path d="M -14,-30 Q 0,-10 14,-30 L 12,-16 L -12,-16 Z" fill={C.bg} />
      </g>
      {/* Other figure walking on raised stone */}
      <g transform={`translate(${otherX},610)`} opacity={0.85}>
        {/* Top hat */}
        <rect x={-14} y={-78} width={28} height={28} fill={C.bg} />
        <line x1={-18} y1={-50} x2={18} y2={-50} stroke={C.bg} strokeWidth={3} />
        {/* Head */}
        <circle cx={0} cy={-30} r={14} fill={C.bg} />
        {/* Coat */}
        <path d="M -28,-10 L -18,-16 L 18,-16 L 28,-10 L 34,140 L -34,140 Z" fill={C.bg} />
      </g>
      {/* BY LAW stamp top-right */}
      <g transform={`translate(1620,200) rotate(-12) scale(${stampScale})`} opacity={stampP}>
        <rect x={-180} y={-80} width={360} height={160} fill="none" stroke={C.red} strokeWidth={6} />
        <text x={0} y={-10} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={48} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">BY LAW</text>
        <text x={0} y={42} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={20} letterSpacing="4">— FRANKFURT —</text>
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">not allowed to walk on the same pavement after dark</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V06_NoLand: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Frankfurt map — alley parcel highlighted, rest grayed; camera zooms out
  const zoom = interpolate(lp, [0, 1], [2.0, 0.85], { easing: ease });
  const parcelPulse = 0.7 + Math.abs(Math.sin(lf * 0.3)) * 0.3;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <g transform={`translate(${960},${540}) scale(${zoom}) translate(-960,-540)`}>
        {/* Frankfurt outline (irregular blob) */}
        <path d="M 460,200 L 720,160 L 980,180 L 1240,200 L 1460,260 L 1560,400 L 1500,580 L 1340,720 L 1120,820 L 880,820 L 660,760 L 520,640 L 440,480 L 420,340 Z"
          fill="url(#ht-sparse)" stroke={C.goldDim} strokeWidth={2} opacity={0.6} />
        {/* Streets — grid lines */}
        {Array.from({ length: 8 }).map((_, i) => (
          <line key={`h-${i}`} x1={420} y1={300 + i * 70} x2={1560} y2={300 + i * 70} stroke={C.goldDim} strokeWidth={0.8} opacity={0.4} />
        ))}
        {Array.from({ length: 12 }).map((_, i) => (
          <line key={`v-${i}`} x1={460 + i * 100} y1={200} x2={460 + i * 100} y2={820} stroke={C.goldDim} strokeWidth={0.8} opacity={0.4} />
        ))}
        {/* Alley parcel — highlighted in red */}
        <rect x={950} y={490} width={30} height={80} fill={C.red} stroke={C.red} strokeWidth={3} opacity={parcelPulse} />
        <circle cx={965} cy={530} r={50 + Math.sin(lf * 0.3) * 10} fill="none" stroke={C.red} strokeWidth={2} opacity={0.7} />
        <text x={965} y={620} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={20} letterSpacing="4" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">ALLOWED</text>
      </g>
      {/* Outside grayed */}
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">not allowed to own land outside this alley</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V07_FiveSons: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Five small son-silhouettes appear in the lit window
  const window2P = interpolate(lp, [0, 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const sonsP = interpolate(lp, [0.3, 0.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      {/* Building wall */}
      <rect x={300} y={0} width={1320} height={1080} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={2} />
      {/* Lit window — wider for 5 sons */}
      <rect x={560} y={200} width={800} height={500} fill={C.haze} stroke={C.gold} strokeWidth={4} opacity={window2P} />
      <rect x={580} y={220} width={760} height={460} fill={C.gold} opacity={window2P * 0.85} />
      <rect x={580} y={220} width={760} height={460} fill="url(#ht-cream)" opacity={window2P * 0.3} />
      {/* 5 son silhouettes in row */}
      {[0, 1, 2, 3, 4].map(i => {
        const x = 660 + i * 160;
        const reveal = interpolate(sonsP, [i * 0.15, i * 0.15 + 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
        return (
          <g key={i} transform={`translate(${x},${500}) scale(${reveal})`}>
            <ellipse cx={0} cy={-40} rx={18} ry={22} fill={C.bg} />
            <path d="M -32,-10 L -22,-22 L 22,-22 L 32,-10 L 36,140 L -36,140 Z" fill={C.bg} />
          </g>
        );
      })}
      {/* Mayer in foreground — full silhouette, contemplating his sons */}
      <g transform={`translate(960,920)`}>
        <ellipse cx={0} cy={-40} rx={26} ry={32} fill={C.bg} />
        <path d="M -20,-66 Q 0,-86 20,-66 L 20,-58 L -20,-58 Z" fill={C.bg} />
        <path d="M -50,-10 L -32,-30 L 32,-30 L 50,-10 L 60,160 L -60,160 Z" fill={C.bg} />
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">and yet · he has five sons</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V08_EuropeMap: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera transitions to halftone Europe map; Mayer-as-general silhouette at bottom
  const mapP = interpolate(lp, [0, 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <g opacity={mapP}>
        <EuropeMap highlightFrankfurt />
        {/* Frankfurt city marker */}
        <circle cx={CITIES.frankfurt.x} cy={CITIES.frankfurt.y} r={10} fill={C.red} />
        <text x={CITIES.frankfurt.x} y={CITIES.frankfurt.y + 30} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={18} letterSpacing="3" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">FRANKFURT</text>
      </g>
      {/* Mayer-as-general silhouette at bottom */}
      <g transform="translate(960,1040)" opacity={mapP}>
        <ellipse cx={0} cy={-150} rx={32} ry={38} fill={C.bg} />
        <path d="M -28,-180 Q 0,-205 28,-180 L 28,-168 L -28,-168 Z" fill={C.bg} />
        <path d="M -64,-110 L -42,-130 L 42,-130 L 64,-110 L 72,40 L -72,40 Z" fill={C.bg} />
        {/* Hand pointing at map */}
        <line x1={50} y1={-110} x2={70} y2={-200} stroke={C.bg} strokeWidth={6} strokeLinecap="round" />
      </g>
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">he looks at them the way a general looks at a map</text>
      <ShimmerMotes frame={lf} count={24} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

// Generic vignette: arrow flies from Frankfurt to a target city, lights up the node
const V_ArrowFlight: React.FC<{ frame: number; v: V; target: keyof typeof CITIES; previousLit: (keyof typeof CITIES)[] }> = ({ frame, v, target, previousLit }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Origin is Frankfurt
  const origin: [number, number] = [CITIES.frankfurt.x, CITIES.frankfurt.y];
  const dest: [number, number] = [CITIES[target].x, CITIES[target].y];
  // Control point — perpendicular bias to make the arc "fly" overhead
  const midX = (origin[0] + dest[0]) / 2;
  const midY = (origin[1] + dest[1]) / 2;
  const dx = dest[0] - origin[0];
  const dy = dest[1] - origin[1];
  const len = Math.hypot(dx, dy);
  // Perpendicular vector (rotated 90 deg clockwise): (-dy, dx) normalized
  const nx = -dy / len;
  const ny = dx / len;
  const arcHeight = Math.min(180, len * 0.35);
  const ctrl: [number, number] = [midX + nx * arcHeight, midY + ny * arcHeight];
  const arrowT = interpolate(lp, [0.05, 0.85], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const [ax, ay] = bezPoint(arrowT, origin, ctrl, dest);
  // Arrow tangent angle
  const [ax2, ay2] = bezPoint(Math.max(0, arrowT - 0.02), origin, ctrl, dest);
  const angle = Math.atan2(ay - ay2, ax - ax2) * 180 / Math.PI;
  // Trail path (drawn with stroke-dasharray)
  const path = bezierPath(origin, ctrl, dest);
  const pathLen = bezLength(origin, ctrl, dest);
  const targetLit = arrowT >= 0.95 ? 1 : 0;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <EuropeMap highlightFrankfurt />
      {/* Existing lit nodes (from previous beats — persistent, dimmed) */}
      {previousLit.map((c, i) => <CityNode key={i} city={c} lit={0.85} pulsePhase={lf * 0.2 + i} />)}
      {/* Trail (gold line) */}
      <path d={path} stroke={C.gold} strokeWidth={2} fill="none" strokeDasharray={pathLen} strokeDashoffset={pathLen * (1 - arrowT)} opacity={0.7} />
      {/* Arrow */}
      {arrowT < 0.99 && (
        <g transform={`translate(${ax},${ay}) rotate(${angle})`}>
          <line x1={-30} y1={0} x2={20} y2={0} stroke={C.gold} strokeWidth={6} strokeLinecap="round" />
          <polygon points="20,-10 36,0 20,10" fill={C.gold} stroke="#5a4612" strokeWidth={1.5} />
          {/* Fletching */}
          <polygon points="-30,-6 -36,0 -30,6 -24,0" fill={C.goldDim} />
        </g>
      )}
      {/* Target node lights up */}
      <CityNode city={target} lit={targetLit} pulsePhase={lf * 0.2} />
      {/* Frankfurt origin always lit */}
      <CityNode city="frankfurt" lit={0.9} pulsePhase={lf * 0.2 + 4} />
      {/* Caption — city name + son name */}
      <g transform="translate(120,120)">
        <text fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">one son to {CITIES[target].label.toLowerCase()}</text>
      </g>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V14_LinesPulses: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Lines draw between all 5 city nodes; pulses travel
  const drawP = interpolate(lp, [0, 0.55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const allCities = ["frankfurt", "london", "paris", "vienna", "naples"] as const;
  // All pairwise edges
  const edges: [keyof typeof CITIES, keyof typeof CITIES][] = [];
  for (let i = 0; i < allCities.length; i++) {
    for (let j = i + 1; j < allCities.length; j++) {
      edges.push([allCities[i], allCities[j]]);
    }
  }
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <EuropeMap />
      {/* Edges */}
      {edges.map(([a, b], i) => {
        const ca = CITIES[a];
        const cb = CITIES[b];
        const len = Math.hypot(cb.x - ca.x, cb.y - ca.y);
        const reveal = interpolate(drawP, [i * 0.05, i * 0.05 + 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
        return (
          <g key={i}>
            <line x1={ca.x} y1={ca.y} x2={cb.x} y2={cb.y} stroke={C.gold} strokeWidth={1.8} opacity={reveal * 0.65} strokeDasharray={`${len} ${len}`} strokeDashoffset={len * (1 - reveal)} />
          </g>
        );
      })}
      {/* Pulses traveling along each edge */}
      {drawP > 0.6 && edges.map(([a, b], i) => {
        const ca = CITIES[a];
        const cb = CITIES[b];
        const phase = ((lf * 0.04) + i * 0.13) % 1;
        const t = phase;
        const px = ca.x + (cb.x - ca.x) * t;
        const py = ca.y + (cb.y - ca.y) * t;
        return <circle key={`p-${i}`} cx={px} cy={py} r={4} fill={C.gold} opacity={(drawP - 0.6) / 0.4 * 0.85} />;
      })}
      {/* All 5 nodes lit */}
      {allCities.map((c, i) => <CityNode key={c} city={c} lit={0.9} pulsePhase={lf * 0.18 + i} />)}
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">he sent them to listen to each other</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V15_EnvelopesFly: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tiny envelope silhouettes ricochet between nodes
  const allCities = ["frankfurt", "london", "paris", "vienna", "naples"] as const;
  const edges: [keyof typeof CITIES, keyof typeof CITIES][] = [];
  for (let i = 0; i < allCities.length; i++) {
    for (let j = i + 1; j < allCities.length; j++) {
      edges.push([allCities[i], allCities[j]]);
    }
  }
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <EuropeMap />
      {/* Edges (faint) */}
      {edges.map(([a, b], i) => {
        const ca = CITIES[a];
        const cb = CITIES[b];
        return <line key={i} x1={ca.x} y1={ca.y} x2={cb.x} y2={cb.y} stroke={C.gold} strokeWidth={1.2} opacity={0.45} />;
      })}
      {/* Envelopes flying both directions */}
      {edges.map(([a, b], i) => {
        const ca = CITIES[a];
        const cb = CITIES[b];
        const speed = 0.04 + (i % 3) * 0.012;
        const phase = ((lf * speed) + i * 0.27) % 1;
        const dir = i % 2 === 0 ? 1 : -1;
        const t = dir > 0 ? phase : 1 - phase;
        const ex = ca.x + (cb.x - ca.x) * t;
        const ey = ca.y + (cb.y - ca.y) * t;
        return (
          <g key={`e-${i}`} transform={`translate(${ex},${ey})`}>
            <rect x={-9} y={-6} width={18} height={12} fill={C.text} stroke="#3a2a14" strokeWidth={1} />
            <path d="M -9,-6 L 0,2 L 9,-6" fill="none" stroke="#3a2a14" strokeWidth={1} />
            <circle cx={0} cy={2} r={2} fill={C.red} />
          </g>
        );
      })}
      {/* All 5 nodes lit */}
      {allCities.map((c, i) => <CityNode key={c} city={c} lit={0.95} pulsePhase={lf * 0.18 + i} />)}
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">to write to each other · to trade information</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

const V16_FiveBanksEnd: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Mayer fades; 5 small bank buildings rise at each node; pulses speed up; camera pulls back
  const fadeP = interpolate(lp, [0, 0.30], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const banksP = interpolate(lp, [0.20, 0.65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const camPullback = interpolate(lp, [0.5, 1], [1, 0.85], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const allCities = ["frankfurt", "london", "paris", "vienna", "naples"] as const;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <HalftoneDefs />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ht-dark)" />
      <g transform={`translate(${960},${540}) scale(${camPullback}) translate(-960,-540)`}>
        <EuropeMap />
        {/* Edges (gold) */}
        {(() => {
          const edges: [keyof typeof CITIES, keyof typeof CITIES][] = [];
          for (let i = 0; i < allCities.length; i++) {
            for (let j = i + 1; j < allCities.length; j++) {
              edges.push([allCities[i], allCities[j]]);
            }
          }
          return edges.map(([a, b], i) => {
            const ca = CITIES[a];
            const cb = CITIES[b];
            const speed = 0.08;
            const phase = ((lf * speed) + i * 0.13) % 1;
            const t = phase;
            const px = ca.x + (cb.x - ca.x) * t;
            const py = ca.y + (cb.y - ca.y) * t;
            return (
              <g key={i}>
                <line x1={ca.x} y1={ca.y} x2={cb.x} y2={cb.y} stroke={C.gold} strokeWidth={1.5} opacity={0.55} />
                <circle cx={px} cy={py} r={4} fill={C.gold} opacity={0.85} />
              </g>
            );
          });
        })()}
        {/* Mayer silhouette fading in center */}
        <g opacity={fadeP}>
          <ellipse cx={CITIES.frankfurt.x} cy={CITIES.frankfurt.y - 60} rx={28} ry={32} fill={C.bg} stroke={C.gold} strokeWidth={1} />
          <path d="M -50,-10 L -32,-30 L 32,-30 L 50,-10 L 60,140 L -60,140 Z" transform={`translate(${CITIES.frankfurt.x},${CITIES.frankfurt.y - 30})`} fill={C.bg} stroke={C.gold} strokeWidth={1} />
        </g>
        {/* 5 small bank buildings rising at each node */}
        {allCities.map((c, i) => {
          const node = CITIES[c];
          const reveal = interpolate(banksP, [i * 0.08, i * 0.08 + 0.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
          const yOff = (1 - reveal) * 60;
          return (
            <g key={c} transform={`translate(${node.x},${node.y - 100 + yOff})`} opacity={reveal}>
              {/* Pediment */}
              <polygon points="-50,0 50,0 40,-20 -40,-20" fill="url(#ht-warm)" stroke={C.gold} strokeWidth={1.5} />
              {/* Body */}
              <rect x={-50} y={0} width={100} height={70} fill="url(#ht-warm)" stroke={C.gold} strokeWidth={1.5} />
              {/* Columns */}
              {[-30, -10, 10, 30].map((cx, j) => (
                <line key={j} x1={cx} y1={4} x2={cx} y2={66} stroke={C.gold} strokeWidth={1.2} />
              ))}
              {/* Door */}
              <rect x={-10} y={40} width={20} height={30} fill={C.bg} stroke={C.gold} strokeWidth={1} />
            </g>
          );
        })}
        {/* All 5 nodes lit */}
        {allCities.map((c, i) => <CityNode key={c} city={c} lit={0.9} pulsePhase={lf * 0.22 + i} />)}
      </g>
      {/* Caption */}
      <text x={120} y={120} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">five capitals · one mind · one family ledger</text>
      {/* Bottom cite */}
      <text x={960} y={1020} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={32} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill" opacity={banksP}>1812 · the family becomes the empire</text>
      <ShimmerMotes frame={lf} count={20} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh1)" />
    </svg>
  );
};

// ── Main ─────────────────────────────────────────────────────────────────────

export const LetterDynastyChapter1: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <Audio src={staticFile("letter-dynasty-chapter1.mp3")} />
      {VIGNETTES.map((v, i) => {
        const op = vOpacity(frame, v);
        if (op <= 0.001) return null;
        let content: React.ReactNode = null;
        switch (v.name) {
          case "frankfurt-skyline": content = <V01_FrankfurtSkyline frame={frame} v={v} />; break;
          case "alley-dive":        content = <V02_AlleyDive frame={frame} v={v} />; break;
          case "narrow-street":     content = <V03_NarrowStreet frame={frame} v={v} />; break;
          case "tilt-window":       content = <V04_TiltWindow frame={frame} v={v} />; break;
          case "by-law-pavement":   content = <V05_ByLawPavement frame={frame} v={v} />; break;
          case "no-land":           content = <V06_NoLand frame={frame} v={v} />; break;
          case "five-sons":         content = <V07_FiveSons frame={frame} v={v} />; break;
          case "europe-map":        content = <V08_EuropeMap frame={frame} v={v} />; break;
          case "arrow-frankfurt":   content = <V_ArrowFlight frame={frame} v={v} target="frankfurt" previousLit={[]} />; break;
          case "arrow-london":      content = <V_ArrowFlight frame={frame} v={v} target="london" previousLit={["frankfurt"]} />; break;
          case "arrow-paris":       content = <V_ArrowFlight frame={frame} v={v} target="paris" previousLit={["frankfurt", "london"]} />; break;
          case "arrow-vienna":      content = <V_ArrowFlight frame={frame} v={v} target="vienna" previousLit={["frankfurt", "london", "paris"]} />; break;
          case "arrow-naples":      content = <V_ArrowFlight frame={frame} v={v} target="naples" previousLit={["frankfurt", "london", "paris", "vienna"]} />; break;
          case "lines-pulses":      content = <V14_LinesPulses frame={frame} v={v} />; break;
          case "envelopes-fly":     content = <V15_EnvelopesFly frame={frame} v={v} />; break;
          case "five-banks-end":    content = <V16_FiveBanksEnd frame={frame} v={v} />; break;
        }
        return <AbsoluteFill key={i} style={{ opacity: op }}>{content}</AbsoluteFill>;
      })}
    </AbsoluteFill>
  );
};
