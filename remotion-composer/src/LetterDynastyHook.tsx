/**
 * Letter That Built A Dynasty — HOOK section.
 * Style: limited-palette flat illustration. Channel: Midnight Magnates.
 * 71s, 14 vignettes, 24fps, 1920×1080.
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

// ── Channel tokens (from Midnight Magnates playbook) ─────────────────────────
const C = {
  bg: mmTheme.bg,           // #080c16
  text: mmTheme.text,       // #f5f0e4
  gold: mmTheme.accent,     // #c9a84c
  goldDim: "#8c6e23",
  blue: "#4a6fa5",
  red: mmTheme.stampRed,    // #b41e1e
  ink: "#0d1a2a",
};

const FPS = 24;
const DURATION_S = 71;
export const LETTER_HOOK_DURATION_FRAMES = Math.ceil(DURATION_S * FPS);

// ── Stroke + shadow recipe (mandatory channel rule) ──────────────────────────
const TEXT_STROKE: React.CSSProperties = {
  textShadow:
    "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000," +
    "1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000," +
    "0 4px 14px rgba(0,0,0,0.55)",
};

// ── Vignette boundaries (in seconds) ─────────────────────────────────────────
type V = { name: string; start: number; end: number };
const VIGNETTES: V[] = [
  { name: "channel-dawn",     start: 0,  end: 6 },
  { name: "letter-glide",     start: 6,  end: 12 },
  { name: "overtake-courier", start: 12, end: 17 },
  { name: "admiralty",        start: 17, end: 22 },
  { name: "foreign-office",   start: 22, end: 27 },
  { name: "king",             start: 27, end: 32 },
  { name: "couriers-london",  start: 32, end: 37 },
  { name: "belgium",          start: 37, end: 42 },
  { name: "exchange-ext",     start: 42, end: 47 },
  { name: "nathan-window",    start: 47, end: 52 },
  { name: "name-card",        start: 52, end: 56 },
  { name: "sun-arc-coins",    start: 56, end: 61 },
  { name: "calendar-back",    start: 61, end: 66 },
  { name: "arrows-info",      start: 66, end: 71 },
];

// Dissolve duration between vignettes
const DISSOLVE_S = 0.7;

// ── Helpers ──────────────────────────────────────────────────────────────────
const ease = Easing.inOut(Easing.cubic);
const easeOut = Easing.out(Easing.cubic);

function vOpacity(frame: number, v: V): number {
  const startF = v.start * FPS;
  const endF = v.end * FPS;
  const dF = DISSOLVE_S * FPS;
  // Fade in first, fade out at end
  const fadeIn = interpolate(frame, [startF - dF / 2, startF + dF / 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  const fadeOut = interpolate(frame, [endF - dF / 2, endF + dF / 2], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });
  return Math.min(fadeIn, fadeOut);
}

function localProgress(frame: number, v: V): number {
  // 0 → 1 across the vignette
  const startF = v.start * FPS;
  const endF = v.end * FPS;
  return Math.max(0, Math.min(1, (frame - startF) / (endF - startF)));
}

function localFrame(frame: number, v: V): number {
  return frame - v.start * FPS;
}

// ── Reusable atmospheric layers ──────────────────────────────────────────────

const StarSpeck: React.FC<{ x: number; y: number; r: number; phase: number; frame: number }> = ({ x, y, r, phase, frame }) => {
  const tw = (Math.sin((frame + phase) * 0.15) + 1) / 2;
  return <circle cx={x} cy={y} r={r} fill={C.text} opacity={0.15 + tw * 0.45} />;
};

const DustMotes: React.FC<{ frame: number; count?: number; spread?: [number, number, number, number] }> = ({
  frame,
  count = 30,
  spread = [0, 0, 1920, 1080],
}) => {
  const [x0, y0, x1, y1] = spread;
  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const seed = i * 137.5;
        const baseX = x0 + ((seed * 7) % (x1 - x0));
        const baseY = y0 + ((seed * 13) % (y1 - y0));
        const drift = ((frame + seed) * 0.25) % 60;
        const x = baseX + drift;
        const y = baseY - drift * 0.4 + Math.sin(frame * 0.05 + seed) * 4;
        const op = 0.10 + ((seed * 0.31) % 0.15);
        return <circle key={i} cx={x % 1920} cy={y % 1080} r={1.2 + (i % 3) * 0.5} fill={C.gold} opacity={op} />;
      })}
    </>
  );
};

const Waves: React.FC<{ frame: number; horizonY: number; amplitude?: number }> = ({ frame, horizonY, amplitude = 1 }) => {
  // Three layered wave bands at different speeds
  const layers = [
    { y: horizonY + 80, speed: 0.4, color: C.ink, amp: 14 * amplitude },
    { y: horizonY + 180, speed: 0.6, color: "#0a1322", amp: 18 * amplitude },
    { y: horizonY + 320, speed: 0.9, color: "#060a14", amp: 22 * amplitude },
  ];
  return (
    <>
      {layers.map((L, i) => {
        const phase = frame * L.speed;
        // Build a wavy path of width 2400 (overflows for parallax)
        const points: string[] = [];
        const w = 2400;
        const offset = -((phase * 1.4) % 240);
        for (let x = 0; x <= w; x += 30) {
          const wave = Math.sin((x + phase * 1.5) * 0.012 + i) * L.amp;
          points.push(`${x + offset},${L.y + wave}`);
        }
        const path = `M ${points.join(" L ")} L ${w + offset},1080 L ${offset},1080 Z`;
        return <path key={i} d={path} fill={L.color} />;
      })}
    </>
  );
};

const Gull: React.FC<{ x: number; y: number; scale?: number; phase?: number }> = ({ x, y, scale = 1, phase = 0 }) => (
  <g transform={`translate(${x},${y}) scale(${scale})`} opacity={0.6}>
    <path d={`M -20,0 Q -10,${-8 + Math.sin(phase) * 3} 0,0 Q 10,${-8 + Math.sin(phase + 0.5) * 3} 20,0`} stroke={C.text} strokeWidth={2} fill="none" strokeLinecap="round" />
  </g>
);

// ── Reusable subject primitives ──────────────────────────────────────────────

const Letter: React.FC<{ x: number; y: number; rot?: number; scale?: number; sealPulse?: number }> = ({ x, y, rot = 0, scale = 1, sealPulse = 1 }) => (
  <g transform={`translate(${x},${y}) rotate(${rot}) scale(${scale})`}>
    {/* Envelope body */}
    <rect x={-60} y={-40} width={120} height={80} fill={C.text} stroke={C.ink} strokeWidth={2} />
    {/* Triangular flap */}
    <path d="M -60,-40 L 0,8 L 60,-40 Z" fill="#e8dec8" stroke={C.ink} strokeWidth={1.5} />
    {/* Wax seal */}
    <circle cx={0} cy={8} r={14 * sealPulse} fill={C.red} stroke="#7a1414" strokeWidth={1.5} />
    <circle cx={0} cy={8} r={6 * sealPulse} fill="#8a1818" />
  </g>
);

const HorseRider: React.FC<{ x: number; y: number; scale?: number; phase?: number; flipX?: boolean; color?: string }> = ({
  x, y, scale = 1, phase = 0, flipX = false, color,
}) => {
  const bob = Math.sin(phase) * 4;
  return (
    <g transform={`translate(${x},${y + bob}) scale(${flipX ? -scale : scale}, ${scale})`}>
      {/* Horse body */}
      <ellipse cx={0} cy={0} rx={42} ry={16} fill={color ?? C.ink} />
      {/* Horse neck + head */}
      <path d="M 30,-2 Q 50,-22 56,-30 L 48,-30 Q 38,-18 25,-8 Z" fill={color ?? C.ink} />
      {/* Horse legs (animated by phase) */}
      <rect x={-26} y={14} width={6} height={24 + Math.sin(phase * 1.4) * 4} fill={color ?? C.ink} />
      <rect x={-12} y={14} width={6} height={24 - Math.sin(phase * 1.4) * 4} fill={color ?? C.ink} />
      <rect x={14} y={14} width={6} height={24 - Math.sin(phase * 1.4) * 4} fill={color ?? C.ink} />
      <rect x={28} y={14} width={6} height={24 + Math.sin(phase * 1.4) * 4} fill={color ?? C.ink} />
      {/* Tail */}
      <path d={`M -42,-2 Q -56,${4 + Math.sin(phase) * 4} -52,18`} stroke={color ?? C.ink} strokeWidth={4} fill="none" strokeLinecap="round" />
      {/* Rider */}
      <circle cx={6} cy={-26} r={9} fill={color ?? C.ink} />
      <path d={`M -2,-18 Q 6,-2 14,-12 L 14,-22 Q 10,-30 0,-26 Z`} fill={color ?? C.ink} />
    </g>
  );
};

// ── Vignette renderers ───────────────────────────────────────────────────────

const V01_ChannelDawn: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera: subtle horizontal drift
  const camX = interpolate(lp, [0, 1], [0, -40], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080" style={{ display: "block" }}>
      <defs>
        {/* Sky gradient — pre-dawn fading toward warmer horizon */}
        <linearGradient id="sky1" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#04060e" />
          <stop offset="55%" stopColor="#0a1226" />
          <stop offset="78%" stopColor="#3a2616" />
          <stop offset="92%" stopColor="#7a4818" />
          <stop offset="100%" stopColor="#b8702a" />
        </linearGradient>
        {/* Bright dawn radial */}
        <radialGradient id="dawn1" cx="50%" cy="92%" r="60%">
          <stop offset="0%" stopColor="#f0a050" stopOpacity={0.9} />
          <stop offset="35%" stopColor={C.gold} stopOpacity={0.55} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
      </defs>
      {/* Sky */}
      <rect x={0} y={0} width={1920} height={1080} fill="url(#sky1)" />
      {/* Star specks */}
      {Array.from({ length: 40 }).map((_, i) => (
        <StarSpeck key={i} x={(i * 89) % 1920} y={(i * 53) % 480} r={i % 5 === 0 ? 1.6 : 0.9} phase={i * 11} frame={frame} />
      ))}
      {/* Dawn radial glow (bright wash above horizon) */}
      <g transform={`translate(${camX},0)`}>
        <ellipse cx={960} cy={780} rx={1300} ry={480} fill="url(#dawn1)" />
      </g>
      {/* Distant cliffs silhouette */}
      <g transform={`translate(${camX * 1.3},0)`}>
        <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,820 L 0,820 Z" fill="#02030a" />
      </g>
      {/* Waves */}
      <g transform={`translate(${camX * 0.8},0)`}>
        <Waves frame={lf} horizonY={760} />
      </g>
      {/* Gold reflection on water */}
      <ellipse cx={960} cy={830} rx={300} ry={28} fill={C.gold} opacity={0.25} />
      <ellipse cx={960} cy={870} rx={220} ry={18} fill={C.gold} opacity={0.18} />
      {/* Gulls */}
      <Gull x={300 + lf * 1.2} y={240} scale={0.8} phase={lf * 0.4} />
      <Gull x={1200 - lf * 1.0} y={180} scale={1.0} phase={lf * 0.5 + 1.2} />
      <Gull x={1500 + lf * 0.8} y={300} scale={0.6} phase={lf * 0.3 + 2.4} />
      <DustMotes frame={lf} count={20} spread={[0, 100, 1920, 700]} />
    </svg>
  );
};

const V02_LetterGlide: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Letter drops in then glides L→R
  const letterX = interpolate(lp, [0, 0.2, 1], [-200, 400, 1700], { easing: easeOut });
  const letterY = interpolate(lp, [0, 0.25, 1], [-100, 460, 480], { easing: easeOut });
  const letterRot = Math.sin(lf * 0.15) * 4;
  const sealPulse = 1 + Math.sin(lf * 0.4) * 0.06;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="sky2" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#06091a" />
          <stop offset="50%" stopColor="#0e1830" />
          <stop offset="78%" stopColor="#5a3418" />
          <stop offset="100%" stopColor="#c87a30" />
        </linearGradient>
        <radialGradient id="dawn2" cx="50%" cy="92%" r="60%">
          <stop offset="0%" stopColor="#ffb060" stopOpacity={0.95} />
          <stop offset="40%" stopColor={C.gold} stopOpacity={0.55} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#sky2)" />
      <ellipse cx={960} cy={780} rx={1300} ry={480} fill="url(#dawn2)" />
      {/* Sun disc rising at right */}
      <circle cx={1500} cy={720} r={60} fill="#ffd080" opacity={0.45} />
      <circle cx={1500} cy={720} r={42} fill="#ffd080" />
      <circle cx={1500} cy={720} r={28} fill="#fff0c0" />
      {/* Cliffs */}
      <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,820 L 0,820 Z" fill="#02030a" />
      <Waves frame={lf} horizonY={760} amplitude={1.1} />
      {/* Sun reflection on water */}
      <ellipse cx={1500} cy={830} rx={140} ry={14} fill="#ffd080" opacity={0.5} />
      <ellipse cx={1500} cy={870} rx={100} ry={10} fill={C.gold} opacity={0.35} />
      {/* Sea spray particles trailing the letter */}
      {Array.from({ length: 12 }).map((_, i) => {
        const trail = (lf * 1.8 - i * 6) % 80;
        const tx = letterX - trail * 2;
        const ty = letterY + 60 + Math.sin((lf + i) * 0.3) * 4;
        return <circle key={i} cx={tx} cy={ty} r={1.5 + (i % 3) * 0.7} fill={C.text} opacity={Math.max(0, 0.5 - trail / 80)} />;
      })}
      <Letter x={letterX} y={letterY} rot={letterRot} sealPulse={sealPulse} />
      <DustMotes frame={lf} count={18} spread={[0, 200, 1920, 700]} />
    </svg>
  );
};

const V03_OvertakeCourier: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera pans horizontally
  const camX = interpolate(lp, [0, 1], [0, -100], { easing: ease });
  // Crown courier on the clifftop road — visible near horizon, scaled larger
  const courierX = interpolate(lp, [0, 1], [200, 1300], { easing: easeOut });
  // Letter overtakes (faster, sweeps fully across)
  const letterX = interpolate(lp, [0, 1], [-150, 2100], { easing: easeOut });
  const letterY = 460 + Math.sin(lf * 0.18) * 12;
  const trailLen = 260;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="sky3" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#08111e" />
          <stop offset="55%" stopColor="#102036" />
          <stop offset="80%" stopColor="#74441e" />
          <stop offset="100%" stopColor="#d68a40" />
        </linearGradient>
        <linearGradient id="trail3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0} />
          <stop offset="100%" stopColor="#ffd080" stopOpacity={1} />
        </linearGradient>
        <radialGradient id="dawn3" cx="50%" cy="92%" r="60%">
          <stop offset="0%" stopColor="#ffb060" stopOpacity={0.85} />
          <stop offset="40%" stopColor={C.gold} stopOpacity={0.45} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#sky3)" />
      <ellipse cx={960} cy={780} rx={1300} ry={480} fill="url(#dawn3)" />
      {/* Sun */}
      <circle cx={1480} cy={720} r={48} fill="#ffd080" opacity={0.5} />
      <circle cx={1480} cy={720} r={32} fill="#ffd080" />
      {/* Clifftop with road */}
      <g transform={`translate(${camX * 0.6},0)`}>
        <path d="M 0,720 L 200,680 L 360,710 L 540,690 L 720,720 L 900,705 L 1100,725 L 1300,700 L 1500,720 L 1700,705 L 1920,725 L 1920,820 L 0,820 Z" fill="#02030a" />
        {/* Road on cliff */}
        <path d="M 0,716 L 1920,716" stroke="#1a1408" strokeWidth={3} opacity={0.7} strokeDasharray="20 14" />
      </g>
      <Waves frame={lf} horizonY={760} />
      {/* Sun reflection */}
      <ellipse cx={1480} cy={830} rx={130} ry={12} fill="#ffd080" opacity={0.45} />
      {/* Crown courier on the road — clearly visible against horizon */}
      <g transform={`translate(${camX},0)`}>
        <HorseRider x={courierX} y={700} scale={1.05} phase={lf * 0.6} color="#020308" />
        {/* Dust kicked up */}
        {Array.from({ length: 5 }).map((_, i) => {
          const dx = courierX - 30 - i * 14;
          const dy = 720 + Math.sin((lf + i * 4) * 0.3) * 3;
          const op = Math.max(0, 0.4 - i * 0.08);
          return <circle key={i} cx={dx} cy={dy} r={3 + i} fill="#3a2a14" opacity={op} />;
        })}
      </g>
      {/* Letter trail (gold streak) */}
      <rect x={letterX - trailLen} y={letterY - 5} width={trailLen} height={10} fill="url(#trail3)" rx={2} />
      <Letter x={letterX} y={letterY} rot={Math.sin(lf * 0.2) * 4} sealPulse={1 + Math.sin(lf * 0.4) * 0.05} />
      <DustMotes frame={lf} count={20} spread={[0, 200, 1920, 700]} />
    </svg>
  );
};

// Generic "letter zips past a building" scene used for vignettes 4-6
const V_LetterPastBuilding: React.FC<{
  frame: number; v: V;
  label: string;
  building: React.ReactNode;
  flagBob?: boolean;
}> = ({ frame, v, label, building, flagBob }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  const letterX = interpolate(lp, [0, 1], [-200, 2120], { easing: easeOut });
  const letterY = 320 + Math.sin(lf * 0.18) * 18;
  // Building fades in with slight scale
  const buildingOp = interpolate(lp, [0, 0.15], [0, 1], { extrapolateRight: "clamp", easing: easeOut });
  const buildingY = interpolate(lp, [0, 0.15], [40, 0], { extrapolateRight: "clamp", easing: easeOut });
  const labelOp = interpolate(lp, [0.35, 0.55, 0.85, 1], [0, 1, 1, 0], { easing: ease });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <defs>
        <radialGradient id="ambient" cx="50%" cy="40%" r="80%">
          <stop offset="0%" stopColor="#1a2640" stopOpacity={0.9} />
          <stop offset="60%" stopColor="#0c1424" stopOpacity={0.6} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
        <linearGradient id="trailB" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0} />
          <stop offset="100%" stopColor="#ffd080" stopOpacity={1} />
        </linearGradient>
        {/* Soft brass shaft of light from above */}
        <linearGradient id="shaft" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0.15} />
          <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#ambient)" />
      {/* Soft single shaft of brass light (proper gradient fade) */}
      <polygon points="780,0 1140,0 1240,1080 680,1080" fill="url(#shaft)" />
      {/* Building */}
      <g transform={`translate(0,${buildingY})`} opacity={buildingOp}>{building}</g>
      {/* Letter trail */}
      <rect x={letterX - 240} y={letterY - 5} width={240} height={10} fill="url(#trailB)" rx={2} />
      <Letter x={letterX} y={letterY} rot={Math.sin(lf * 0.2) * 5} sealPulse={1 + Math.sin(lf * 0.4) * 0.06} />
      {/* Label tag (bottom) */}
      <g opacity={labelOp}>
        <rect x={660} y={948} width={600} height={84} fill={C.bg} stroke={C.gold} strokeWidth={3} />
        <rect x={672} y={960} width={576} height={60} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.5} />
        <text
          x={960} y={1003} textAnchor="middle"
          fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={36}
          stroke="#000" strokeWidth={2} paintOrder="stroke fill"
          letterSpacing="4">{label}</text>
      </g>
      <DustMotes frame={lf} count={22} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

const AdmiraltyDome: React.FC<{ frame: number }> = ({ frame }) => {
  const flagWave = Math.sin(frame * 0.18) * 6;
  return (
    <g>
      {/* Façade */}
      <rect x={620} y={520} width={680} height={420} fill="#10182a" stroke={C.gold} strokeWidth={2} />
      {/* Columns */}
      {[0, 1, 2, 3, 4, 5].map(i => (
        <rect key={i} x={650 + i * 105} y={560} width={26} height={380} fill="#162236" />
      ))}
      {/* Steps */}
      <polygon points="600,940 1320,940 1280,970 640,970" fill="#0c1626" />
      {/* Dome base */}
      <rect x={780} y={420} width={360} height={120} fill="#162236" stroke={C.gold} strokeWidth={2} />
      {/* Dome */}
      <ellipse cx={960} cy={420} rx={180} ry={140} fill="#1a263e" stroke={C.gold} strokeWidth={2} />
      {/* Dome highlight */}
      <ellipse cx={920} cy={400} rx={70} ry={50} fill={C.gold} opacity={0.18} />
      {/* Mast */}
      <line x1={960} y1={280} x2={960} y2={200} stroke={C.gold} strokeWidth={3} />
      {/* Flag */}
      <path d={`M 960,200 L ${1010 + flagWave},210 L ${990 + flagWave / 2},230 L 960,222 Z`} fill={C.red} />
    </g>
  );
};

const ForeignOfficeFacade: React.FC<{ frame: number }> = ({ frame }) => {
  const flicker = (i: number) => 0.6 + Math.abs(Math.sin(frame * 0.25 + i)) * 0.4;
  return (
    <g>
      <rect x={400} y={480} width={1120} height={460} fill="#10182a" stroke={C.gold} strokeWidth={2} />
      {/* Pediment */}
      <polygon points="380,480 1540,480 1460,400 460,400" fill="#162236" stroke={C.gold} strokeWidth={2} />
      {/* Columns (taller, more) */}
      {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => (
        <g key={i}>
          <rect x={430 + i * 110} y={530} width={28} height={400} fill="#1c2942" />
          <rect x={426 + i * 110} y={524} width={36} height={10} fill={C.gold} opacity={0.5} />
          <rect x={426 + i * 110} y={926} width={36} height={10} fill={C.gold} opacity={0.5} />
        </g>
      ))}
      {/* Lit windows between columns */}
      {[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => (
        <rect key={i} x={478 + i * 110} y={680} width={56} height={88} fill={C.gold} opacity={flicker(i) * 0.55} />
      ))}
      <polygon points="380,940 1540,940 1480,970 440,970" fill="#0c1626" />
    </g>
  );
};

const PalaceFlag: React.FC<{ frame: number }> = ({ frame }) => {
  const wave = Math.sin(frame * 0.22) * 14;
  const insigniaPulse = 1 + Math.sin(frame * 0.18) * 0.08;
  return (
    <g>
      {/* Palace facade */}
      <rect x={280} y={500} width={1360} height={440} fill="#0e1626" stroke={C.gold} strokeWidth={2} />
      {/* Crenelations */}
      {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(i => (
        <rect key={i} x={290 + i * 113} y={480} width={70} height={26} fill="#0e1626" stroke={C.gold} strokeWidth={1.5} />
      ))}
      {/* Central tower */}
      <rect x={840} y={340} width={240} height={180} fill="#10182a" stroke={C.gold} strokeWidth={2} />
      {/* Crown tower top */}
      <polygon points="840,340 960,260 1080,340" fill="#10182a" stroke={C.gold} strokeWidth={2} />
      {/* Tall flagpole */}
      <line x1={960} y1={260} x2={960} y2={150} stroke={C.gold} strokeWidth={3} />
      {/* King's flag with crown insignia */}
      <path d={`M 960,150 L ${1090 + wave},170 L ${1060 + wave / 2},230 L 960,210 Z`} fill={C.red} stroke="#7a1414" strokeWidth={1.5} />
      {/* Crown insignia */}
      <g transform={`translate(${1015 + wave / 2},190) scale(${insigniaPulse})`}>
        <polygon points="-12,4 -8,-10 -4,-2 0,-12 4,-2 8,-10 12,4" fill={C.gold} />
        <rect x={-12} y={4} width={24} height={4} fill={C.gold} />
      </g>
      {/* Lit lower windows */}
      {[0, 1, 2, 3, 4, 5, 6].map(i => (
        <rect key={i} x={350 + i * 180} y={660} width={70} height={120} fill={C.gold} opacity={0.45} />
      ))}
      <polygon points="280,940 1640,940 1580,970 340,970" fill="#0c1626" />
    </g>
  );
};

const V07_LondonArrival: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera tilt down slightly
  const camY = interpolate(lp, [0, 1], [-30, 0], { easing: ease });
  // Couriers galloping in from right, slowing
  const cx = interpolate(lp, [0, 1], [2100, 800], { easing: easeOut });
  const slump = Math.sin(lf * 0.15) * 2;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="londonSky" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0a1424" />
          <stop offset="55%" stopColor="#16223c" />
          <stop offset="85%" stopColor="#3a2616" />
          <stop offset="100%" stopColor="#84502a" />
        </linearGradient>
        <radialGradient id="londonHaze" cx="50%" cy="92%" r="60%">
          <stop offset="0%" stopColor="#ffaa50" stopOpacity={0.55} />
          <stop offset="50%" stopColor="#c87838" stopOpacity={0.3} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#londonSky)" />
      <ellipse cx={960} cy={780} rx={1300} ry={380} fill="url(#londonHaze)" />
      {/* London skyline */}
      <g transform={`translate(0,${camY})`}>
        <path d="M 0,720 L 80,720 L 80,640 L 140,640 L 140,690 L 240,690 L 240,560 L 280,560 L 280,540 L 320,540 L 320,560 L 360,560 L 360,690 L 440,690 L 440,720 L 540,720 L 540,580 L 600,580 L 600,500 L 620,500 L 620,470 L 660,470 L 660,500 L 680,500 L 680,580 L 740,580 L 740,720 L 860,720 L 860,640 L 920,640 L 920,520 L 960,520 L 960,420 L 1000,420 L 1000,520 L 1040,520 L 1040,640 L 1140,640 L 1140,720 L 1260,720 L 1260,600 L 1320,600 L 1320,720 L 1440,720 L 1440,560 L 1480,560 L 1480,540 L 1520,540 L 1520,560 L 1560,560 L 1560,720 L 1700,720 L 1700,650 L 1780,650 L 1780,720 L 1920,720 L 1920,1080 L 0,1080 Z" fill="#020610" />
        {/* St Paul's dome highlight */}
        <ellipse cx={980} cy={490} rx={50} ry={32} fill="#020610" stroke={C.gold} strokeWidth={1.5} opacity={0.6} />
        {/* Lit windows */}
        {Array.from({ length: 60 }).map((_, i) => {
          const x = 60 + (i * 31) % 1860;
          const y = 580 + ((i * 73) % 130);
          const op = 0.5 + Math.abs(Math.sin(lf * 0.2 + i)) * 0.5;
          return <rect key={i} x={x} y={y} width={5} height={9} fill={C.gold} opacity={op} />;
        })}
      </g>
      {/* Cobblestone road in foreground */}
      <rect x={0} y={930} width={1920} height={150} fill="#040810" />
      <line x1={0} y1={930} x2={1920} y2={930} stroke={C.goldDim} strokeWidth={1} opacity={0.4} />
      {/* Couriers on the road — bigger */}
      <HorseRider x={cx} y={970 + slump} scale={1.6} phase={lf * 0.4} color="#02030a" />
      <HorseRider x={cx + 180} y={985 + slump} scale={1.4} phase={lf * 0.4 + 1.5} color="#02030a" />
      {/* Horse breath mist */}
      {Array.from({ length: 8 }).map((_, i) => {
        const mistX = cx + 80 + ((lf - i * 5) * 1.2);
        const mistY = 920 - ((lf + i * 4) % 30);
        const op = Math.max(0, 0.6 - ((lf + i * 4) % 30) / 30);
        return <circle key={i} cx={mistX} cy={mistY} r={8 + (i % 3) * 3} fill={C.text} opacity={op * 0.35} />;
      })}
      {/* Papers in courier hand */}
      <rect x={cx - 14} y={930 + slump} width={28} height={20} fill={C.text} transform={`rotate(${Math.sin(lf * 0.2) * 6} ${cx} ${940})`} />
      <DustMotes frame={lf} count={18} spread={[0, 200, 1920, 800]} />
    </svg>
  );
};

const V08_Belgium: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Camera zooms in slightly on Belgium
  const zoom = interpolate(lp, [0, 1], [0.95, 1.08], { easing: ease });
  // Dotted line: Brussels → English coast
  const dotProgress = interpolate(lp, [0.2, 0.95], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const dots = 18;
  // Antique map color palette
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <pattern id="seaPattern" x={0} y={0} width={40} height={40} patternUnits="userSpaceOnUse">
          <rect width={40} height={40} fill="#0a1424" />
          <path d="M 0,20 Q 10,15 20,20 T 40,20" stroke="#1a2640" strokeWidth={1} fill="none" opacity={0.6} />
        </pattern>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#seaPattern)" />
      {/* Compass rose top right */}
      <g transform="translate(1700,180) scale(0.9)" opacity={0.55}>
        <circle cx={0} cy={0} r={70} fill="none" stroke={C.gold} strokeWidth={1.5} />
        <circle cx={0} cy={0} r={50} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.6} />
        <polygon points="0,-65 8,-12 0,-22 -8,-12" fill={C.gold} />
        <polygon points="0,65 8,12 0,22 -8,12" fill={C.goldDim} opacity={0.7} />
        <polygon points="-65,0 -12,8 -22,0 -12,-8" fill={C.goldDim} opacity={0.7} />
        <polygon points="65,0 12,8 22,0 12,-8" fill={C.goldDim} opacity={0.7} />
        <text x={0} y={-78} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={14} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">N</text>
      </g>
      <g transform={`translate(${960 - 960 * zoom},${540 - 540 * zoom}) scale(${zoom})`}>
        {/* Larger landmasses for context — England (top-left), Continental Europe (right) */}
        {/* England */}
        <path d="M 200,260 L 320,240 L 480,250 L 580,280 L 660,330 L 720,400 L 740,470 L 720,540 L 680,580 L 600,570 L 520,540 L 460,500 L 380,510 L 300,490 L 240,440 L 200,390 L 180,330 Z" fill="#221608" stroke={C.gold} strokeWidth={1.5} opacity={0.85} />
        <text x={460} y={420} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={26} fontStyle="italic" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill" opacity={0.85}>ENGLAND</text>
        {/* London marker */}
        <circle cx={620} cy={520} r={5} fill={C.text} />
        <text x={620} y={550} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontSize={14} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">London</text>
        {/* France */}
        <path d="M 680,640 L 820,610 L 960,630 L 1080,680 L 1140,750 L 1120,840 L 1040,900 L 920,920 L 800,900 L 720,860 L 680,800 L 660,720 Z" fill="#1a1208" stroke={C.goldDim} strokeWidth={1.5} opacity={0.75} />
        <text x={900} y={790} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontSize={20} fontStyle="italic" opacity={0.7} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">FRANCE</text>
        {/* Netherlands stub */}
        <path d="M 1100,500 L 1200,480 L 1280,500 L 1290,560 L 1240,600 L 1180,610 L 1130,580 L 1110,540 Z" fill="#1a1208" stroke={C.goldDim} strokeWidth={1.5} opacity={0.7} />
        {/* Germany stub right */}
        <path d="M 1290,560 L 1380,540 L 1500,560 L 1620,600 L 1700,650 L 1700,780 L 1620,830 L 1500,820 L 1380,790 L 1300,750 L 1280,680 Z" fill="#1a1208" stroke={C.goldDim} strokeWidth={1.5} opacity={0.7} />
        {/* Belgium — highlighted */}
        <path d="M 1090,610 L 1180,610 L 1240,650 L 1290,700 L 1280,760 L 1220,790 L 1140,790 L 1080,760 L 1040,720 L 1050,660 Z" fill="#3a2c14" stroke={C.gold} strokeWidth={3.5} />
        <text x={1170} y={720} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={28} stroke="#000" strokeWidth={2} paintOrder="stroke fill" letterSpacing="2">BELGIUM</text>
        {/* Brussels marker */}
        <circle cx={1170} cy={690} r={6} fill={C.red} />
        <circle cx={1170} cy={690} r={11} fill="none" stroke={C.red} strokeWidth={2} opacity={0.6 + Math.sin(lf * 0.18) * 0.4} />
        <text x={1170} y={760} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={18} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">Brussels</text>
        {/* Dotted route Brussels → English coast */}
        {Array.from({ length: dots }).map((_, i) => {
          const t = i / (dots - 1);
          const reveal = dotProgress * dots;
          if (i > reveal) return null;
          // Curve from (1170, 690) → (700, 540)
          const x = 1170 + (700 - 1170) * t;
          const y = 690 + (540 - 690) * t - Math.sin(t * Math.PI) * 80;
          return <circle key={i} cx={x} cy={y} r={5} fill={C.gold} opacity={0.95} />;
        })}
        {/* Coast marker on English side */}
        {dotProgress > 0.95 && (
          <g>
            <circle cx={700} cy={540} r={8} fill={C.red} />
            <circle cx={700} cy={540} r={14} fill="none" stroke={C.red} strokeWidth={2} opacity={0.5} />
            <text x={700} y={585} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontSize={16} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">to England</text>
          </g>
        )}
      </g>
      <DustMotes frame={lf} count={16} spread={[0, 100, 1920, 1000]} />
    </svg>
  );
};

const V09_ExchangeExterior: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Building rises from below
  const bldgY = interpolate(lp, [0, 0.3], [60, 0], { extrapolateRight: "clamp", easing: easeOut });
  // Lit window pulses
  const winPulse = 0.6 + Math.abs(Math.sin(lf * 0.14)) * 0.4;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <radialGradient id="exchangeGlow" cx="50%" cy="60%" r="60%">
          <stop offset="0%" stopColor="#1a2438" stopOpacity={0.5} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
        <linearGradient id="exchShaft" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
          <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#exchangeGlow)" />
      {/* Subtle vertical shaft of light through pediment */}
      <polygon points="900,0 1020,0 1080,1080 840,1080" fill="url(#exchShaft)" />
      <g transform={`translate(0,${bldgY})`}>
        {/* Stock Exchange — Greek revival */}
        <rect x={460} y={520} width={1000} height={420} fill="#0e1626" stroke={C.gold} strokeWidth={2} />
        {/* Pediment */}
        <polygon points="440,520 1480,520 1380,400 540,400" fill="#10182a" stroke={C.gold} strokeWidth={2} />
        {/* Pediment medallion — circular ornament */}
        <circle cx={960} cy={470} r={32} fill={C.gold} opacity={0.45 * winPulse} />
        <circle cx={960} cy={470} r={32} fill="none" stroke={C.gold} strokeWidth={2.5} />
        <circle cx={960} cy={470} r={18} fill="none" stroke={C.gold} strokeWidth={1.5} opacity={0.6} />
        {/* Pediment relief lines */}
        <line x1={580} y1={500} x2={920} y2={500} stroke={C.goldDim} strokeWidth={1.5} opacity={0.55} />
        <line x1={1000} y1={500} x2={1340} y2={500} stroke={C.goldDim} strokeWidth={1.5} opacity={0.55} />
        {/* Columns */}
        {[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => (
          <g key={i}>
            <rect x={490 + i * 110} y={560} width={28} height={380} fill="#1c2942" />
            {/* Vertical fluting */}
            <line x1={500 + i * 110} y1={560} x2={500 + i * 110} y2={940} stroke="#0e1626" strokeWidth={1.5} />
            <line x1={510 + i * 110} y1={560} x2={510 + i * 110} y2={940} stroke="#0e1626" strokeWidth={1.5} />
            <rect x={486 + i * 110} y={552} width={36} height={10} fill={C.gold} opacity={0.5} />
            <rect x={486 + i * 110} y={930} width={36} height={10} fill={C.gold} opacity={0.5} />
          </g>
        ))}
        {/* Inter-column windows, dim */}
        {[0, 1, 2, 3, 4, 5, 6, 7].map(i => (
          <rect key={i} x={528 + i * 110} y={700} width={68} height={92} fill="#1a2640" opacity={0.6} stroke={C.goldDim} strokeWidth={1} />
        ))}
        {/* The single lit window — focal point */}
        <rect x={638} y={700} width={68} height={92} fill={C.gold} opacity={winPulse} />
        <rect x={638} y={700} width={68} height={92} fill="none" stroke={C.gold} strokeWidth={2.5} />
        {/* Window cross */}
        <line x1={672} y1={700} x2={672} y2={792} stroke={C.bg} strokeWidth={2} opacity={0.7} />
        <line x1={638} y1={746} x2={706} y2={746} stroke={C.bg} strokeWidth={2} opacity={0.7} />
        {/* Steps */}
        <polygon points="440,940 1480,940 1420,985 500,985" fill="#0c1626" />
        <line x1={440} y1={948} x2={1480} y2={948} stroke={C.gold} strokeWidth={1} opacity={0.4} />
        <line x1={460} y1={965} x2={1460} y2={965} stroke={C.gold} strokeWidth={1} opacity={0.3} />
      </g>
      {/* Glow halo around the lit window */}
      <circle cx={672} cy={746 + bldgY} r={70} fill={C.gold} opacity={0.18 * winPulse} />
      {/* Rain streaks */}
      {Array.from({ length: 80 }).map((_, i) => {
        const seed = i * 91.7;
        const x = (seed * 17) % 1920;
        const y = ((lf * 18 + seed * 23) % 1080);
        return <line key={i} x1={x} y1={y} x2={x - 5} y2={y + 26} stroke={C.text} strokeWidth={1.2} opacity={0.22} />;
      })}
      <DustMotes frame={lf} count={14} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

const V10_NathanWindow: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Push in: scale + translate (less aggressive so room is readable)
  const zoom = interpolate(lp, [0, 1], [1.0, 1.9], { easing: ease });
  const camX = interpolate(lp, [0, 1], [0, -120], { easing: ease });
  const camY = interpolate(lp, [0, 1], [0, -80], { easing: ease });
  const minuteAngle = (lf * 8) % 360;
  const flashOp = interpolate(lf, [50, 70, 90], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <g transform={`translate(${960 + camX},${540 + camY}) scale(${zoom}) translate(-960,-540)`}>
        {/* Outer wall darkening around window */}
        <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
        {/* Window frame (gold) */}
        <rect x={620} y={300} width={680} height={620} fill={C.goldDim} />
        <rect x={640} y={320} width={640} height={580} fill="#162236" stroke={C.gold} strokeWidth={4} />
        {/* Inner room glow — warm candlelight */}
        <radialGradient id="roomGlow">
          <stop offset="0%" stopColor="#c8893a" stopOpacity={0.55} />
          <stop offset="100%" stopColor="#162236" stopOpacity={0} />
        </radialGradient>
        <rect x={640} y={320} width={640} height={580} fill="url(#roomGlow)" />
        {/* Window cross */}
        <line x1={960} y1={320} x2={960} y2={900} stroke={C.gold} strokeWidth={3} />
        <line x1={640} y1={610} x2={1280} y2={610} stroke={C.gold} strokeWidth={3} />
        {/* Desk — wide */}
        <rect x={680} y={780} width={560} height={50} fill="#3a2a14" />
        <rect x={680} y={830} width={560} height={20} fill="#1c1408" />
        {/* Inkwell on desk */}
        <rect x={1140} y={760} width={26} height={28} fill="#0a0a0a" />
        <rect x={1136} y={758} width={34} height={6} fill={C.gold} />
        {/* Candle on desk */}
        <rect x={730} y={732} width={12} height={48} fill={C.text} />
        <ellipse cx={736} cy={720} rx={6} ry={14} fill="#ffaa30" opacity={0.9 + Math.sin(lf * 0.6) * 0.1} />
        <circle cx={736} cy={715} r={3} fill="#ffe080" />
        {/* Candle aura */}
        <circle cx={736} cy={720} r={50} fill="#ffaa30" opacity={0.18} />
        {/* Nathan — figure with detail */}
        {/* Body (coat) */}
        <path d="M 850,700 L 920,650 L 1000,650 L 1070,700 L 1080,820 L 840,820 Z" fill="#0a0c14" stroke={C.gold} strokeWidth={1.5} />
        {/* Lapels */}
        <path d="M 920,650 L 935,720 L 960,710 L 985,720 L 1000,650 Z" fill="#080a10" />
        {/* Head */}
        <ellipse cx={960} cy={620} rx={36} ry={42} fill="#1a1408" />
        {/* Top hat */}
        <rect x={925} y={530} width={70} height={70} fill="#080a10" />
        <ellipse cx={960} cy={602} rx={48} ry={8} fill="#080a10" />
        <rect x={920} y={596} width={80} height={6} fill="#080a10" />
        {/* Letter in hand */}
        <rect x={918} y={730} width={84} height={56} fill={C.text} stroke="#3a2c14" strokeWidth={1.5} />
        {/* Wax seal on letter */}
        <circle cx={994} cy={758} r={6} fill={C.red} />
        {/* Hand */}
        <ellipse cx={912} cy={748} rx={10} ry={8} fill="#1a1408" />
        <ellipse cx={1008} cy={768} rx={10} ry={8} fill="#1a1408" />
      </g>
      {/* Clock face overlay top right */}
      <g transform={`translate(${1660 + Math.sin(lf * 0.05) * 3},${180})`}>
        <circle cx={0} cy={0} r={90} fill={C.bg} stroke={C.gold} strokeWidth={3} />
        <circle cx={0} cy={0} r={84} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.5} />
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2;
          const x1 = Math.cos(a) * 76;
          const y1 = Math.sin(a) * 76;
          const x2 = Math.cos(a) * 88;
          const y2 = Math.sin(a) * 88;
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={C.gold} strokeWidth={i % 3 === 0 ? 3 : 1.5} />;
        })}
        <line x1={0} y1={0}
          x2={Math.cos((minuteAngle - 90) * Math.PI / 180) * 70}
          y2={Math.sin((minuteAngle - 90) * Math.PI / 180) * 70}
          stroke={C.text} strokeWidth={3} strokeLinecap="round" />
        <line x1={0} y1={0}
          x2={Math.cos((minuteAngle / 12 - 90) * Math.PI / 180) * 50}
          y2={Math.sin((minuteAngle / 12 - 90) * Math.PI / 180) * 50}
          stroke={C.text} strokeWidth={5} strokeLinecap="round" />
        <circle cx={0} cy={0} r={6} fill={C.gold} />
      </g>
      {/* British Empire flash */}
      <g opacity={flashOp}>
        <rect x={460} y={920} width={1000} height={84} fill="rgba(8,12,22,0.94)" stroke={C.gold} strokeWidth={2} />
        <text x={960} y={970} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontWeight={700} fontSize={40} letterSpacing="8" stroke="#000" strokeWidth={2} paintOrder="stroke fill">THE BRITISH EMPIRE</text>
      </g>
      <DustMotes frame={lf} count={12} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

const V11_NameCard: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  const zoom = interpolate(lp, [0, 1], [1, 1.04], { easing: ease });
  // Name reveal: clip-path from center outward (full width visible at end)
  const reveal = interpolate(lp, [0.1, 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="nameShaft" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
          <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
        </linearGradient>
        <radialGradient id="nameRoomGlow" cx="50%" cy="40%" r="50%">
          <stop offset="0%" stopColor="#3a2a14" stopOpacity={0.6} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
        <clipPath id="nameClip11">
          <rect x={960 - 720 * reveal} y={770} width={1440 * reveal} height={120} />
        </clipPath>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#nameRoomGlow)" />
      <polygon points="800,0 1120,0 1180,1080 740,1080" fill="url(#nameShaft)" />
      <g transform={`translate(${960},${440}) scale(${zoom}) translate(-960,-440)`}>
        {/* Nathan as a filled silhouette */}
        {/* Coat */}
        <path d="M 800,560 L 880,490 L 1040,490 L 1120,560 L 1140,840 L 780,840 Z" fill="#0a0c14" stroke={C.gold} strokeWidth={2} />
        {/* Lapel detail */}
        <path d="M 880,490 L 905,580 L 960,560 L 1015,580 L 1040,490 Z" fill="#06080f" />
        {/* Head */}
        <ellipse cx={960} cy={440} rx={50} ry={62} fill="#120c06" />
        {/* Top hat */}
        <rect x={912} y={300} width={96} height={100} fill="#04050a" />
        <ellipse cx={960} cy={398} rx={70} ry={10} fill="#04050a" />
        <rect x={898} y={392} width={124} height={10} fill="#04050a" />
        {/* Hat band */}
        <rect x={912} y={380} width={96} height={6} fill={C.gold} opacity={0.55} />
        {/* Subtle face highlight */}
        <ellipse cx={952} cy={430} rx={6} ry={3} fill={C.gold} opacity={0.5} />
      </g>
      {/* Name card */}
      <g>
        <rect x={240} y={770} width={1440} height={120} fill="rgba(8,12,22,0.96)" stroke={C.gold} strokeWidth={3} />
        <rect x={252} y={782} width={1416} height={96} fill="none" stroke={C.gold} strokeWidth={1} opacity={0.4} />
        <g clipPath="url(#nameClip11)">
          <text
            x={960} y={846} textAnchor="middle"
            fill={C.text} fontFamily="Georgia, serif" fontWeight={700} fontSize={56} letterSpacing="6"
            stroke="#000" strokeWidth={2} paintOrder="stroke fill"
          >
            NATHAN MAYER ROTHSCHILD
          </text>
        </g>
      </g>
      {/* Subtitle */}
      <text x={960} y={950} textAnchor="middle" fill={C.gold} fontFamily="Georgia, serif" fontStyle="italic" fontSize={26} letterSpacing="3" stroke="#000" strokeWidth={1.5} paintOrder="stroke fill" opacity={interpolate(lp, [0.5, 0.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
        London, June 19, 1815
      </text>
      <DustMotes frame={lf} count={14} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

const V12_SunArcCoins: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Sun arcs morning to dusk
  const sunT = lp;
  const sunX = interpolate(sunT, [0, 1], [200, 1720]);
  const sunY = 320 - Math.sin(sunT * Math.PI) * 200;
  const coins = 22;
  const coinReveal = interpolate(lp, [0.15, 1], [0, coins], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  // Phase-based sky color: morning blue -> midday gold -> dusk crimson
  const sR = Math.round(interpolate(sunT, [0, 0.5, 1], [0x16, 0x88, 0xc8]));
  const sG = Math.round(interpolate(sunT, [0, 0.5, 1], [0x22, 0x42, 0x44]));
  const sB = Math.round(interpolate(sunT, [0, 0.5, 1], [0x36, 0x18, 0x18]));
  const horizon = `rgb(${sR},${sG},${sB})`;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="sunsky" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#04060e" />
          <stop offset="55%" stopColor="#10182a" />
          <stop offset="90%" stopColor={horizon} />
          <stop offset="100%" stopColor={horizon} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill="url(#sunsky)" />
      {/* Sun trail */}
      {Array.from({ length: 24 }).map((_, i) => {
        const t = i / 23;
        if (t > sunT) return null;
        const x = interpolate(t, [0, 1], [200, 1720]);
        const y = 320 - Math.sin(t * Math.PI) * 200;
        return <circle key={i} cx={x} cy={y} r={6} fill={C.gold} opacity={0.18 + t * 0.18} />;
      })}
      {/* Sun (bigger) */}
      <circle cx={sunX} cy={sunY} r={75} fill={C.gold} opacity={0.45} />
      <circle cx={sunX} cy={sunY} r={50} fill="#ffd080" />
      <circle cx={sunX} cy={sunY} r={32} fill="#fff0c0" />
      {/* Horizon line */}
      <line x1={0} y1={780} x2={1920} y2={780} stroke={C.gold} strokeWidth={1.5} opacity={0.45} />
      <rect x={0} y={780} width={1920} height={300} fill="#040810" />
      {/* Nathan silhouette (LARGER, lower-left third) */}
      <g transform="translate(420,540)">
        {/* Coat */}
        <path d="M -80,160 L -50,80 L 50,80 L 80,160 L 88,420 L -88,420 Z" fill="#02030a" stroke={C.gold} strokeWidth={2} />
        {/* Lapel */}
        <path d="M -50,80 L -28,180 L 0,160 L 28,180 L 50,80 Z" fill="#000" />
        {/* Head */}
        <ellipse cx={0} cy={40} rx={40} ry={50} fill="#02030a" stroke={C.gold} strokeWidth={1.5} />
        {/* Hat */}
        <rect x={-38} y={-80} width={76} height={80} fill="#000" />
        <ellipse cx={0} cy={2} rx={56} ry={8} fill="#000" />
        <rect x={-50} y={-2} width={100} height={8} fill="#000" />
        <rect x={-38} y={-12} width={76} height={5} fill={C.gold} opacity={0.6} />
        {/* Subtle face highlight from sun */}
        <ellipse cx={-12} cy={30} rx={5} ry={3} fill={C.gold} opacity={0.45} />
      </g>
      {/* Coin stack on the right (LARGER) */}
      <g>
        {Array.from({ length: coins }).map((_, i) => {
          if (i > coinReveal) return null;
          const yBase = 1020 - i * 32;
          const wob = Math.sin(lf * 0.1 + i) * 1.5;
          return (
            <g key={i} transform={`translate(${1480 + wob},${yBase})`}>
              <ellipse cx={0} cy={6} rx={120} ry={14} fill="#5a4612" />
              <ellipse cx={0} cy={0} rx={120} ry={20} fill={C.gold} stroke="#3a2a08" strokeWidth={2} />
              <ellipse cx={0} cy={-3} rx={90} ry={9} fill="#ffe0a0" opacity={0.45} />
              {i === Math.floor(coinReveal) && (
                <ellipse cx={0} cy={0} rx={120} ry={20} fill="none" stroke={C.gold} strokeWidth={2} opacity={0.6} />
              )}
            </g>
          );
        })}
      </g>
      <DustMotes frame={lf} count={22} spread={[0, 200, 1920, 800]} />
    </svg>
  );
};

const V13_CalendarBack: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Year decreases 1815 -> 1795
  const yearProg = interpolate(lp, [0, 1], [1815, 1795], { easing: ease });
  const year = Math.round(yearProg);
  const subtitle = year >= 1813 ? "London" : year >= 1808 ? "the road back" : year >= 1800 ? "the long return" : "Frankfurt";
  // Page tear sheets flip from right to left in sequence
  const pageCount = 8;
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="calShaft" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
          <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
        </linearGradient>
        <radialGradient id="calRoom" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="#1a2438" stopOpacity={0.7} />
          <stop offset="100%" stopColor={C.bg} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <rect x={0} y={0} width={1920} height={1080} fill="url(#calRoom)" />
      <polygon points="800,0 1120,0 1180,1080 740,1080" fill="url(#calShaft)" />
      {/* Calendar frame */}
      <g transform="translate(960,540)">
        {/* Hanging hook above */}
        <line x1={0} y1={-280} x2={0} y2={-240} stroke={C.gold} strokeWidth={3} />
        <circle cx={0} cy={-280} r={5} fill={C.gold} />
        {/* Calendar body */}
        <rect x={-340} y={-240} width={680} height={500} fill="#1a1a1a" stroke={C.gold} strokeWidth={4} />
        {/* Header bar */}
        <rect x={-340} y={-240} width={680} height={70} fill={C.gold} />
        <text x={0} y={-192} textAnchor="middle" fill={C.bg} fontFamily="Georgia, serif" fontWeight={700} fontSize={36} letterSpacing="6">CALENDAR</text>
        {/* Inner cream paper */}
        <rect x={-318} y={-160} width={636} height={400} fill="#f0e0c0" />
        {/* Hole punches */}
        <circle cx={-280} cy={-130} r={8} fill="#1a1a1a" />
        <circle cx={280} cy={-130} r={8} fill="#1a1a1a" />
        {/* Year display */}
        <text x={0} y={50} textAnchor="middle" fill="#3a2a14" fontFamily="Georgia, serif" fontWeight={700} fontSize={180} letterSpacing="10">
          {year}
        </text>
        <line x1={-260} y1={100} x2={260} y2={100} stroke="#3a2a14" strokeWidth={2} opacity={0.6} />
        <text x={0} y={170} textAnchor="middle" fill="#3a2a14" fontFamily="Georgia, serif" fontStyle="italic" fontSize={36}>
          {subtitle}
        </text>
        {/* Decorative corners */}
        <path d="M -310,-150 L -290,-150 L -310,-130 Z" fill="#3a2a14" opacity={0.6} />
        <path d="M 310,-150 L 290,-150 L 310,-130 Z" fill="#3a2a14" opacity={0.6} />
        <path d="M -310,230 L -290,230 L -310,210 Z" fill="#3a2a14" opacity={0.6} />
        <path d="M 310,230 L 290,230 L 310,210 Z" fill="#3a2a14" opacity={0.6} />
      </g>
      {/* Pages tearing off (flip from right edge) */}
      {Array.from({ length: pageCount }).map((_, i) => {
        const startT = (i / pageCount) * 0.85;
        const flipDur = 0.18;
        const t = (lp - startT) / flipDur;
        if (t < 0 || t > 1) return null;
        // Page rotates around its left hinge (x=0 in local), so we transform around (640,540)
        const angle = interpolate(t, [0, 1], [0, -160]);
        const liftY = Math.sin(t * Math.PI) * -40;
        return (
          <g key={i} transform={`translate(640,${540 + liftY}) rotate(${angle}) translate(0,0)`}>
            <rect x={0} y={-160} width={320} height={400} fill="#f0e0c0" stroke="#3a2a14" strokeWidth={1.5} />
            <rect x={0} y={-160} width={320} height={6} fill="#3a2a14" opacity={0.6} />
            <text x={160} y={70} textAnchor="middle" fill="#3a2a14" fontFamily="Georgia, serif" fontWeight={700} fontSize={140}>{1815 - i}</text>
            {/* Edge shadow */}
            <line x1={0} y1={-160} x2={0} y2={240} stroke="#1a1208" strokeWidth={3} />
          </g>
        );
      })}
      <DustMotes frame={lf} count={14} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

const V14_ArrowsInfoCoin: React.FC<{ frame: number; v: V }> = ({ frame, v }) => {
  const lf = localFrame(frame, v);
  const lp = localProgress(frame, v);
  // Stage windows
  const unfoldP = interpolate(lp, [0, 0.35], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const letterFade = interpolate(lp, [0.32, 0.45], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const arrowP = interpolate(lp, [0.32, 0.65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const arrowFade = interpolate(lp, [0.62, 0.74], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const coinP = interpolate(lp, [0.62, 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  return (
    <svg viewBox="0 0 1920 1080" width="1920" height="1080">
      <defs>
        <linearGradient id="v14Shaft" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor={C.gold} stopOpacity={0.18} />
          <stop offset="100%" stopColor={C.gold} stopOpacity={0} />
        </linearGradient>
      </defs>
      <rect x={0} y={0} width={1920} height={1080} fill={C.bg} />
      <polygon points="800,0 1120,0 1180,1080 740,1080" fill="url(#v14Shaft)" />
      {/* Stage A: letter unfolds, alley peek inside */}
      <g opacity={letterFade}>
        <g transform={`translate(960,540) scale(${1 + unfoldP * 0.6})`}>
          {/* Outer envelope shadow */}
          <rect x={-265} y={-175} width={530} height={350} fill="#3a2a14" opacity={0.3} transform="translate(8,8)" />
          {/* Cream paper background */}
          <rect x={-260} y={-170} width={520} height={340} fill={C.text} stroke="#3a2a14" strokeWidth={3} />
          {/* Top flap — unfolds upward (visible going up) */}
          <path d={`M -260,-170 L 0,${-170 - unfoldP * 60} L 260,-170 Z`} fill="#e0d2b0" stroke="#3a2a14" strokeWidth={2} />
          {/* Inside content (alley peek revealed) */}
          {unfoldP > 0.4 && (
            <g opacity={(unfoldP - 0.4) / 0.6}>
              {/* Alley scene inside */}
              <rect x={-220} y={-130} width={440} height={260} fill="#0a1224" />
              <rect x={-220} y={-130} width={120} height={260} fill="#162236" />
              <rect x={100} y={-130} width={120} height={260} fill="#162236" />
              {/* Cobblestones */}
              <rect x={-100} y={70} width={200} height={60} fill="#080d18" />
              {[0, 1, 2, 3].map(i => (
                <rect key={i} x={-90 + i * 50} y={80} width={40} height={40} fill="none" stroke="#1a2236" strokeWidth={1} />
              ))}
              {/* Lit window mid-up */}
              <rect x={-30} y={-40} width={60} height={80} fill={C.gold} opacity={0.85} />
              <line x1={0} y1={-40} x2={0} y2={40} stroke="#3a2a14" strokeWidth={2} opacity={0.6} />
              <line x1={-30} y1={0} x2={30} y2={0} stroke="#3a2a14" strokeWidth={2} opacity={0.6} />
              <text x={0} y={120} textAnchor="middle" fill={C.text} fontFamily="Georgia, serif" fontStyle="italic" fontSize={20} stroke="#000" strokeWidth={1.5} paintOrder="stroke fill">Frankfurt, 1795</text>
            </g>
          )}
          {/* Wax seal (still visible at top of flap) */}
          <circle cx={0} cy={-170} r={18} fill={C.red} stroke="#7a1414" strokeWidth={2} />
          <circle cx={0} cy={-170} r={9} fill="#8a1818" />
        </g>
      </g>
      {/* Stage B: arrow splits into 5 (golden) */}
      <g opacity={arrowFade} transform="translate(960,540)">
        {/* Origin glow */}
        <circle cx={0} cy={0} r={20 + arrowP * 50} fill={C.gold} opacity={(1 - arrowP) * 0.6} />
        <circle cx={0} cy={0} r={14} fill={C.gold} />
        {[0, 1, 2, 3, 4].map(i => {
          const angle = -60 + i * 30;
          const r = arrowP * 360;
          const x = Math.cos((angle * Math.PI) / 180) * r;
          const y = Math.sin((angle * Math.PI) / 180) * r;
          return (
            <g key={i} transform={`translate(${x},${y}) rotate(${angle})`}>
              {/* Arrow shaft */}
              <line x1={-80} y1={0} x2={60} y2={0} stroke={C.gold} strokeWidth={10} strokeLinecap="round" />
              {/* Trailing wisp */}
              <line x1={-160} y1={0} x2={-80} y2={0} stroke={C.gold} strokeWidth={4} strokeLinecap="round" opacity={0.4} />
              {/* Arrowhead */}
              <polygon points="60,-18 90,0 60,18" fill={C.gold} stroke="#5a4612" strokeWidth={1.5} />
              {/* Fletching */}
              <polygon points="-80,-10 -90,0 -80,10 -70,0" fill="#5a4612" />
            </g>
          );
        })}
      </g>
      {/* Stage C: coin flips and lands stamped INFORMATION */}
      {coinP > 0 && (() => {
        const flipCycles = 3;
        const flipPhase = (1 - coinP) * Math.PI * 2 * flipCycles;
        const xScale = Math.cos(flipPhase);
        const liftY = Math.sin(coinP * Math.PI) * -120;
        const showBack = xScale < 0;
        return (
          <g opacity={coinP} transform={`translate(960, ${540 + liftY})`}>
            <g transform={`scale(${Math.max(0.05, Math.abs(xScale))}, 1)`}>
              <ellipse cx={0} cy={0} rx={180} ry={180} fill={C.gold} stroke="#5a4612" strokeWidth={5} />
              <circle cx={0} cy={0} r={160} fill="none" stroke="#5a4612" strokeWidth={2.5} opacity={0.7} />
              {!showBack && coinP > 0.55 && (
                <g>
                  <circle cx={0} cy={0} r={155} fill="none" stroke="#3a2c0a" strokeWidth={3} />
                  <circle cx={0} cy={0} r={145} fill="none" stroke="#3a2c0a" strokeWidth={1.5} />
                  <text x={0} y={16} textAnchor="middle" fill="#3a2c0a" fontFamily="Georgia, serif" fontWeight={700} fontSize={36} letterSpacing="6">
                    INFORMATION
                  </text>
                  <text x={0} y={-50} textAnchor="middle" fill="#3a2c0a" fontFamily="Georgia, serif" fontWeight={700} fontSize={18} letterSpacing="4" opacity={0.7}>
                    THE ONLY CURRENCY
                  </text>
                  <text x={0} y={70} textAnchor="middle" fill="#3a2c0a" fontFamily="Georgia, serif" fontStyle="italic" fontSize={16} letterSpacing="2" opacity={0.7}>
                    that does not lose its value
                  </text>
                </g>
              )}
              {showBack && (
                <g>
                  <polygon points="-50,40 0,-70 50,40" fill="#5a4612" opacity={0.5} />
                </g>
              )}
            </g>
          </g>
        );
      })()}
      <DustMotes frame={lf} count={20} spread={[0, 100, 1920, 900]} />
    </svg>
  );
};

// ── Main composition ─────────────────────────────────────────────────────────

export const LetterDynastyHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Render every vignette but mask by opacity. Cross-dissolves overlap.
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <Audio src={staticFile("letter-dynasty-hook.wav")} />
      {VIGNETTES.map((v, i) => {
        const op = vOpacity(frame, v);
        if (op <= 0.001) return null;
        let content: React.ReactNode = null;
        switch (v.name) {
          case "channel-dawn":     content = <V01_ChannelDawn frame={frame} v={v} />; break;
          case "letter-glide":     content = <V02_LetterGlide frame={frame} v={v} />; break;
          case "overtake-courier": content = <V03_OvertakeCourier frame={frame} v={v} />; break;
          case "admiralty":        content = <V_LetterPastBuilding frame={frame} v={v} label="THE ADMIRALTY" building={<AdmiraltyDome frame={frame - v.start * FPS} />} />; break;
          case "foreign-office":   content = <V_LetterPastBuilding frame={frame} v={v} label="THE FOREIGN OFFICE" building={<ForeignOfficeFacade frame={frame - v.start * FPS} />} />; break;
          case "king":             content = <V_LetterPastBuilding frame={frame} v={v} label="THE KING" building={<PalaceFlag frame={frame - v.start * FPS} />} />; break;
          case "couriers-london":  content = <V07_LondonArrival frame={frame} v={v} />; break;
          case "belgium":          content = <V08_Belgium frame={frame} v={v} />; break;
          case "exchange-ext":     content = <V09_ExchangeExterior frame={frame} v={v} />; break;
          case "nathan-window":    content = <V10_NathanWindow frame={frame} v={v} />; break;
          case "name-card":        content = <V11_NameCard frame={frame} v={v} />; break;
          case "sun-arc-coins":    content = <V12_SunArcCoins frame={frame} v={v} />; break;
          case "calendar-back":    content = <V13_CalendarBack frame={frame} v={v} />; break;
          case "arrows-info":      content = <V14_ArrowsInfoCoin frame={frame} v={v} />; break;
        }
        return (
          <AbsoluteFill key={i} style={{ opacity: op }}>
            {content}
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
