/**
 * Letter That Built A Dynasty — COLD OPEN.
 * Style: line-art / engraving / woodcut. Channel: Midnight Magnates.
 * 103s, 18 vignettes, 24fps, 1920×1080.
 *
 * Aesthetic: cream-and-gold strokes on near-black.  No fills — only strokes.
 * Crosshatching via SVG <pattern>.  Stroke-dasharray reveals for "etched" feel.
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
  bg: "#04060e",
  ink: "#0a0c14",
  text: mmTheme.text,         // #f5f0e4
  gold: mmTheme.accent,       // #c9a84c
  goldDim: "#8c6e23",
  red: mmTheme.stampRed,      // #b41e1e
  paper: "#1a1208",
};

const FPS = 24;
const DURATION_S = 103;
export const LETTER_COLD_OPEN_DURATION_FRAMES = Math.ceil(DURATION_S * FPS);

const ease = Easing.inOut(Easing.cubic);
const easeOut = Easing.out(Easing.cubic);

type V = { name: string; start: number; end: number };
const VIGNETTES: V[] = [
  { name: "wide-floor",      start: 0,   end: 6   },
  { name: "nathan-pillar",   start: 6,   end: 12  },
  { name: "broker-watch-1",  start: 12,  end: 17  },
  { name: "broker-watch-2",  start: 17,  end: 22  },
  { name: "nathan-eyes",     start: 22,  end: 27  },
  { name: "sell-card",       start: 27,  end: 32  },
  { name: "bond-cert",       start: 32,  end: 38  },
  { name: "rally-channel",   start: 38,  end: 44  },
  { name: "panic",           start: 44,  end: 49  },
  { name: "wellington-lost", start: 49,  end: 55  },
  { name: "sell-wave",       start: 55,  end: 61  },
  { name: "market-collapse", start: 61,  end: 66  },
  { name: "fall-fall-fall",  start: 66,  end: 71  },
  { name: "agents-emerge",   start: 71,  end: 77  },
  { name: "agent-track",     start: 77,  end: 83  },
  { name: "ledger-tally",    start: 83,  end: 89  },
  { name: "disaster-street", start: 89,  end: 95  },
  { name: "whitehall-end",   start: 95,  end: 103 },
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

// ── Reusable engraving primitives ───────────────────────────────────────────

/** SVG defs shared across all vignettes — crosshatch patterns + grain */
const EngravingDefs: React.FC = () => (
  <defs>
    {/* Crosshatch pattern: diagonal lines for shading */}
    <pattern id="hatch" x="0" y="0" width="6" height="6" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="6" y2="6" stroke={C.text} strokeWidth="0.8" opacity="0.5" />
    </pattern>
    <pattern id="hatchDense" x="0" y="0" width="4" height="4" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="4" y2="4" stroke={C.text} strokeWidth="0.7" opacity="0.7" />
    </pattern>
    <pattern id="hatchCross" x="0" y="0" width="6" height="6" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="6" y2="6" stroke={C.text} strokeWidth="0.7" opacity="0.5" />
      <line x1="6" y1="0" x2="0" y2="6" stroke={C.text} strokeWidth="0.7" opacity="0.5" />
    </pattern>
    {/* Vignette darken */}
    <radialGradient id="vignetteGrad" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stopColor={C.bg} stopOpacity={0} />
      <stop offset="80%" stopColor={C.bg} stopOpacity={0.6} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={1} />
    </radialGradient>
    {/* Soft brass shaft */}
    <linearGradient id="shaftCO" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
      <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
    </linearGradient>
  </defs>
);

/** Subtle grain texture overlay (dust + film grain) */
const GrainOverlay: React.FC<{ frame: number }> = ({ frame }) => (
  <>
    {Array.from({ length: 80 }).map((_, i) => {
      const seed = i * 137;
      const x = (seed * 19 + frame * 0.6) % 1920;
      const y = (seed * 23 + frame * 0.4) % 1080;
      return <circle key={i} cx={x} cy={y} r={0.7 + (i % 3) * 0.2} fill={C.text} opacity={0.06 + ((i % 5) * 0.02)} />;
    })}
  </>
);

/** Reveal a path with stroke-dasharray (drawing-in animation) */
const DrawPath: React.FC<{
  d: string; pathLength: number; progress: number;
  stroke?: string; strokeWidth?: number; opacity?: number;
}> = ({ d, pathLength, progress, stroke = C.text, strokeWidth = 1.5, opacity = 1 }) => {
  const dashOffset = pathLength * (1 - progress);
  return (
    <path
      d={d}
      stroke={stroke}
      strokeWidth={strokeWidth}
      fill="none"
      opacity={opacity}
      strokeDasharray={pathLength}
      strokeDashoffset={dashOffset}
      strokeLinecap="round"
    />
  );
};

/** Engraved figure: top-hatted gentleman with crosshatched coat (used for brokers) */
const EngravedGent: React.FC<{
  x: number; y: number; scale?: number;
  headRot?: number; armRaise?: number; coatHatch?: boolean;
  faceMood?: "neutral" | "alarm" | "still";
}> = ({ x, y, scale = 1, headRot = 0, armRaise = 0, coatHatch = true, faceMood = "neutral" }) => (
  <g transform={`translate(${x},${y}) scale(${scale})`}>
    {/* Coat (outline + hatch fill) */}
    <path d="M -42,40 L -28,-30 L 28,-30 L 42,40 L 38,140 L -38,140 Z"
      fill={coatHatch ? "url(#hatch)" : "none"} stroke={C.text} strokeWidth={1.2} />
    {/* Lapels */}
    <path d="M -28,-30 L -10,40 L 0,30 L 10,40 L 28,-30" fill="none" stroke={C.text} strokeWidth={1.2} />
    {/* Head + neck */}
    <g transform={`rotate(${headRot})`}>
      <circle cx={0} cy={-50} r={18} fill="none" stroke={C.text} strokeWidth={1.2} />
      <line x1={-8} y1={-32} x2={8} y2={-32} stroke={C.text} strokeWidth={1.2} />
      {faceMood === "alarm" && <circle cx={0} cy={-50} r={2.5} fill={C.text} />}
    </g>
    {/* Top hat */}
    <g transform={`rotate(${headRot})`}>
      <rect x={-14} y={-86} width={28} height={26} fill={C.bg} stroke={C.text} strokeWidth={1.2} />
      <line x1={-18} y1={-60} x2={18} y2={-60} stroke={C.text} strokeWidth={1.2} />
    </g>
    {/* Arm (raises with armRaise param) */}
    <line x1={28} y1={20} x2={50 + armRaise * 30} y2={20 - armRaise * 60} stroke={C.text} strokeWidth={1.5} strokeLinecap="round" />
    {/* If alarm: paper waved */}
    {faceMood === "alarm" && armRaise > 0.5 && (
      <rect x={50 + armRaise * 30 - 12} y={20 - armRaise * 60 - 18} width={24} height={18}
        fill="none" stroke={C.text} strokeWidth={1.2} transform={`rotate(${-15 + armRaise * 30} ${50 + armRaise * 30} ${20 - armRaise * 60})`} />
    )}
  </g>
);

const Pillar: React.FC<{ x: number; y: number; h?: number }> = ({ x, y, h = 480 }) => (
  <g transform={`translate(${x},${y})`}>
    <rect x={-26} y={0} width={52} height={h} fill="url(#hatch)" stroke={C.text} strokeWidth={1.2} />
    {/* Capital */}
    <rect x={-32} y={-12} width={64} height={12} fill="none" stroke={C.text} strokeWidth={1.2} />
    <rect x={-36} y={-22} width={72} height={10} fill="none" stroke={C.text} strokeWidth={1.2} />
    {/* Base */}
    <rect x={-36} y={h} width={72} height={12} fill="none" stroke={C.text} strokeWidth={1.2} />
    <rect x={-40} y={h + 12} width={80} height={10} fill="none" stroke={C.text} strokeWidth={1.2} />
    {/* Vertical fluting */}
    {[-18, -6, 6, 18].map((fx, i) => (
      <line key={i} x1={fx} y1={0} x2={fx} y2={h} stroke={C.text} strokeWidth={0.7} opacity={0.7} />
    ))}
  </g>
);

const ShaftLight: React.FC = () => (
  <polygon points="780,0 1140,0 1240,1080 680,1080" fill="url(#shaftCO)" />
);

// ── Vignette renderers ───────────────────────────────────────────────────────

const V01_WideFloor: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Drawing in: floor reveals stroke-by-stroke, dolly-in begins
  const drawP = interpolate(lp, [0, 0.85], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const zoom = interpolate(lp, [0, 1], [0.92, 1.0], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom}) scale(${zoom})`}>
        {/* Floor lines (perspective) */}
        <DrawPath d="M 0,940 L 1920,940" pathLength={1920} progress={drawP} strokeWidth={2} />
        <DrawPath d="M 0,990 L 1920,990" pathLength={1920} progress={drawP} strokeWidth={1.2} opacity={0.7} />
        <DrawPath d="M 0,1040 L 1920,1040" pathLength={1920} progress={drawP} strokeWidth={1} opacity={0.5} />
        {/* Vanishing-point perspective lines */}
        <DrawPath d="M 0,940 L 960,500" pathLength={1100} progress={drawP} strokeWidth={1} opacity={0.6} />
        <DrawPath d="M 1920,940 L 960,500" pathLength={1100} progress={drawP} strokeWidth={1} opacity={0.6} />
        {/* Far wall */}
        <DrawPath d="M 480,500 L 1440,500" pathLength={960} progress={drawP} strokeWidth={1.5} />
        {/* Pillars receding */}
        {drawP > 0.4 && [200, 600, 1320, 1720].map((px, i) => (
          <g key={i} opacity={(drawP - 0.4) / 0.6}>
            <Pillar x={px} y={460} h={480} />
          </g>
        ))}
        {/* Ceiling beam */}
        <DrawPath d="M 480,300 L 1440,300" pathLength={960} progress={drawP} strokeWidth={1.5} />
        <DrawPath d="M 480,300 L 480,500" pathLength={200} progress={drawP} strokeWidth={1.2} />
        <DrawPath d="M 1440,300 L 1440,500" pathLength={200} progress={drawP} strokeWidth={1.2} />
        {/* Skylight oculus */}
        <DrawPath d="M 800,300 Q 960,160 1120,300" pathLength={500} progress={drawP} strokeWidth={1.5} />
        {/* Crosshatch shading on far wall */}
        {drawP > 0.7 && (
          <g opacity={(drawP - 0.7) / 0.3}>
            <rect x={520} y={320} width={880} height={170} fill="url(#hatch)" opacity={0.6} />
          </g>
        )}
      </g>
      {/* Dust motes in shaft */}
      {Array.from({ length: 40 }).map((_, i) => {
        const seed = i * 113;
        const baseX = 760 + (seed * 7) % 400;
        const drift = (lf * 0.6 + seed) % 1080;
        return <circle key={i} cx={baseX + Math.sin((lf + i) * 0.05) * 8} cy={drift}
          r={1 + (i % 3) * 0.5} fill={C.gold} opacity={0.25 + ((i % 5) * 0.05)} />;
      })}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
      {/* Section label (very small, top-left, period correct) */}
      <text x={80} y={80} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={20} opacity={0.6} letterSpacing="2">London Stock Exchange · the trading floor</text>
    </svg>
  );
};

const V02_NathanPillar: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Slow dolly-in toward Nathan
  const zoom = interpolate(lp, [0, 1], [1.0, 1.18], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom}) scale(${zoom})`}>
        {/* Floor */}
        <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
        <line x1={0} y1={990} x2={1920} y2={990} stroke={C.text} strokeWidth={1} opacity={0.5} />
        {/* Pillars */}
        <Pillar x={300} y={460} h={480} />
        <Pillar x={1620} y={460} h={480} />
        {/* Nathan's pillar — taller, central */}
        <Pillar x={960} y={400} h={540} />
        {/* Nathan at his pillar (still, central) */}
        <EngravedGent x={960} y={830} scale={1.35} faceMood="still" coatHatch={false} />
        {/* Other figures around — animated micro-loops */}
        {[
          { x: 540, scale: 0.95, ph: 0 },
          { x: 720, scale: 0.85, ph: 1.3 },
          { x: 1180, scale: 0.92, ph: 0.6 },
          { x: 1380, scale: 0.88, ph: 2.1 },
        ].map((g, i) => {
          const head = Math.sin(lf * 0.1 + g.ph) * 8;
          const arm = (Math.sin(lf * 0.15 + g.ph) + 1) * 0.3;
          return <EngravedGent key={i} x={g.x} y={870} scale={g.scale} headRot={head} armRaise={arm} />;
        })}
        {/* Ceiling beams */}
        <line x1={300} y1={300} x2={1620} y2={300} stroke={C.text} strokeWidth={1.5} />
      </g>
      {/* Dust motes in shaft */}
      {Array.from({ length: 50 }).map((_, i) => {
        const seed = i * 113;
        const baseX = 800 + (seed * 7) % 320;
        const drift = (lf * 0.7 + seed) % 1080;
        return <circle key={i} cx={baseX + Math.sin((lf + i) * 0.05) * 8} cy={drift}
          r={1 + (i % 3) * 0.5} fill={C.gold} opacity={0.25 + ((i % 5) * 0.05)} />;
      })}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V03_BrokerWatch1: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera holds. One broker rotates head toward Nathan
  const headRot = interpolate(lp, [0.1, 0.7], [0, -45], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      {/* Floor */}
      <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
      {/* Pillar in center where Nathan stands */}
      <Pillar x={1300} y={400} h={540} />
      <EngravedGent x={1300} y={830} scale={1.0} faceMood="still" coatHatch={false} />
      {/* Foreground broker, turning head */}
      <EngravedGent x={620} y={840} scale={1.5} headRot={headRot} faceMood="neutral" />
      {/* Subtle hatching shading on broker */}
      <g transform="translate(620,840) scale(1.5)">
        <rect x={-42} y={40} width={84} height={100} fill="url(#hatchDense)" opacity={0.5} pointerEvents="none" />
      </g>
      {/* Crosshatch on right side (deepening shadow) */}
      <rect x={1200} y={200} width={720} height={840} fill="url(#hatch)" opacity={0.25} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V04_BrokerWatch2: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Two more brokers turn in sequence
  const head1 = interpolate(lp, [0.1, 0.5], [0, -38], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const head2 = interpolate(lp, [0.3, 0.7], [0, 35], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
      <Pillar x={960} y={400} h={540} />
      <EngravedGent x={960} y={830} scale={1.05} faceMood="still" coatHatch={false} />
      <EngravedGent x={420} y={840} scale={1.2} headRot={head1} />
      <EngravedGent x={1500} y={840} scale={1.15} headRot={head2} />
      <EngravedGent x={1700} y={870} scale={0.9} headRot={Math.sin(lf * 0.1) * 6} />
      {/* Deepened crosshatch shadow */}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#hatch)" opacity={0.18} pointerEvents="none" />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V05_NathanEyes: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tight on Nathan's face: zoom in dramatically
  const zoom = interpolate(lp, [0, 1], [1.5, 2.6], { easing: ease });
  // Eyes lift
  const eyeY = interpolate(lp, [0.3, 0.65], [4, -2], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom + 100}) scale(${zoom})`}>
        {/* Nathan, very tight */}
        <EngravedGent x={960} y={580} scale={3.5} faceMood="still" coatHatch={false} />
        {/* Eye detail (engraved iris) */}
        <g transform={`translate(960,440)`}>
          <line x1={-30} y1={eyeY - 5} x2={-12} y2={eyeY - 5} stroke={C.text} strokeWidth={2.5} />
          <line x1={12} y1={eyeY - 5} x2={30} y2={eyeY - 5} stroke={C.text} strokeWidth={2.5} />
          <circle cx={-21} cy={eyeY} r={3.5} fill={C.text} />
          <circle cx={21} cy={eyeY} r={3.5} fill={C.text} />
          {/* Crow's feet */}
          <line x1={-44} y1={-10 + eyeY} x2={-38} y2={-2 + eyeY} stroke={C.text} strokeWidth={1.2} />
          <line x1={-44} y1={-2 + eyeY} x2={-38} y2={6 + eyeY} stroke={C.text} strokeWidth={1.2} />
          <line x1={44} y1={-10 + eyeY} x2={38} y2={-2 + eyeY} stroke={C.text} strokeWidth={1.2} />
          <line x1={44} y1={-2 + eyeY} x2={38} y2={6 + eyeY} stroke={C.text} strokeWidth={1.2} />
        </g>
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V06_SellCard: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tight on Nathan's hand emerging with a small SELL card
  const cardSlide = interpolate(lp, [0.3, 0.85], [0, 80], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  // Ticker tape unspooling
  const tickerOffset = (lf * 1.6) % 80;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      {/* Ticker tape band at top */}
      <g transform={`translate(${-tickerOffset},120)`}>
        <line x1={-200} y1={20} x2={2200} y2={20} stroke={C.text} strokeWidth={1.5} />
        <line x1={-200} y1={70} x2={2200} y2={70} stroke={C.text} strokeWidth={1.5} />
        {[..."CONSOLS · SELL · CONSOLS · SELL · CONSOLS · SELL · CONSOLS · SELL · CONSOLS · SELL"].map((ch, i) => null)}
        {Array.from({ length: 14 }).map((_, i) => (
          <text key={i} x={-200 + i * 220} y={56} fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={28} letterSpacing="3">CONSOLS · SELL ·</text>
        ))}
      </g>
      {/* Tight hand and card */}
      <g transform="translate(960,540) scale(2.5)">
        {/* Hand emerging from coat sleeve */}
        <path d="M -80,80 L -20,80 L -10,120 L -90,120 Z" fill={C.bg} stroke={C.text} strokeWidth={1.2} />
        <ellipse cx={-50} cy={140} rx={40} ry={22} fill="none" stroke={C.text} strokeWidth={1.2} />
        {/* Card peeking out, slid distance grows */}
        <g transform={`translate(${-50 + cardSlide * 0.6},${140 + cardSlide * 0.3})`}>
          <rect x={-40} y={-22} width={80} height={44} fill={C.bg} stroke={C.text} strokeWidth={1.5} />
          <text x={0} y={6} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={20} letterSpacing="3">SELL</text>
          {/* Hatch shadow under card */}
          <rect x={-40} y={20} width={80} height={6} fill="url(#hatchDense)" opacity={0.5} />
        </g>
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V07_BondCert: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Bond certificate fills frame — ornate borders draw in
  const drawP = interpolate(lp, [0, 0.7], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const priceTick = Math.floor(interpolate(lp, [0.3, 1], [100, 96], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Bond certificate paper */}
      <rect x={300} y={140} width={1320} height={800} fill={C.paper} stroke={C.text} strokeWidth={2} />
      <rect x={320} y={160} width={1280} height={760} fill="none" stroke={C.text} strokeWidth={1} opacity={0.7} />
      {/* Decorative ornate border */}
      <DrawPath d="M 340,180 L 1580,180 L 1580,900 L 340,900 Z" pathLength={3920} progress={drawP} strokeWidth={1.5} stroke={C.gold} />
      {/* Corner ornaments */}
      {[[340, 180], [1580, 180], [340, 900], [1580, 900]].map(([cx, cy], i) => (
        <g key={i} transform={`translate(${cx},${cy})`}>
          <circle cx={0} cy={0} r={18} fill="none" stroke={C.gold} strokeWidth={1.5} />
          <circle cx={0} cy={0} r={10} fill="none" stroke={C.gold} strokeWidth={1} />
          <circle cx={0} cy={0} r={4} fill={C.gold} />
        </g>
      ))}
      {/* Title */}
      <text x={960} y={290} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={56} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">BRITISH CONSOLS</text>
      <text x={960} y={340} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3">His Majesty's Government Stock</text>
      {/* Decorative laurel */}
      <DrawPath d="M 700,380 Q 960,420 1220,380" pathLength={550} progress={drawP} strokeWidth={1.5} stroke={C.gold} />
      <DrawPath d="M 700,400 Q 960,440 1220,400" pathLength={550} progress={drawP} strokeWidth={1} stroke={C.gold} opacity={0.6} />
      {/* Price */}
      <text x={960} y={500} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={26} letterSpacing="3" opacity={0.85}>par value</text>
      <text x={960} y={720} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={200} letterSpacing="8" stroke="#000" strokeWidth={3} paintOrder="stroke fill">{priceTick}</text>
      {/* Subtle pulse ring */}
      <circle cx={960} cy={660} r={170 + Math.sin(lf * 0.15) * 6} fill="none" stroke={C.gold} strokeWidth={1.5} opacity={0.4} />
      <text x={960} y={830} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22} opacity={0.7}>Issued under His Majesty's seal · 1815</text>
      {/* Hatching texture on paper */}
      <rect x={300} y={140} width={1320} height={800} fill="url(#hatch)" opacity={0.08} pointerEvents="none" />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V08_RallyChannel: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Inset Channel motif on the certificate; price "100" pulses
  const drawP = interpolate(lp, [0, 0.7], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const pricePulse = 1 + Math.sin(lf * 0.25) * 0.05;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <rect x={300} y={140} width={1320} height={800} fill={C.paper} stroke={C.text} strokeWidth={2} />
      <rect x={320} y={160} width={1280} height={760} fill="none" stroke={C.text} strokeWidth={1} opacity={0.7} />
      {/* Title */}
      <text x={960} y={250} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={42} letterSpacing="4" stroke="#000" strokeWidth={2} paintOrder="stroke fill">VICTORY EXPECTED</text>
      <text x={960} y={290} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22}>news from Belgium imminent</text>
      {/* Channel motif inset — sailing ship over wavy line */}
      <g transform="translate(960,540)">
        <rect x={-300} y={-140} width={600} height={280} fill={C.bg} stroke={C.text} strokeWidth={1.5} />
        <DrawPath d="M -300,-140 L 300,-140" pathLength={600} progress={drawP} strokeWidth={1.5} />
        <DrawPath d="M -300,-140 L -300,140" pathLength={280} progress={drawP} strokeWidth={1.5} />
        {/* Wavy water line */}
        <DrawPath d="M -260,40 Q -200,30 -140,40 T 0,40 T 140,40 T 260,40" pathLength={520} progress={drawP} strokeWidth={1.5} stroke={C.text} />
        <DrawPath d="M -260,70 Q -200,60 -140,70 T 0,70 T 140,70 T 260,70" pathLength={520} progress={drawP} strokeWidth={1} opacity={0.6} />
        {/* Sailing ship */}
        {drawP > 0.6 && (
          <g transform="translate(0,-10)" opacity={(drawP - 0.6) / 0.4}>
            {/* Hull */}
            <path d="M -50,30 L 50,30 L 40,55 L -40,55 Z" fill="none" stroke={C.text} strokeWidth={1.5} />
            {/* Mast */}
            <line x1={0} y1={30} x2={0} y2={-80} stroke={C.text} strokeWidth={1.5} />
            {/* Sails */}
            <path d="M 0,-80 L -40,-30 L 0,-20 Z" fill="none" stroke={C.text} strokeWidth={1.5} />
            <path d="M 0,-80 L 40,-30 L 0,-20 Z" fill="url(#hatchDense)" stroke={C.text} strokeWidth={1.5} opacity={0.7} />
          </g>
        )}
      </g>
      {/* Price tag bottom right */}
      <g transform={`translate(1380,870) scale(${pricePulse})`}>
        <rect x={-90} y={-40} width={180} height={80} fill="none" stroke={C.gold} strokeWidth={2} />
        <text x={0} y={14} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={56} letterSpacing="4">100</text>
      </g>
      <text x={960} y={860} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22} opacity={0.85}>the bond should rally on victory</text>
      <rect x={300} y={140} width={1320} height={800} fill="url(#hatch)" opacity={0.08} pointerEvents="none" />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V09_Panic: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Wide of trading floor — brokers wide-eyed, papers raised
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
      <Pillar x={300} y={460} h={480} />
      <Pillar x={1620} y={460} h={480} />
      {/* Frantic brokers — arms raised, papers in hand */}
      {[
        { x: 200, ph: 0.0 },
        { x: 460, ph: 1.1 },
        { x: 720, ph: 0.6 },
        { x: 1180, ph: 1.5 },
        { x: 1440, ph: 0.3 },
        { x: 1700, ph: 2.2 },
      ].map((g, i) => {
        const arm = (Math.sin(lf * 0.4 + g.ph) + 1) * 0.5 + 0.5;
        const head = Math.sin(lf * 0.3 + g.ph) * 12;
        return <EngravedGent key={i} x={g.x} y={870} scale={1.1} faceMood="alarm" headRot={head} armRaise={arm} />;
      })}
      {/* Nathan still at his pillar (smaller, central, contrast to chaos) */}
      <Pillar x={960} y={400} h={540} />
      <EngravedGent x={960} y={830} scale={1.0} faceMood="still" coatHatch={false} />
      {/* Dimming gold light — shafts narrowing */}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#hatch)" opacity={0.18} pointerEvents="none" />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V10_WellingtonLost: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tight on Nathan's name placard etched on his pillar
  const drawP = interpolate(lp, [0.1, 0.7], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      {/* Pillar with placard */}
      <g transform="translate(960,540)">
        {/* Pillar surface (close-up) */}
        <rect x={-300} y={-400} width={600} height={800} fill="url(#hatch)" stroke={C.text} strokeWidth={1.5} />
        <rect x={-300} y={-400} width={600} height={800} fill="none" stroke={C.text} strokeWidth={1.5} />
        {/* Placard frame */}
        <DrawPath d="M -240,-150 L 240,-150 L 240,150 L -240,150 Z" pathLength={1380} progress={drawP} strokeWidth={2.5} stroke={C.gold} />
        <rect x={-220} y={-130} width={440} height={260} fill={C.bg} />
        {/* Etched name */}
        <text x={0} y={-60} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={36} letterSpacing="4" stroke="#000" strokeWidth={2} paintOrder="stroke fill">N. M. ROTHSCHILD</text>
        <text x={0} y={0} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22}>est. 1798</text>
        {/* WELLINGTON LOST? */}
        <text x={0} y={70} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={28} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill" opacity={drawP}>WELLINGTON LOST?</text>
      </g>
      {/* Faint figures in BG raising SELL */}
      <g opacity={0.4}>
        {[100, 1700].map((x, i) => (
          <EngravedGent key={i} x={x} y={870} scale={0.8} faceMood="alarm" armRaise={0.7 + Math.sin(lf * 0.3 + i) * 0.2} />
        ))}
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V11_SellWave: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Wave of SELL cards rises across the floor in staggered rows
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ShaftLight />
      <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
      {/* Many brokers waving SELL */}
      {Array.from({ length: 10 }).map((_, i) => {
        const x = 100 + i * 195;
        const startT = i * 0.06;
        const reveal = interpolate(lp, [startT, startT + 0.25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
        const armRaise = reveal;
        return <EngravedGent key={i} x={x} y={870} scale={1.0} faceMood="alarm" armRaise={armRaise} headRot={Math.sin(lf * 0.2 + i) * 8} />;
      })}
      {/* Floating SELL papers being thrown */}
      {Array.from({ length: 12 }).map((_, i) => {
        const phase = (lf * 0.4 + i * 8) % 80;
        const x = 100 + (i * 150) % 1820;
        const y = 200 + phase * 4 - 200;
        const rot = Math.sin(lf * 0.3 + i) * 25;
        return (
          <g key={i} transform={`translate(${x},${y}) rotate(${rot})`} opacity={0.7}>
            <rect x={-22} y={-15} width={44} height={30} fill={C.bg} stroke={C.text} strokeWidth={1.2} />
            <text x={0} y={6} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={14}>SELL</text>
          </g>
        );
      })}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V12_MarketCollapse: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Engraved line chart begins drawing — flat then drops at end
  const drawP = interpolate(lp, [0, 1], [0, 1], { easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Ornate chart frame */}
      <rect x={240} y={160} width={1440} height={760} fill="none" stroke={C.gold} strokeWidth={2.5} />
      <rect x={260} y={180} width={1400} height={720} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.5} />
      {/* Chart title */}
      <text x={960} y={240} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={36} letterSpacing="4" stroke="#000" strokeWidth={2} paintOrder="stroke fill">CONSOLS · 19 JUNE 1815</text>
      {/* Y-axis labels */}
      {[100, 95, 90, 85, 80].map((v, i) => {
        const y = 320 + i * 130;
        return (
          <g key={i}>
            <line x1={340} y1={y} x2={1620} y2={y} stroke={C.text} strokeWidth={0.6} opacity={0.3} strokeDasharray="3 3" />
            <text x={310} y={y + 6} textAnchor="end" fill={C.text} fontFamily="Georgia, serif" fontSize={20} opacity={0.7}>{v}</text>
          </g>
        );
      })}
      {/* X-axis labels */}
      {[
        { x: 380, label: "open" },
        { x: 700, label: "10am" },
        { x: 1020, label: "noon" },
        { x: 1340, label: "2pm" },
        { x: 1620, label: "close" },
      ].map((t, i) => (
        <text key={i} x={t.x} y={890} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontSize={18} opacity={0.7}>{t.label}</text>
      ))}
      {/* Chart line — flat then drops */}
      <DrawPath
        d="M 380,320 L 480,322 L 580,318 L 700,320 L 820,322 L 940,330 L 1060,360 L 1180,440 L 1300,560 L 1420,680 L 1540,800 L 1620,830"
        pathLength={1500}
        progress={drawP}
        strokeWidth={4}
        stroke={C.gold}
      />
      {/* Crosshatch shading under the falling line */}
      {drawP > 0.6 && (
        <path d="M 940,330 L 1060,360 L 1180,440 L 1300,560 L 1420,680 L 1540,800 L 1620,830 L 1620,860 L 940,860 Z"
          fill="url(#hatch)" opacity={(drawP - 0.6) / 0.4 * 0.4} />
      )}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V13_FallFallFall: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Three discrete drops timed to "fall, fall, fall"
  const stage1 = interpolate(lp, [0.05, 0.30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stage2 = interpolate(lp, [0.30, 0.60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stage3 = interpolate(lp, [0.60, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stage = stage1 + stage2 + stage3;
  // Camera shakes slightly with each drop
  const shake = Math.sin(lf * 1.5) * (lp > 0.85 ? 6 : lp > 0.55 ? 4 : lp > 0.25 ? 2 : 0);
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <g transform={`translate(${shake},${shake * 0.3})`}>
        <rect x={240} y={160} width={1440} height={760} fill="none" stroke={C.gold} strokeWidth={2.5} />
        <text x={960} y={240} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={48} letterSpacing="8" stroke="#000" strokeWidth={2} paintOrder="stroke fill">FALL · FALL · FALL</text>
        {/* Y guides */}
        {[100, 95, 90, 85, 80].map((vv, i) => {
          const y = 320 + i * 130;
          return <line key={i} x1={340} y1={y} x2={1620} y2={y} stroke={C.text} strokeWidth={0.5} opacity={0.25} />;
        })}
        {/* Big arrow segments — three discrete drops */}
        <line x1={340} y1={400} x2={760} y2={500} stroke={C.gold} strokeWidth={6} opacity={stage1} strokeLinecap="round" />
        <line x1={760} y1={500} x2={1180} y2={650} stroke={C.gold} strokeWidth={6} opacity={stage2} strokeLinecap="round" />
        <line x1={1180} y1={650} x2={1620} y2={830} stroke={C.gold} strokeWidth={6} opacity={stage3} strokeLinecap="round" />
        {/* Drop arrows at break points */}
        {stage1 > 0.5 && <polygon points="760,490 750,470 770,470" fill={C.red} opacity={stage1} />}
        {stage2 > 0.5 && <polygon points="1180,640 1170,620 1190,620" fill={C.red} opacity={stage2} />}
        {stage3 > 0.5 && <polygon points="1620,820 1610,800 1630,800" fill={C.red} opacity={stage3} />}
        {/* Caption */}
        <text x={960} y={1010} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={26} opacity={0.85} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">−4 points · −9 points · −18 points</text>
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V14_AgentsEmerge: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Pull back wide; floor of slumped brokers; agents emerge from corners
  const camZoom = interpolate(lp, [0, 1], [1.15, 1.0], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <g transform={`translate(${960 - 960 * camZoom},${540 - 540 * camZoom}) scale(${camZoom})`}>
        <line x1={0} y1={940} x2={1920} y2={940} stroke={C.text} strokeWidth={1.5} />
        <Pillar x={300} y={460} h={480} />
        <Pillar x={1620} y={460} h={480} />
        {/* Slumped brokers (heads down, arms hanging) */}
        {[200, 480, 720, 1180, 1440, 1700].map((x, i) => (
          <EngravedGent key={i} x={x} y={910} scale={0.95} headRot={30 + Math.sin(lf * 0.05 + i) * 4} armRaise={0} />
        ))}
        {/* Strewn papers on floor */}
        {Array.from({ length: 16 }).map((_, i) => {
          const px = 100 + (i * 113) % 1720;
          const py = 950 + ((i * 17) % 30);
          const rot = (i * 27) % 60 - 30;
          return (
            <g key={i} transform={`translate(${px},${py}) rotate(${rot})`}>
              <rect x={-12} y={-8} width={24} height={16} fill={C.bg} stroke={C.text} strokeWidth={1} opacity={0.7} />
            </g>
          );
        })}
        {/* Agents emerging from corners — distinct (no top hats, plainer coats) */}
        {[
          { x: -50 + lp * 280, y: 870 },
          { x: 1970 - lp * 300, y: 870 },
          { x: 220 + lp * 60, y: 870 },
          { x: 1700 - lp * 80, y: 870 },
        ].map((a, i) => (
          <g key={i} transform={`translate(${a.x},${a.y}) scale(0.95)`}>
            {/* Plain coat (no hatch fill — they should look different from brokers) */}
            <path d="M -38,40 L -26,-30 L 26,-30 L 38,40 L 34,140 L -34,140 Z" fill="none" stroke={C.gold} strokeWidth={1.5} />
            <circle cx={0} cy={-50} r={16} fill="none" stroke={C.gold} strokeWidth={1.5} />
            {/* Cap (not top hat) */}
            <ellipse cx={0} cy={-66} rx={20} ry={6} fill="none" stroke={C.gold} strokeWidth={1.5} />
            <path d="M -16,-66 Q 0,-78 16,-66" fill="none" stroke={C.gold} strokeWidth={1.5} />
          </g>
        ))}
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V15_AgentTrack: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Track one agent across the floor
  const ax = interpolate(lp, [0, 1], [200, 1700], { easing: ease });
  // Camera follows
  const camX = interpolate(lp, [0, 1], [-200, -100], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <g transform={`translate(${camX},0)`}>
        <line x1={-300} y1={940} x2={2200} y2={940} stroke={C.text} strokeWidth={1.5} />
        {/* Slumped brokers strewn behind */}
        {[100, 380, 660, 1240, 1520, 1800].map((x, i) => (
          <EngravedGent key={i} x={x + 200} y={910} scale={0.95} headRot={30 + Math.sin(lf * 0.05 + i) * 4} armRaise={0} />
        ))}
        {/* The agent (highlighted, focal) */}
        <g transform={`translate(${ax + 200},870)`}>
          <path d="M -40,40 L -28,-32 L 28,-32 L 40,40 L 36,140 L -36,140 Z" fill="url(#hatch)" stroke={C.gold} strokeWidth={2} />
          <circle cx={0} cy={-52} r={17} fill="none" stroke={C.gold} strokeWidth={2} />
          {/* Cap */}
          <ellipse cx={0} cy={-68} rx={22} ry={6} fill="none" stroke={C.gold} strokeWidth={2} />
          <path d="M -18,-68 Q 0,-82 18,-68" fill="none" stroke={C.gold} strokeWidth={2} />
          {/* BUY card peeking from coat */}
          <rect x={20} y={20} width={50} height={28} fill={C.bg} stroke={C.gold} strokeWidth={1.5} />
          <text x={45} y={40} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={18}>BUY</text>
        </g>
        {/* Pillars */}
        <Pillar x={300} y={460} h={480} />
        <Pillar x={1620} y={460} h={480} />
        <Pillar x={2940} y={460} h={480} />
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V16_LedgerTally: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Multi-agent montage; ledger tally marks accumulate
  const tallyCount = Math.floor(interpolate(lp, [0, 1], [0, 80], { easing: ease }));
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Ledger book taking center stage */}
      <g transform="translate(960,540)">
        <rect x={-560} y={-300} width={1120} height={600} fill={C.paper} stroke={C.text} strokeWidth={2} />
        {/* Spine */}
        <line x1={0} y1={-300} x2={0} y2={300} stroke={C.text} strokeWidth={3} />
        {/* Header */}
        <text x={-280} y={-240} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={24} letterSpacing="3" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">PURCHASE LEDGER</text>
        <text x={280} y={-240} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={24} letterSpacing="3" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">19 JUNE 1815</text>
        <line x1={-540} y1={-220} x2={540} y2={-220} stroke={C.text} strokeWidth={1.5} />
        {/* Tally marks accumulate */}
        {Array.from({ length: tallyCount }).map((_, i) => {
          const col = i % 8;
          const row = Math.floor(i / 8);
          const x = -480 + col * 130 + (row % 2 === 1 ? 65 : 0);
          const y = -180 + row * 50;
          return (
            <g key={i} transform={`translate(${x},${y})`}>
              <line x1={0} y1={-12} x2={0} y2={12} stroke={C.text} strokeWidth={2} />
              {i % 5 === 4 && <line x1={-10} y1={-8} x2={10} y2={8} stroke={C.text} strokeWidth={2} />}
            </g>
          );
        })}
      </g>
      {/* Hands writing in corners */}
      {Array.from({ length: 3 }).map((_, i) => {
        const x = [200, 960, 1720][i];
        const y = 180 + Math.sin(lf * 0.2 + i) * 4;
        return (
          <g key={i} transform={`translate(${x},${y})`}>
            <ellipse cx={0} cy={0} rx={50} ry={20} fill="none" stroke={C.gold} strokeWidth={1.5} />
            <line x1={20} y1={0} x2={50 + Math.sin(lf * 0.3 + i) * 5} y2={-30} stroke={C.gold} strokeWidth={2} />
            <text x={0} y={50} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={16} opacity={0.7}>agent · {(i + 1).toString().padStart(2, "0")}</text>
          </g>
        );
      })}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V17_DisasterStreet: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Cross-cut to street outside; Londoners reading newspaper "DISASTER?"
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Street facade — buildings */}
      <line x1={0} y1={780} x2={1920} y2={780} stroke={C.text} strokeWidth={1.5} />
      {/* Building outlines */}
      {[100, 380, 660, 1260, 1540].map((x, i) => (
        <g key={i}>
          <rect x={x} y={300} width={220} height={480} fill="url(#hatch)" stroke={C.text} strokeWidth={1.5} opacity={0.65} />
          {[0, 1, 2].map((row) =>
            [0, 1, 2].map((col) => (
              <rect key={`${row}${col}`} x={x + 30 + col * 60} y={350 + row * 130} width={36} height={50} fill={C.bg} stroke={C.text} strokeWidth={1} />
            ))
          )}
        </g>
      ))}
      {/* Foreground figures reading newspapers */}
      {[420, 880, 1340].map((x, i) => (
        <g key={i} transform={`translate(${x},900)`}>
          <EngravedGent x={0} y={-30} scale={1.1} headRot={20} armRaise={0.4} />
          {/* Newspaper */}
          <rect x={-40} y={-50} width={80} height={70} fill={C.paper} stroke={C.text} strokeWidth={1.5} />
          <text x={0} y={-30} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={14} letterSpacing="1">DISASTER?</text>
          <line x1={-30} y1={-15} x2={30} y2={-15} stroke={C.text} strokeWidth={0.7} />
          <line x1={-30} y1={-5} x2={30} y2={-5} stroke={C.text} strokeWidth={0.7} />
          <line x1={-30} y1={5} x2={30} y2={5} stroke={C.text} strokeWidth={0.7} />
          <line x1={-30} y1={15} x2={30} y2={15} stroke={C.text} strokeWidth={0.7} />
        </g>
      ))}
      {/* Rain streaks */}
      {Array.from({ length: 80 }).map((_, i) => {
        const seed = i * 91.7;
        const x = (seed * 17) % 1920;
        const y = ((lf * 18 + seed * 23) % 1080);
        return <line key={i} x1={x} y1={y} x2={x - 5} y2={y + 26} stroke={C.text} strokeWidth={1.2} opacity={0.18} />;
      })}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

const V18_WhitehallEnd: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  const stageA = interpolate(lp, [0, 0.30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stageAFade = interpolate(lp, [0.28, 0.40], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stageB = interpolate(lp, [0.32, 0.62], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stageBFade = interpolate(lp, [0.60, 0.72], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stageC = interpolate(lp, [0.65, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <EngravingDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Stage A: Whitehall facade — large, fills frame */}
      <g opacity={stageAFade}>
        {/* Wide pediment */}
        <polygon points="160,260 1760,260 1620,120 300,120" fill="url(#hatch)" stroke={C.text} strokeWidth={2} />
        {/* Body */}
        <rect x={160} y={260} width={1600} height={680} fill="url(#hatch)" stroke={C.text} strokeWidth={2} />
        {/* Columns — 12 across the front */}
        {Array.from({ length: 12 }).map((_, i) => (
          <g key={i}>
            <rect x={210 + i * 130} y={290} width={42} height={620} fill="url(#hatchDense)" stroke={C.text} strokeWidth={1.2} />
            <rect x={205 + i * 130} y={282} width={52} height={12} fill="none" stroke={C.text} strokeWidth={1.2} />
            <rect x={205 + i * 130} y={902} width={52} height={12} fill="none" stroke={C.text} strokeWidth={1.2} />
          </g>
        ))}
        {/* Steps */}
        <polygon points="160,940 1760,940 1700,990 220,990" fill="none" stroke={C.text} strokeWidth={1.5} />
        <line x1={200} y1={1010} x2={1720} y2={1010} stroke={C.text} strokeWidth={1.2} opacity={0.6} />
        {/* Crown insignia in pediment */}
        <g transform="translate(960,200) scale(1.5)">
          <polygon points="-22,8 -14,-18 -6,-2 0,-22 6,-2 14,-18 22,8" fill="none" stroke={C.gold} strokeWidth={2} />
          <rect x={-22} y={8} width={44} height={6} fill="none" stroke={C.gold} strokeWidth={2} />
        </g>
        {/* Label */}
        <text x={960} y={210} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={28} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill" opacity={0.85}>WHITEHALL</text>
        {/* Late messenger riding in (BIGGER) */}
        <g transform={`translate(${interpolate(stageA, [0, 1], [2100, 1480])},${1000})`}>
          {/* Horse body */}
          <ellipse cx={0} cy={0} rx={70} ry={22} fill="none" stroke={C.text} strokeWidth={1.8} />
          {/* Horse legs */}
          <line x1={-44} y1={20} x2={-44} y2={70} stroke={C.text} strokeWidth={2} />
          <line x1={-18} y1={20} x2={-18} y2={70} stroke={C.text} strokeWidth={2} />
          <line x1={22} y1={20} x2={22} y2={70} stroke={C.text} strokeWidth={2} />
          <line x1={48} y1={20} x2={48} y2={70} stroke={C.text} strokeWidth={2} />
          {/* Horse head */}
          <path d="M 50,-4 Q 84,-36 92,-46 L 78,-50 Q 64,-30 44,-12 Z" fill="none" stroke={C.text} strokeWidth={1.8} />
          {/* Rider */}
          <circle cx={10} cy={-50} r={14} fill="none" stroke={C.text} strokeWidth={2} />
          <path d="M 0,-36 L 22,-12 L 22,-30 Z" fill="none" stroke={C.text} strokeWidth={1.8} />
          {/* Dispatch in raised hand */}
          <rect x={28} y={-92} width={26} height={20} fill={C.bg} stroke={C.text} strokeWidth={1.5} />
        </g>
        <text x={960} y={1060} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill" opacity={stageA}>the Crown's messenger · arrives the next morning</text>
      </g>
      {/* Stage B: Nathan walks out of Exchange holding closed ledger — much LARGER */}
      <g opacity={stageB * stageBFade}>
        {/* Exchange portal — fills upper frame */}
        <polygon points="380,200 1540,200 1420,80 500,80" fill="none" stroke={C.text} strokeWidth={2} />
        <rect x={460} y={200} width={1000} height={760} fill="url(#hatchDense)" stroke={C.text} strokeWidth={2} opacity={0.4} />
        {/* Greek revival columns flanking */}
        {[0, 1, 2, 3, 4, 5].map(i => (
          <g key={i}>
            <rect x={490 + i * 165} y={220} width={36} height={740} fill="url(#hatchDense)" stroke={C.text} strokeWidth={1.2} />
          </g>
        ))}
        {/* Doorway */}
        <rect x={840} y={400} width={240} height={460} fill={C.bg} stroke={C.text} strokeWidth={2} />
        {/* Nathan walks out — BIG, foreground */}
        <g transform={`translate(${interpolate(stageB, [0, 1], [960, 1140])},${800})`}>
          <EngravedGent x={0} y={0} scale={4.0} faceMood="still" coatHatch={false} />
          {/* Closed ledger in hand */}
          <g transform="translate(110, 120)">
            <rect x={-50} y={-40} width={100} height={80} fill={C.paper} stroke={C.text} strokeWidth={2} />
            <line x1={-50} y1={-22} x2={50} y2={-22} stroke={C.text} strokeWidth={1.2} />
            <line x1={-50} y1={-4} x2={50} y2={-4} stroke={C.text} strokeWidth={1.2} />
            <line x1={-50} y1={14} x2={50} y2={14} stroke={C.text} strokeWidth={1.2} />
            {/* Wax seal */}
            <circle cx={20} cy={20} r={10} fill={C.red} stroke="#7a1414" strokeWidth={1.5} />
          </g>
        </g>
        <text x={960} y={1050} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} stroke="#000" strokeWidth={2} paintOrder="stroke fill">Rothschild's positions are closed · the trade is done</text>
      </g>
      {/* Stage C: Final etched title card — MUCH bigger */}
      <g opacity={stageC}>
        <rect x={120} y={140} width={1680} height={800} fill={C.bg} stroke={C.gold} strokeWidth={4} />
        <rect x={150} y={170} width={1620} height={740} fill="none" stroke={C.gold} strokeWidth={1.5} opacity={0.55} />
        {/* Decorative corner ornaments */}
        {[[150, 170], [1770, 170], [150, 910], [1770, 910]].map(([cx, cy], i) => (
          <g key={i} transform={`translate(${cx},${cy})`}>
            <circle cx={0} cy={0} r={22} fill="none" stroke={C.gold} strokeWidth={2} />
            <circle cx={0} cy={0} r={14} fill="none" stroke={C.gold} strokeWidth={1.2} />
            <circle cx={0} cy={0} r={5} fill={C.gold} />
          </g>
        ))}
        {/* 1815 — huge centerpiece */}
        <text x={960} y={520} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={320} letterSpacing="30" stroke="#000" strokeWidth={4} paintOrder="stroke fill">1815</text>
        <line x1={300} y1={580} x2={1620} y2={580} stroke={C.gold} strokeWidth={2} opacity={0.6} />
        <text x={960} y={680} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={48} letterSpacing="2" stroke="#000" strokeWidth={2} paintOrder="stroke fill">the silence between two pieces of information</text>
        <text x={960} y={760} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontSize={28} opacity={0.7} letterSpacing="6" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">the modern financial world begins here</text>
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteGrad)" />
      <GrainOverlay frame={frame} />
    </svg>
  );
};

// ── Main ─────────────────────────────────────────────────────────────────────

export const LetterDynastyColdOpen: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <Audio src={staticFile("letter-dynasty-cold-open.mp3")} />
      {VIGNETTES.map((v, i) => {
        const op = vOpacity(frame, v);
        if (op <= 0.001) return null;
        let content: React.ReactNode = null;
        switch (v.name) {
          case "wide-floor":      content = <V01_WideFloor frame={frame} v={v} />; break;
          case "nathan-pillar":   content = <V02_NathanPillar frame={frame} v={v} />; break;
          case "broker-watch-1":  content = <V03_BrokerWatch1 frame={frame} v={v} />; break;
          case "broker-watch-2":  content = <V04_BrokerWatch2 frame={frame} v={v} />; break;
          case "nathan-eyes":     content = <V05_NathanEyes frame={frame} v={v} />; break;
          case "sell-card":       content = <V06_SellCard frame={frame} v={v} />; break;
          case "bond-cert":       content = <V07_BondCert frame={frame} v={v} />; break;
          case "rally-channel":   content = <V08_RallyChannel frame={frame} v={v} />; break;
          case "panic":           content = <V09_Panic frame={frame} v={v} />; break;
          case "wellington-lost": content = <V10_WellingtonLost frame={frame} v={v} />; break;
          case "sell-wave":       content = <V11_SellWave frame={frame} v={v} />; break;
          case "market-collapse": content = <V12_MarketCollapse frame={frame} v={v} />; break;
          case "fall-fall-fall":  content = <V13_FallFallFall frame={frame} v={v} />; break;
          case "agents-emerge":   content = <V14_AgentsEmerge frame={frame} v={v} />; break;
          case "agent-track":     content = <V15_AgentTrack frame={frame} v={v} />; break;
          case "ledger-tally":    content = <V16_LedgerTally frame={frame} v={v} />; break;
          case "disaster-street": content = <V17_DisasterStreet frame={frame} v={v} />; break;
          case "whitehall-end":   content = <V18_WhitehallEnd frame={frame} v={v} />; break;
        }
        return <AbsoluteFill key={i} style={{ opacity: op }}>{content}</AbsoluteFill>;
      })}
    </AbsoluteFill>
  );
};
