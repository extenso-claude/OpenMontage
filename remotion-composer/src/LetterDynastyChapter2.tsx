/**
 * Letter That Built A Dynasty — CHAPTER 2: The Couriers.
 * Style: silhouette-against-glow (most cinematic).
 * 79s, 18 vignettes, 24fps, 1920×1080.
 *
 * Diagonal sweeps + tracking gallop into vanishing-point glow.
 * Pure black silhouettes against radial gradients (dawn, ember, moonlit).
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
  silhouette: "#000000",
};

const FPS = 24;
const DURATION_S = 79;
export const LETTER_CHAPTER2_DURATION_FRAMES = Math.ceil(DURATION_S * FPS);

const ease = Easing.inOut(Easing.cubic);
const easeOut = Easing.out(Easing.cubic);

type V = { name: string; start: number; end: number };
const VIGNETTES: V[] = [
  { name: "crown-coach",      start: 0,  end: 5  },
  { name: "four-days",        start: 5,  end: 9  },
  { name: "good-week",        start: 9,  end: 13 },
  { name: "weather-channel",  start: 13, end: 17 },
  { name: "rothschild-rider", start: 17, end: 22 },
  { name: "weather-cycle",    start: 22, end: 26 },
  { name: "private-network",  start: 26, end: 31 },
  { name: "packet-boats",     start: 31, end: 36 },
  { name: "clerks-shifts",    start: 36, end: 41 },
  { name: "thread-paris",     start: 41, end: 46 },
  { name: "thread-london",    start: 46, end: 50 },
  { name: "rothschild-trio",  start: 50, end: 55 },
  { name: "deny-customs",     start: 55, end: 59 },
  { name: "deny-banker",      start: 59, end: 63 },
  { name: "deny-spy",         start: 63, end: 67 },
  { name: "roworth-waterloo", start: 67, end: 71 },
  { name: "roworth-decision", start: 71, end: 75 },
  { name: "roworth-rides",    start: 75, end: 79 },
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

// ── Glow defs ────────────────────────────────────────────────────────────────

const GlowDefs: React.FC = () => (
  <defs>
    {/* Dawn glow — warm gold/orange */}
    <radialGradient id="glow-dawn" cx="50%" cy="80%" r="70%">
      <stop offset="0%" stopColor="#ffaa50" stopOpacity={0.95} />
      <stop offset="35%" stopColor={C.gold} stopOpacity={0.6} />
      <stop offset="70%" stopColor="#3a2616" stopOpacity={0.3} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
    </radialGradient>
    {/* Dusk/ember glow — orange/red */}
    <radialGradient id="glow-ember" cx="50%" cy="80%" r="70%">
      <stop offset="0%" stopColor="#ff7028" stopOpacity={0.9} />
      <stop offset="35%" stopColor="#c84818" stopOpacity={0.5} />
      <stop offset="70%" stopColor="#3a1808" stopOpacity={0.3} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
    </radialGradient>
    {/* Moonlit glow — cool blue */}
    <radialGradient id="glow-moon" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stopColor="#a8c8e8" stopOpacity={0.85} />
      <stop offset="40%" stopColor="#3a4a78" stopOpacity={0.4} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
    </radialGradient>
    {/* Battlefield haze — desaturated red-brown smoke */}
    <radialGradient id="glow-battle" cx="50%" cy="60%" r="70%">
      <stop offset="0%" stopColor="#c87038" stopOpacity={0.85} />
      <stop offset="40%" stopColor="#6a3010" stopOpacity={0.5} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
    </radialGradient>
    {/* Candle warm */}
    <radialGradient id="glow-candle" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stopColor="#ffc070" stopOpacity={0.9} />
      <stop offset="50%" stopColor="#a06028" stopOpacity={0.4} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
    </radialGradient>
    {/* Vignette */}
    <radialGradient id="vignetteCh2" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stopColor={C.bg} stopOpacity={0} />
      <stop offset="80%" stopColor={C.bg} stopOpacity={0.4} />
      <stop offset="100%" stopColor={C.bg} stopOpacity={0.95} />
    </radialGradient>
  </defs>
);

// ── Reusable silhouette primitives ───────────────────────────────────────────

const HorseRiderSilhouette: React.FC<{ x: number; y: number; scale?: number; phase?: number; flipX?: boolean }> = ({
  x, y, scale = 1, phase = 0, flipX = false,
}) => {
  const bob = Math.sin(phase) * 5;
  return (
    <g transform={`translate(${x},${y + bob}) scale(${flipX ? -scale : scale}, ${scale})`}>
      {/* Horse body */}
      <ellipse cx={0} cy={0} rx={50} ry={18} fill={C.silhouette} />
      {/* Neck + head */}
      <path d="M 35,-2 Q 60,-26 68,-36 L 56,-36 Q 44,-22 30,-10 Z" fill={C.silhouette} />
      {/* Mane */}
      <path d="M 30,-10 Q 18,-22 16,-26 Q 28,-18 38,-14 Z" fill={C.silhouette} />
      {/* Legs animated by phase */}
      <rect x={-32} y={16} width={6} height={28 + Math.sin(phase * 1.6) * 5} fill={C.silhouette} />
      <rect x={-16} y={16} width={6} height={28 - Math.sin(phase * 1.6) * 5} fill={C.silhouette} />
      <rect x={16} y={16} width={6} height={28 - Math.sin(phase * 1.6) * 5} fill={C.silhouette} />
      <rect x={32} y={16} width={6} height={28 + Math.sin(phase * 1.6) * 5} fill={C.silhouette} />
      {/* Tail */}
      <path d={`M -50,-2 Q -64,${4 + Math.sin(phase) * 4} -60,20`} stroke={C.silhouette} strokeWidth={5} fill="none" strokeLinecap="round" />
      {/* Rider */}
      <circle cx={6} cy={-32} r={11} fill={C.silhouette} />
      <path d="M -4,-22 Q 6,-2 16,-14 L 16,-26 Q 12,-36 0,-30 Z" fill={C.silhouette} />
      {/* Tricorn hat hint */}
      <path d="M -4,-40 L 16,-40 L 6,-46 Z" fill={C.silhouette} />
    </g>
  );
};

const CoachSilhouette: React.FC<{ x: number; y: number; scale?: number; phase?: number }> = ({ x, y, scale = 1, phase = 0 }) => (
  <g transform={`translate(${x},${y}) scale(${scale})`}>
    {/* Carriage body */}
    <rect x={-60} y={-30} width={120} height={50} fill={C.silhouette} />
    <rect x={-50} y={-40} width={100} height={12} fill={C.silhouette} />
    {/* Windows (cut-out — slightly lighter) */}
    <rect x={-40} y={-22} width={20} height={20} fill={C.bg} opacity={0.7} />
    <rect x={20} y={-22} width={20} height={20} fill={C.bg} opacity={0.7} />
    {/* Driver */}
    <circle cx={-50} cy={-44} r={6} fill={C.silhouette} />
    {/* Wheels animated */}
    <g transform={`translate(-40,30) rotate(${phase * 20})`}>
      <circle cx={0} cy={0} r={20} fill={C.silhouette} />
      <line x1={-20} y1={0} x2={20} y2={0} stroke={C.bg} strokeWidth={1.2} opacity={0.4} />
      <line x1={0} y1={-20} x2={0} y2={20} stroke={C.bg} strokeWidth={1.2} opacity={0.4} />
    </g>
    <g transform={`translate(40,30) rotate(${phase * 20})`}>
      <circle cx={0} cy={0} r={20} fill={C.silhouette} />
      <line x1={-20} y1={0} x2={20} y2={0} stroke={C.bg} strokeWidth={1.2} opacity={0.4} />
      <line x1={0} y1={-20} x2={0} y2={20} stroke={C.bg} strokeWidth={1.2} opacity={0.4} />
    </g>
    {/* Two horses */}
    <ellipse cx={-110} cy={10} rx={30} ry={12} fill={C.silhouette} />
    <ellipse cx={-150} cy={10} rx={30} ry={12} fill={C.silhouette} />
    <rect x={-130} y={20} width={4} height={18 + Math.sin(phase * 1.6) * 3} fill={C.silhouette} />
    <rect x={-118} y={20} width={4} height={18 - Math.sin(phase * 1.6) * 3} fill={C.silhouette} />
    <rect x={-160} y={20} width={4} height={18 + Math.sin(phase * 1.6) * 3} fill={C.silhouette} />
    <rect x={-148} y={20} width={4} height={18 - Math.sin(phase * 1.6) * 3} fill={C.silhouette} />
  </g>
);

const RainStreaks: React.FC<{ frame: number; count?: number; angle?: number }> = ({ frame, count = 80, angle = 18 }) => {
  const rad = (angle * Math.PI) / 180;
  return (
    <g>
      {Array.from({ length: count }).map((_, i) => {
        const seed = i * 91.7;
        const x = (seed * 17) % 1920;
        const y = ((frame * 18 + seed * 23) % 1080);
        const dx = -Math.sin(rad) * 22;
        const dy = Math.cos(rad) * 22;
        return <line key={i} x1={x} y1={y} x2={x + dx} y2={y + dy} stroke={C.text} strokeWidth={1.2} opacity={0.22} />;
      })}
    </g>
  );
};

const SnowFlakes: React.FC<{ frame: number; count?: number }> = ({ frame, count = 70 }) => (
  <g>
    {Array.from({ length: count }).map((_, i) => {
      const seed = i * 131;
      const x = ((seed * 13 + frame * 0.6) % 1920);
      const y = ((seed * 19 + frame * 2.4) % 1080);
      return <circle key={i} cx={x + Math.sin((frame + i) * 0.05) * 6} cy={y} r={2 + (i % 3) * 0.8} fill={C.text} opacity={0.5} />;
    })}
  </g>
);

const LightningFlash: React.FC<{ active: boolean; frame: number }> = ({ active, frame }) => {
  if (!active) return null;
  const flicker = Math.sin(frame * 0.6) > 0 ? 1 : 0;
  return (
    <g opacity={flicker}>
      <rect x={0} y={0} width={1920} height={1080} fill="#a8c8e8" opacity={0.18} />
      <path d="M 1500,80 L 1450,300 L 1490,310 L 1430,540 L 1480,560 L 1400,800" stroke="#e8f0ff" strokeWidth={4} fill="none" />
    </g>
  );
};

const SmokeWisps: React.FC<{ frame: number; count?: number; spread?: [number, number, number, number] }> = ({
  frame, count = 18, spread = [200, 600, 1720, 1000],
}) => (
  <g>
    {/* Diffuse smoke layer — big soft ellipses, low opacity, layered */}
    {Array.from({ length: count }).map((_, i) => {
      const seed = i * 103;
      const baseX = spread[0] + (seed * 7) % (spread[2] - spread[0]);
      const baseY = spread[1] + ((seed * 13 - frame * 0.4) % (spread[3] - spread[1]));
      const wob = Math.sin((frame + i) * 0.04) * 12;
      const r = 80 + (i % 4) * 30;
      return (
        <ellipse key={i}
          cx={baseX + wob} cy={baseY}
          rx={r * 1.6} ry={r * 0.7}
          fill="#1a0a04"
          opacity={0.10 + ((i % 3) * 0.04)}
        />
      );
    })}
    {/* Lighter outer haze layer for softness */}
    {Array.from({ length: Math.floor(count * 0.6) }).map((_, i) => {
      const seed = i * 167;
      const baseX = spread[0] + (seed * 11) % (spread[2] - spread[0]);
      const baseY = spread[1] + ((seed * 17 - frame * 0.3) % (spread[3] - spread[1]));
      const wob = Math.sin((frame + i) * 0.03) * 16;
      return (
        <ellipse key={`o-${i}`}
          cx={baseX + wob} cy={baseY}
          rx={180 + (i % 4) * 40}
          ry={70 + (i % 3) * 16}
          fill="#3a1e10"
          opacity={0.06}
        />
      );
    })}
  </g>
);

// ── Vignette renderers ───────────────────────────────────────────────────────

const V01_CrownCoach: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Dawn glow with foggy ridge
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1300} ry={500} fill="url(#glow-dawn)" />
      {/* Distant ridge silhouette */}
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,820 L 0,820 Z" fill={C.silhouette} />
      {/* Foreground hill with road */}
      <path d="M 0,820 L 1920,820 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      {/* Coach silhouette traversing the ridge */}
      <CoachSilhouette x={interpolate(lp, [0, 1], [400, 1200])} y={780} scale={0.9} phase={lf * 0.4} />
      {/* Caption */}
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="3" stroke="#000" strokeWidth={2} paintOrder="stroke fill">the official postal service of the Crown</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V02_FourDays: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Counter "4 DAYS" etches in
  const counterP = interpolate(lp, [0, 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1300} ry={500} fill="url(#glow-dawn)" />
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      {/* Coach moving slowly */}
      <CoachSilhouette x={interpolate(lp, [0, 1], [200, 700])} y={780} scale={1.0} phase={lf * 0.3} />
      {/* Big counter */}
      <g transform="translate(1480,440)" opacity={counterP}>
        <rect x={-260} y={-110} width={520} height={220} fill={C.bg} stroke={C.gold} strokeWidth={4} />
        <rect x={-244} y={-94} width={488} height={188} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.5} />
        <text x={0} y={28} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={140} letterSpacing="14" stroke="#000" strokeWidth={3} paintOrder="stroke fill">4 DAYS</text>
        <text x={0} y={78} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={26} letterSpacing="6">brussels → london</text>
      </g>
      {/* Caption */}
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">to move a single letter</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V03_GoodWeek: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Sun arcs across, day counter ticks
  const sunT = lp;
  const sunX = interpolate(sunT, [0, 1], [200, 1720]);
  const sunY = 320 - Math.sin(sunT * Math.PI) * 180;
  // Day counter
  const dayCount = Math.min(4, Math.floor(lp * 5) + 1);
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1300} ry={500} fill="url(#glow-dawn)" />
      {/* Sun arc trail */}
      {Array.from({ length: 16 }).map((_, i) => {
        const t = i / 15;
        if (t > sunT) return null;
        const x = interpolate(t, [0, 1], [200, 1720]);
        const y = 320 - Math.sin(t * Math.PI) * 180;
        return <circle key={i} cx={x} cy={y} r={6} fill={C.gold} opacity={0.18 + t * 0.18} />;
      })}
      {/* Sun */}
      <circle cx={sunX} cy={sunY} r={50} fill="#ffd080" opacity={0.5} />
      <circle cx={sunX} cy={sunY} r={32} fill="#ffd080" />
      {/* Ridge */}
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      <CoachSilhouette x={interpolate(lp, [0, 1], [-100, 1900])} y={780} scale={0.8} phase={lf * 0.25} />
      {/* Day counter */}
      <g transform="translate(1620,840)">
        <rect x={-140} y={-50} width={280} height={100} fill={C.bg} stroke={C.gold} strokeWidth={3} />
        <text x={0} y={20} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={56} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">DAY {dayCount}</text>
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">on a good week</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V04_WeatherChannel: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Stormy weather — coach struggles
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Storm sky — desaturated dim glow */}
      <ellipse cx={960} cy={780} rx={1300} ry={500} fill="url(#glow-moon)" opacity={0.6} />
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      <CoachSilhouette x={interpolate(lp, [0, 1], [400, 800])} y={780} scale={1.0} phase={lf * 0.25} />
      <RainStreaks frame={lf} count={120} angle={22} />
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.85} stroke="#000" strokeWidth={2} paintOrder="stroke fill">longer when the weather turns</text>
      <text x={120} y={170} fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22} letterSpacing="2" opacity={0.7}>or the Channel runs rough</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V05_RothschildRider: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Fast Rothschild rider; "32 HRS" snaps in
  const counterP = interpolate(lp, [0.15, 0.45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const counterScale = interpolate(counterP, [0, 0.6, 1], [0.4, 1.2, 1.0], { easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1400} ry={520} fill="url(#glow-ember)" />
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      {/* Rothschild rider — galloping fast (BIGGER, mid-frame) */}
      <HorseRiderSilhouette x={interpolate(lp, [0, 1], [-200, 2120])} y={780} scale={2.4} phase={lf * 0.9} />
      {/* Dust kicked up behind */}
      {Array.from({ length: 10 }).map((_, i) => {
        const trail = (lf * 1.5 - i * 4) % 50;
        const tx = interpolate(lp, [0, 1], [-200, 2120]) - 80 - trail * 3;
        const ty = 790 + Math.sin((lf + i) * 0.3) * 4;
        const op = Math.max(0, 0.5 - trail / 50);
        return <circle key={i} cx={tx} cy={ty} r={4 + (i % 3)} fill="#3a2410" opacity={op} />;
      })}
      {/* Counter "32 HRS" */}
      <g transform={`translate(1500,400) scale(${counterScale})`} opacity={counterP}>
        <rect x={-260} y={-110} width={520} height={220} fill={C.bg} stroke={C.gold} strokeWidth={4} />
        <text x={0} y={28} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={140} letterSpacing="10" stroke="#000" strokeWidth={3} paintOrder="stroke fill">32 HRS</text>
        <text x={0} y={78} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={24} letterSpacing="6">the rothschild network</text>
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="3" stroke="#000" strokeWidth={2} paintOrder="stroke fill">the Rothschilds move it in thirty-two hours</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V06_WeatherCycle: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Three weather backdrops cycle (lightning / snow / rain) — rider keeps going
  const phaseT = lp * 3; // 0-1 lightning, 1-2 snow, 2-3 rain
  const showLightning = phaseT < 1;
  const showSnow = phaseT >= 1 && phaseT < 2;
  const showRain = phaseT >= 2;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1300} ry={500} fill="url(#glow-moon)" opacity={0.5} />
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
      {/* Rider — keeps moving forward (LARGER, more central) */}
      <HorseRiderSilhouette x={interpolate(lp, [0, 1], [200, 1720])} y={800} scale={2.2} phase={lf * 1.0} />
      {showLightning && <LightningFlash active frame={lf} />}
      {showSnow && <SnowFlakes frame={lf} count={120} />}
      {showRain && <RainStreaks frame={lf} count={120} angle={20} />}
      {/* Weather label */}
      <g transform="translate(960,200)">
        <rect x={-160} y={-40} width={320} height={70} fill={C.bg} stroke={C.gold} strokeWidth={2} opacity={0.85} />
        <text x={0} y={10} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={32} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">
          {showLightning ? "STORM" : showSnow ? "SNOW" : "RAIN"}
        </text>
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">in any weather · in any season</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V07_PrivateNetwork: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Diagonal sweep — first rider hands satchel to second
  const camX = interpolate(lp, [0, 1], [0, -300], { easing: ease });
  const camY = interpolate(lp, [0, 1], [0, -50], { easing: ease });
  // Rider 1 at handoff
  const rider1X = interpolate(lp, [0, 1], [400, 760]);
  // Rider 2 receiving + leaving
  const rider2X = interpolate(lp, [0, 1], [760, 1400]);
  const handoffP = interpolate(lp, [0.3, 0.55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={780} rx={1400} ry={520} fill="url(#glow-dawn)" />
      <g transform={`translate(${camX},${camY})`}>
        {/* Ridge */}
        <path d="M -300,720 L 200,680 L 600,710 L 1000,690 L 1400,720 L 1800,705 L 2200,725 L 2200,1080 L -300,1080 Z" fill={C.silhouette} />
        {/* Relay station — small post structure */}
        <g transform="translate(760,720)">
          <rect x={-50} y={-100} width={100} height={100} fill={C.silhouette} />
          <polygon points="-60,-100 60,-100 0,-140" fill={C.silhouette} />
          {/* Lit lantern */}
          <circle cx={0} cy={-40} r={14} fill="#ffc070" opacity={0.85} />
          <circle cx={0} cy={-40} r={32} fill="#ffc070" opacity={0.25} />
        </g>
        {/* Rider 1 — incoming, slowing (LARGER) */}
        <HorseRiderSilhouette x={rider1X} y={780} scale={2.0} phase={lf * 0.7} />
        {/* Rider 2 — leaving, accelerating (LARGER) */}
        <HorseRiderSilhouette x={rider2X} y={780} scale={2.0} phase={lf * 1.0} />
        {/* Handoff: small letter shape between them */}
        {handoffP > 0 && handoffP < 1 && (
          <g transform={`translate(${interpolate(handoffP, [0, 1], [rider1X + 30, rider2X - 30])},${720 - Math.sin(handoffP * Math.PI) * 30})`}>
            <rect x={-12} y={-8} width={24} height={16} fill={C.text} stroke="#3a2a14" strokeWidth={1.5} />
            <circle cx={0} cy={2} r={3} fill={C.red} />
          </g>
        )}
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">a private network of riders</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V08_PacketBoats: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Coast silhouette; packet boat at dock; sails dropping
  const sailDrop = interpolate(lp, [0.3, 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const boatX = interpolate(lp, [0.6, 1], [780, 1100], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Moonlit sky */}
      <ellipse cx={1600} cy={350} rx={400} ry={280} fill="url(#glow-moon)" />
      <circle cx={1620} cy={300} r={42} fill="#e0e8f4" opacity={0.85} />
      <circle cx={1620} cy={300} r={28} fill="#f0f4ff" />
      {/* Water */}
      <rect x={0} y={780} width={1920} height={300} fill="#0a1024" />
      {Array.from({ length: 14 }).map((_, i) => {
        const wy = 800 + i * 18;
        return <path key={i} d={`M 0,${wy} Q 480,${wy + Math.sin((lf + i * 4) * 0.05) * 4} 960,${wy} T 1920,${wy}`} stroke="#1a2438" strokeWidth={1.4} fill="none" opacity={0.4} />;
      })}
      {/* Moonlit reflection */}
      <ellipse cx={1620} cy={830} rx={140} ry={14} fill="#a8c8e8" opacity={0.45} />
      <ellipse cx={1620} cy={870} rx={100} ry={10} fill="#a8c8e8" opacity={0.3} />
      {/* Coast cliff (left side) */}
      <path d="M 0,400 L 400,420 L 600,500 L 720,580 L 760,720 L 760,780 L 0,780 Z" fill={C.silhouette} />
      {/* Dock structure */}
      <rect x={680} y={780} width={300} height={20} fill={C.silhouette} />
      {[700, 800, 900].map((px, i) => (
        <rect key={i} x={px} y={780} width={8} height={50} fill={C.silhouette} />
      ))}
      {/* Packet boat */}
      <g transform={`translate(${boatX},800)`}>
        {/* Hull */}
        <path d="M -100,0 L 100,0 L 80,40 L -80,40 Z" fill={C.silhouette} />
        {/* Mast */}
        <line x1={0} y1={0} x2={0} y2={-200} stroke={C.silhouette} strokeWidth={5} />
        {/* Boom */}
        <line x1={-60} y1={-160} x2={60} y2={-160} stroke={C.silhouette} strokeWidth={3} />
        {/* Sails */}
        <path d={`M 0,-200 L ${-90 * sailDrop},${-50 + sailDrop * 30} L 0,-30 Z`} fill={C.silhouette} />
        <path d={`M 0,-200 L ${90 * sailDrop},${-50 + sailDrop * 30} L 0,-30 Z`} fill={C.silhouette} />
        {/* Lit lantern at bow */}
        <circle cx={80} cy={-10} r={6} fill="#ffc070" opacity={0.9} />
        <circle cx={80} cy={-10} r={20} fill="#ffc070" opacity={0.3} />
      </g>
      {/* Rider arriving on dock */}
      {lp < 0.7 && (
        <HorseRiderSilhouette x={interpolate(lp, [0, 0.7], [200, 760])} y={770} scale={0.95} phase={lf * 0.7} />
      )}
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">fast packet boats kept on standby</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V09_ClerksShifts: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Single candlelit window; clerk swap on chime; candle continuous
  const swapPhase = (lp < 0.55) ? 0 : 1;
  const candleFlicker = 0.85 + Math.sin(lf * 0.5) * 0.1;
  // Clock chimes at 0.55
  const chimeP = interpolate(lp, [0.45, 0.65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Office facade — full silhouette */}
      <rect x={0} y={0} width={1920} height={1080} fill={C.silhouette} />
      {/* Window — single lit (LARGER) */}
      <g transform="translate(960,540)">
        {/* Frame */}
        <rect x={-280} y={-340} width={560} height={680} fill="#3a2810" />
        <rect x={-260} y={-320} width={520} height={640} fill="url(#glow-candle)" opacity={candleFlicker} />
        {/* Window cross */}
        <line x1={0} y1={-320} x2={0} y2={320} stroke="#3a2810" strokeWidth={6} />
        <line x1={-260} y1={0} x2={260} y2={0} stroke="#3a2810" strokeWidth={6} />
        {/* Clerk silhouette inside (changes after 0.55) */}
        {swapPhase === 0 ? (
          <g transform="translate(-60,100) scale(1.4)">
            {/* Old clerk — bowed over desk */}
            <circle cx={0} cy={-70} r={22} fill={C.silhouette} />
            <path d="M -50,-50 L -28,-65 L 28,-65 L 50,-50 L 56,90 L -56,90 Z" fill={C.silhouette} />
            {/* Spectacles hint */}
            <circle cx={-9} cy={-72} r={3.5} fill={C.bg} opacity={0.55} />
            <circle cx={9} cy={-72} r={3.5} fill={C.bg} opacity={0.55} />
          </g>
        ) : (
          <g transform="translate(60,100) scale(1.4)">
            {/* New clerk — younger, upright */}
            <circle cx={0} cy={-80} r={20} fill={C.silhouette} />
            <path d="M -44,-60 L -25,-75 L 25,-75 L 44,-60 L 48,90 L -48,90 Z" fill={C.silhouette} />
          </g>
        )}
        {/* Candle on desk */}
        <rect x={210} y={170} width={8} height={56} fill={C.silhouette} />
        <ellipse cx={214} cy={154} rx={6} ry={13} fill="#ffd080" opacity={candleFlicker} />
        <circle cx={214} cy={150} r={3} fill="#fff0c0" />
        {/* Desk */}
        <rect x={-220} y={200} width={440} height={28} fill={C.silhouette} />
      </g>
      {/* Outside facade hatching (very subtle brick lines) */}
      {Array.from({ length: 12 }).map((_, i) => (
        <line key={i} x1={0} y1={i * 90} x2={1920} y2={i * 90} stroke="#0c0a04" strokeWidth={1} opacity={0.6} />
      ))}
      {/* Clock chime ripple at swap */}
      {chimeP > 0 && chimeP < 1 && (
        <g transform="translate(1700,200)" opacity={1 - chimeP}>
          <circle cx={0} cy={0} r={chimeP * 200} fill="none" stroke={C.gold} strokeWidth={2} />
          <text x={0} y={-30} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22}>· chime ·</text>
        </g>
      )}
      {/* Clock face */}
      <g transform={`translate(1700,200)`}>
        <circle cx={0} cy={0} r={80} fill={C.bg} stroke={C.gold} strokeWidth={3} />
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2;
          return <line key={i} x1={Math.cos(a) * 70} y1={Math.sin(a) * 70} x2={Math.cos(a) * 78} y2={Math.sin(a) * 78} stroke={C.gold} strokeWidth={2} />;
        })}
        <line x1={0} y1={0} x2={0} y2={-50} stroke={C.text} strokeWidth={3} />
        <line x1={0} y1={0} x2={30} y2={20} stroke={C.text} strokeWidth={4} />
        <circle cx={0} cy={0} r={5} fill={C.gold} />
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">clerks who slept in shifts</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V_ThreadCity: React.FC<{ frame: number; v: V; from: string; to: string; threadProgress: number; threadFinal: boolean }> = ({
  frame, v, from, to, threadProgress, threadFinal,
}) => {
  const lf = localFrame(frame, v);
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={540} rx={1500} ry={500} fill="url(#glow-ember)" opacity={0.5} />
      {/* Paris skyline silhouette (left) — Notre Dame inspired */}
      <g transform="translate(0,0)">
        <rect x={0} y={760} width={760} height={320} fill={C.silhouette} />
        {/* Notre Dame towers */}
        <rect x={140} y={580} width={70} height={180} fill={C.silhouette} />
        <rect x={240} y={580} width={70} height={180} fill={C.silhouette} />
        <polygon points="140,580 145,540 175,540 180,580" fill={C.silhouette} />
        <polygon points="240,580 245,540 275,540 280,580" fill={C.silhouette} />
        {/* Spire between */}
        <polygon points="200,540 220,440 240,540" fill={C.silhouette} />
        {/* Bridge */}
        <rect x={400} y={720} width={300} height={40} fill={C.silhouette} />
        <ellipse cx={460} cy={760} rx={40} ry={20} fill={C.bg} opacity={0.6} />
        <ellipse cx={560} cy={760} rx={40} ry={20} fill={C.bg} opacity={0.6} />
        <ellipse cx={660} cy={760} rx={40} ry={20} fill={C.bg} opacity={0.6} />
        <text x={300} y={1010} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={36} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">PARIS</text>
      </g>
      {/* London skyline silhouette (right) — St Paul's */}
      <g transform="translate(0,0)">
        <rect x={1160} y={760} width={760} height={320} fill={C.silhouette} />
        {/* St Paul's dome */}
        <ellipse cx={1500} cy={620} rx={90} ry={70} fill={C.silhouette} />
        <rect x={1430} y={620} width={140} height={140} fill={C.silhouette} />
        {/* Cross */}
        <line x1={1500} y1={550} x2={1500} y2={520} stroke={C.silhouette} strokeWidth={5} />
        <line x1={1490} y1={530} x2={1510} y2={530} stroke={C.silhouette} strokeWidth={3} />
        {/* Other buildings */}
        <rect x={1280} y={680} width={60} height={80} fill={C.silhouette} />
        <rect x={1620} y={660} width={70} height={100} fill={C.silhouette} />
        <rect x={1740} y={690} width={50} height={70} fill={C.silhouette} />
        <text x={1620} y={1010} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={36} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">LONDON</text>
      </g>
      {/* Thread between Paris and London */}
      <g>
        {/* Curve from (380, 600) to (1500, 580) with arc up */}
        <path d={`M 380,600 Q 940,${430 + Math.sin(lf * 0.05) * 6} 1500,580`}
          stroke={C.gold} strokeWidth={4}
          fill="none"
          strokeDasharray={2400}
          strokeDashoffset={2400 * (1 - threadProgress)}
          opacity={0.95} />
        {/* Glow underneath */}
        <path d={`M 380,600 Q 940,${430 + Math.sin(lf * 0.05) * 6} 1500,580`}
          stroke={C.gold} strokeWidth={14}
          fill="none"
          strokeDasharray={2400}
          strokeDashoffset={2400 * (1 - threadProgress)}
          opacity={0.18} />
        {/* Letter traveling along when thread complete */}
        {threadFinal && (() => {
          const t = (lf * 0.04) % 1;
          // Approximate point on curve
          const x = 380 + (1500 - 380) * t;
          const y = 600 + (580 - 600) * t - Math.sin(t * Math.PI) * 170;
          return (
            <g transform={`translate(${x},${y})`}>
              <rect x={-16} y={-12} width={32} height={24} fill={C.text} stroke="#3a2a14" strokeWidth={1.5} />
              <path d="M -16,-12 L 0,0 L 16,-12" fill="none" stroke="#3a2a14" strokeWidth={1.5} />
              <circle cx={0} cy={0} r={4} fill={C.red} />
            </g>
          );
        })()}
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">{threadFinal ? "did not enter a public mailbag" : `from ${from} to ${to}`}</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V12_RothschildTrio: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Three quick beats: hand passing letter / galloping horse / boat at sea
  const tt = lp * 3;
  const phase = Math.floor(tt);
  const localT = tt - phase;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {phase === 0 && (
        <g>
          {/* Hand passing letter — gold glow */}
          <ellipse cx={960} cy={540} rx={1300} ry={500} fill="url(#glow-dawn)" />
          {/* Two hands meeting */}
          <g transform="translate(960,540) scale(2)">
            {/* Hand left */}
            <ellipse cx={-80} cy={0} rx={60} ry={28} fill={C.silhouette} />
            <path d="M -50,-10 L -20,-20 L -20,-2 L -50,8 Z" fill={C.silhouette} />
            {/* Hand right */}
            <ellipse cx={80} cy={0} rx={60} ry={28} fill={C.silhouette} />
            <path d="M 50,-10 L 20,-20 L 20,-2 L 50,8 Z" fill={C.silhouette} />
            {/* Letter being passed */}
            <rect x={-30} y={-10 - localT * 20} width={60} height={36} fill={C.text} stroke="#3a2a14" strokeWidth={1.5} />
            <circle cx={20} cy={-localT * 20} r={6} fill={C.red} />
          </g>
          <text x={960} y={300} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="4" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">Rothschild hands</text>
        </g>
      )}
      {phase === 1 && (
        <g>
          {/* Galloping horse — ember glow */}
          <ellipse cx={960} cy={780} rx={1400} ry={500} fill="url(#glow-ember)" />
          <path d="M 0,720 L 1920,720 L 1920,1080 L 0,1080 Z" fill={C.silhouette} />
          <HorseRiderSilhouette x={interpolate(localT, [0, 1], [-200, 2120])} y={760} scale={1.6} phase={lf * 1.0} />
          <text x={960} y={300} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="4" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">Rothschild horses</text>
        </g>
      )}
      {phase >= 2 && (
        <g>
          {/* Boat at sea — moonlit */}
          <ellipse cx={1500} cy={350} rx={400} ry={280} fill="url(#glow-moon)" />
          <circle cx={1620} cy={300} r={42} fill="#e0e8f4" />
          <rect x={0} y={780} width={1920} height={300} fill="#0a1024" />
          {Array.from({ length: 14 }).map((_, i) => {
            const wy = 800 + i * 18;
            return <path key={i} d={`M 0,${wy} Q 480,${wy + Math.sin((lf + i * 4) * 0.05) * 4} 960,${wy} T 1920,${wy}`} stroke="#1a2438" strokeWidth={1.4} fill="none" opacity={0.4} />;
          })}
          <ellipse cx={1620} cy={830} rx={140} ry={14} fill="#a8c8e8" opacity={0.45} />
          {/* Boat */}
          <g transform={`translate(${interpolate(localT, [0, 1], [200, 1700])},800)`}>
            <path d="M -100,0 L 100,0 L 80,40 L -80,40 Z" fill={C.silhouette} />
            <line x1={0} y1={0} x2={0} y2={-200} stroke={C.silhouette} strokeWidth={5} />
            <path d="M 0,-200 L -90,-50 L 0,-30 Z" fill={C.silhouette} />
            <path d="M 0,-200 L 90,-50 L 0,-30 Z" fill={C.silhouette} />
            <circle cx={80} cy={-10} r={6} fill="#ffc070" />
            <circle cx={80} cy={-10} r={18} fill="#ffc070" opacity={0.3} />
          </g>
          <text x={960} y={300} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={32} letterSpacing="4" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">Rothschild boats</text>
        </g>
      )}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V_DenialStamp: React.FC<{ frame: number; v: V; figure: "customs" | "banker" | "spy"; label: string }> = ({ frame, v, figure, label }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  const figureP = interpolate(lp, [0, 0.4], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const stampP = interpolate(lp, [0.45, 0.65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const stampScale = interpolate(stampP, [0, 0.6, 1], [0.4, 1.3, 1.0], { easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={540} rx={1300} ry={500} fill="url(#glow-ember)" opacity={0.5} />
      {/* Figure */}
      <g transform={`translate(960,720) scale(${1.2 * figureP})`} opacity={figureP}>
        {figure === "customs" && (
          <g>
            {/* Officer with seal stamper raised */}
            <circle cx={0} cy={-180} r={36} fill={C.silhouette} />
            {/* Tricorn */}
            <path d="M -50,-200 L 50,-200 L 0,-228 Z" fill={C.silhouette} />
            <path d="M -55,-200 L 55,-200 L 60,-190 L -60,-190 Z" fill={C.silhouette} />
            {/* Body */}
            <path d="M -60,-140 L -40,-160 L 40,-160 L 60,-140 L 80,200 L -80,200 Z" fill={C.silhouette} />
            {/* Arm raised holding stamper */}
            <line x1={50} y1={-130} x2={120} y2={-220} stroke={C.silhouette} strokeWidth={18} strokeLinecap="round" />
            <rect x={108} y={-244} width={28} height={36} fill={C.silhouette} />
          </g>
        )}
        {figure === "banker" && (
          <g>
            <circle cx={0} cy={-180} r={36} fill={C.silhouette} />
            <rect x={-32} y={-220} width={64} height={48} fill={C.silhouette} />
            <rect x={-44} y={-176} width={88} height={8} fill={C.silhouette} />
            {/* Body */}
            <path d="M -60,-140 L -40,-160 L 40,-160 L 60,-140 L 80,200 L -80,200 Z" fill={C.silhouette} />
            {/* Magnifying glass in hand */}
            <line x1={50} y1={-100} x2={110} y2={-160} stroke={C.silhouette} strokeWidth={10} strokeLinecap="round" />
            <circle cx={130} cy={-180} r={26} fill="none" stroke={C.silhouette} strokeWidth={8} />
            <circle cx={130} cy={-180} r={20} fill={C.bg} opacity={0.4} />
          </g>
        )}
        {figure === "spy" && (
          <g>
            {/* Cloak */}
            <path d="M -90,-160 L -50,-200 L 50,-200 L 90,-160 L 100,200 L -100,200 Z" fill={C.silhouette} />
            {/* Hooded head */}
            <ellipse cx={0} cy={-200} rx={36} ry={42} fill={C.silhouette} />
            <path d="M -42,-220 Q 0,-260 42,-220 L 42,-180 L -42,-180 Z" fill={C.silhouette} />
            {/* Eyes — visible cuts */}
            <line x1={-14} y1={-200} x2={-6} y2={-200} stroke="#c8a040" strokeWidth={2} />
            <line x1={6} y1={-200} x2={14} y2={-200} stroke="#c8a040" strokeWidth={2} />
          </g>
        )}
      </g>
      {/* Label below */}
      <g transform="translate(960,960)" opacity={figureP}>
        <rect x={-220} y={-40} width={440} height={80} fill={C.bg} stroke={C.gold} strokeWidth={2} />
        <text x={0} y={14} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={32} letterSpacing="6" stroke="#000" strokeWidth={2} paintOrder="stroke fill">{label}</text>
      </g>
      {/* Big CLASSIFIED/DENIED stamp */}
      <g transform={`translate(960,440) rotate(-12) scale(${stampScale})`} opacity={stampP}>
        <rect x={-280} y={-110} width={560} height={220} fill="none" stroke={C.red} strokeWidth={10} />
        <text x={0} y={-10} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={84} letterSpacing="10" stroke="#000" strokeWidth={3} paintOrder="stroke fill">DENIED</text>
        <text x={0} y={64} textAnchor="middle" fill={C.red} fontFamily="Courier New, monospace" fontWeight={700} fontSize={26} letterSpacing="6">no access · no copy · no decode</text>
      </g>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V16_RoworthWaterloo: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Battlefield haze */}
      <ellipse cx={960} cy={680} rx={1500} ry={520} fill="url(#glow-battle)" />
      {/* Distant ridge with cannons */}
      <path d="M 0,720 L 200,710 L 360,730 L 540,710 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,820 L 0,820 Z" fill={C.silhouette} />
      {/* Cannons (small silhouettes on ridge) */}
      {[300, 700, 1100, 1500].map((cx, i) => (
        <g key={i} transform={`translate(${cx},700)`}>
          <rect x={-18} y={0} width={36} height={14} fill={C.silhouette} />
          <line x1={0} y1={4} x2={36} y2={-6} stroke={C.silhouette} strokeWidth={6} />
          <circle cx={-22} cy={10} r={6} fill={C.silhouette} />
          <circle cx={22} cy={10} r={6} fill={C.silhouette} />
        </g>
      ))}
      {/* Smoke wisps */}
      <SmokeWisps frame={lf} count={20} spread={[0, 500, 1920, 800]} />
      {/* Foreground ground */}
      <rect x={0} y={820} width={1920} height={260} fill={C.silhouette} />
      {/* Roworth on horseback — facing left, looking back at battle */}
      <g transform="translate(960,800) scale(1.6)">
        {/* Horse standing */}
        <ellipse cx={0} cy={0} rx={50} ry={18} fill={C.silhouette} />
        <path d="M -35,-2 Q -56,-26 -64,-36 L -54,-36 Q -42,-22 -28,-10 Z" fill={C.silhouette} />
        <rect x={-32} y={16} width={6} height={32} fill={C.silhouette} />
        <rect x={-16} y={16} width={6} height={32} fill={C.silhouette} />
        <rect x={16} y={16} width={6} height={32} fill={C.silhouette} />
        <rect x={32} y={16} width={6} height={32} fill={C.silhouette} />
        <path d="M 50,-2 Q 64,12 60,28" stroke={C.silhouette} strokeWidth={5} fill="none" strokeLinecap="round" />
        {/* Roworth — looking back over shoulder */}
        <circle cx={6} cy={-32} r={11} fill={C.silhouette} />
        <path d="M -4,-22 Q 6,-2 16,-14 L 16,-26 Q 12,-36 0,-30 Z" fill={C.silhouette} />
        <path d="M -4,-40 L 16,-40 L 6,-46 Z" fill={C.silhouette} />
      </g>
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">a man named Roworth · on the field at Waterloo</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V17_RoworthDecision: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tight on Roworth; smoke clearing; horse stamps
  const zoom = interpolate(lp, [0, 1], [1.0, 1.4], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <ellipse cx={960} cy={540} rx={1500} ry={520} fill="url(#glow-battle)" opacity={0.7} />
      {/* Smoke clearing — fades as lp increases */}
      <g opacity={1 - lp * 0.7}>
        <SmokeWisps frame={lf} count={30} spread={[200, 200, 1720, 800]} />
      </g>
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom}) scale(${zoom})`}>
        <rect x={0} y={820} width={1920} height={260} fill={C.silhouette} />
        {/* Roworth on horseback — same as V16 but tighter */}
        <g transform="translate(960,800) scale(1.6)">
          <ellipse cx={0} cy={0} rx={50} ry={18} fill={C.silhouette} />
          <path d="M -35,-2 Q -56,-26 -64,-36 L -54,-36 Q -42,-22 -28,-10 Z" fill={C.silhouette} />
          {/* Stamping foreleg */}
          <rect x={-32} y={16} width={6} height={32 + Math.sin(lf * 0.5) * 6} fill={C.silhouette} />
          <rect x={-16} y={16} width={6} height={32} fill={C.silhouette} />
          <rect x={16} y={16} width={6} height={32} fill={C.silhouette} />
          <rect x={32} y={16} width={6} height={32 + Math.sin(lf * 0.5 + 1) * 6} fill={C.silhouette} />
          <path d="M 50,-2 Q 64,12 60,28" stroke={C.silhouette} strokeWidth={5} fill="none" strokeLinecap="round" />
          <circle cx={6} cy={-32} r={11} fill={C.silhouette} />
          <path d="M -4,-22 Q 6,-2 16,-14 L 16,-26 Q 12,-36 0,-30 Z" fill={C.silhouette} />
          <path d="M -4,-40 L 16,-40 L 6,-46 Z" fill={C.silhouette} />
        </g>
      </g>
      {/* Caption */}
      <text x={120} y={130} fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={28} letterSpacing="3" opacity={0.9} stroke="#000" strokeWidth={2} paintOrder="stroke fill">he doesn't wait for confirmation</text>
      <text x={120} y={170} fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={22} letterSpacing="2" opacity={0.7}>he doesn't wait for orders · he doesn't wait for the official dispatch</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

const V18_RoworthRides: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Tracking gallop INTO vanishing-point glow — final freeze on tiny silhouette
  // Camera follows: rider moves into distance (gets smaller, recedes)
  const riderScale = interpolate(lp, [0, 0.85, 1], [2.0, 0.4, 0.3], { easing: ease });
  const riderY = interpolate(lp, [0, 0.85, 1], [840, 760, 740], { easing: ease });
  const riderX = interpolate(lp, [0, 0.85, 1], [400, 1100, 1140], { easing: ease });
  // Glow grows as we approach
  const glowR = interpolate(lp, [0, 1], [400, 800], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <GlowDefs />
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      {/* Vanishing-point glow — bright center */}
      <radialGradient id="g-vanish">
        <stop offset="0%" stopColor="#ffe080" stopOpacity={1} />
        <stop offset="20%" stopColor="#ffaa50" stopOpacity={0.85} />
        <stop offset="50%" stopColor={C.gold} stopOpacity={0.45} />
        <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
      </radialGradient>
      <ellipse cx={1140} cy={760} rx={glowR * 1.5} ry={glowR} fill="url(#g-vanish)" />
      {/* Sun disc at vanishing point */}
      <circle cx={1140} cy={760} r={interpolate(lp, [0, 1], [60, 110])} fill="#ffe080" opacity={0.7} />
      <circle cx={1140} cy={760} r={interpolate(lp, [0, 1], [40, 70])} fill="#fff0c0" />
      {/* Foreground silhouette ground */}
      <path d={`M 0,${interpolate(lp, [0, 1], [880, 800])} L 1920,${interpolate(lp, [0, 1], [880, 800])} L 1920,1080 L 0,1080 Z`} fill={C.silhouette} />
      {/* Rays of light from sun */}
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i / 12) * Math.PI * 2;
        const len = 200 + Math.abs(Math.sin(lf * 0.05 + i)) * 30;
        return <line key={i} x1={1140} y1={760}
          x2={1140 + Math.cos(a) * len} y2={760 + Math.sin(a) * len}
          stroke={C.gold} strokeWidth={2} opacity={0.25} />;
      })}
      {/* Rider receding into glow */}
      <g transform={`translate(${riderX},${riderY}) scale(${riderScale})`}>
        <HorseRiderSilhouette x={0} y={0} scale={1} phase={lf * 1.0} />
      </g>
      {/* Dust trail */}
      {Array.from({ length: 16 }).map((_, i) => {
        const trail = (lf * 1.5 - i * 4) % 60;
        const tx = riderX - trail * 5;
        const ty = riderY + 20 + Math.sin((lf + i) * 0.3) * 4;
        const op = Math.max(0, 0.5 - trail / 60) * (1 - lp);
        return <circle key={i} cx={tx} cy={ty} r={5 + (i % 3) * 2} fill="#3a2410" opacity={op} />;
      })}
      {/* Final caption */}
      <text x={960} y={1010} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={36} letterSpacing="4" stroke="#000" strokeWidth={2} paintOrder="stroke fill">he simply turns his horse north · and rides</text>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#vignetteCh2)" />
    </svg>
  );
};

// ── Main ────────────────────────────────────────────────────────────────────

export const LetterDynastyChapter2: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <Audio src={staticFile("letter-dynasty-chapter2.mp3")} />
      {VIGNETTES.map((v, i) => {
        const op = vOpacity(frame, v);
        if (op <= 0.001) return null;
        const lp = localProgress(frame, v);
        let content: React.ReactNode = null;
        switch (v.name) {
          case "crown-coach":      content = <V01_CrownCoach frame={frame} v={v} />; break;
          case "four-days":        content = <V02_FourDays frame={frame} v={v} />; break;
          case "good-week":        content = <V03_GoodWeek frame={frame} v={v} />; break;
          case "weather-channel":  content = <V04_WeatherChannel frame={frame} v={v} />; break;
          case "rothschild-rider": content = <V05_RothschildRider frame={frame} v={v} />; break;
          case "weather-cycle":    content = <V06_WeatherCycle frame={frame} v={v} />; break;
          case "private-network":  content = <V07_PrivateNetwork frame={frame} v={v} />; break;
          case "packet-boats":     content = <V08_PacketBoats frame={frame} v={v} />; break;
          case "clerks-shifts":    content = <V09_ClerksShifts frame={frame} v={v} />; break;
          case "thread-paris":     content = <V_ThreadCity frame={frame} v={v} from="Paris" to="London" threadProgress={interpolate(lp, [0.1, 1], [0, 0.55], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut })} threadFinal={false} />; break;
          case "thread-london":    content = <V_ThreadCity frame={frame} v={v} from="Paris" to="London" threadProgress={interpolate(lp, [0, 0.7], [0.55, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut })} threadFinal={lp > 0.5} />; break;
          case "rothschild-trio":  content = <V12_RothschildTrio frame={frame} v={v} />; break;
          case "deny-customs":     content = <V_DenialStamp frame={frame} v={v} figure="customs" label="NO CUSTOMS OFFICER OPENED IT" />; break;
          case "deny-banker":      content = <V_DenialStamp frame={frame} v={v} figure="banker" label="NO COMPETING BANKER COPIED IT" />; break;
          case "deny-spy":         content = <V_DenialStamp frame={frame} v={v} figure="spy" label="NO KING'S SPY DECODED IT" />; break;
          case "roworth-waterloo": content = <V16_RoworthWaterloo frame={frame} v={v} />; break;
          case "roworth-decision": content = <V17_RoworthDecision frame={frame} v={v} />; break;
          case "roworth-rides":    content = <V18_RoworthRides frame={frame} v={v} />; break;
        }
        return <AbsoluteFill key={i} style={{ opacity: op }}>{content}</AbsoluteFill>;
      })}
    </AbsoluteFill>
  );
};
