/**
 * FiveArrowsReveal — animated reveal of N arrows fanning out from a central
 * origin point to peripheral capitals (or any set of destinations).
 *
 * Hero motif of the Midnight Magnates "Five Arrows" episode (Rothschild
 * dynasty). Generalizes to any "X branches of an empire" / "X disciples sent
 * abroad" / "X trade routes" pattern across both Sleep Network channels.
 *
 * Visual language (locked to Midnight Magnates per visual-design-quality.md):
 *   - Editorial-magazine + art-deco/geometric + luxury/refined
 *   - Single shaft of light from origin (no competing highlights)
 *   - Brass-gold accent on arrows; cream city labels (never raw white)
 *   - 2px black stroke + drop-shadow on every text element
 *   - Slow noir reveal: scale 0.97 → 1.0, no bounce, Easing.out(cubic)
 *   - Min hold ≥ 4s; default 9s
 *
 * Timeline (relative to scene start):
 *   0      → fadeIn       : opacity 0 → 1, scale 0.97 → 1.0
 *   fadeIn → originReveal : origin pulse + label
 *   per-arrow stagger     : draw arc, then arrowhead, then city label
 *   final fadeFrames      : opacity 1 → 0
 *
 * Coordinates: positions are in 0–1 normalized over the 1920×1080 viewport.
 * Arrows are drawn as quadratic-bezier paths so they curve outward (not
 * straight) which reads as both more elegant AND more "fired".
 *
 * @version 0.1.0
 */
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

// 8-offset stroke + soft drop shadow (channel-mandatory for burned-in text)
const TEXT_STROKE =
  "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000, " +
  "1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000, " +
  "0 4px 14px rgba(0,0,0,0.55)";

// Default 5-Rothschild city positions in 1920×1080 normalized 0–1 space.
// Approximates real geography: Frankfurt (origin), London NW, Paris W,
// Vienna E, Naples SE, plus the 5th option keeps Frankfurt as origin only.
const DEFAULT_CITY_POSITIONS: Record<string, { x: number; y: number }> = {
  Frankfurt: { x: 0.50, y: 0.50 }, // origin (centered)
  London: { x: 0.27, y: 0.30 },
  Paris: { x: 0.32, y: 0.55 },
  Vienna: { x: 0.70, y: 0.45 },
  Naples: { x: 0.65, y: 0.78 },
};

export interface FiveArrowsRevealProps {
  /** Cities the arrows fly to (also used as labels). */
  cities: string[];
  /** Origin label rendered at the centerpoint. Defaults to first city. */
  originLabel?: string;
  /** Optional explicit positions (0–1). Falls back to DEFAULT_CITY_POSITIONS. */
  positions?: Record<string, { x: number; y: number }>;
  /** Pulse the origin marker more strongly. Default true. */
  highlightOrigin?: boolean;
  /** Total scene duration in frames; if omitted uses video config. */
  durationFrames?: number;
  /** Theme override (channel playbook). */
  theme?: Partial<BrandTheme>;
}

const ARROW_COLORS_FALLBACK = ["#c9a84c", "#b89544", "#a78237", "#8c6e23", "#d4b85a"];

export const FiveArrowsReveal: React.FC<FiveArrowsRevealProps> = ({
  cities,
  originLabel,
  positions,
  highlightOrigin = true,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const total = durationFrames ?? durationInFrames;
  const fadeFrames = theme.fadeFrames ?? 36;

  // Resolve origin and destinations
  const posMap = { ...DEFAULT_CITY_POSITIONS, ...(positions ?? {}) };
  const originName = originLabel ?? cities[0];
  const origin = posMap[originName] ?? { x: 0.5, y: 0.5 };
  const destinations = cities
    .filter((c) => c !== originName)
    .map((c) => ({
      name: c,
      pos: posMap[c] ?? { x: 0.5, y: 0.5 },
    }));

  // Per-arrow stagger across the active middle of the scene
  const drawDuration = Math.round(fps * 0.9); // 0.9s draw per arrow
  const labelDelay = Math.round(fps * 0.15);
  const labelDuration = Math.round(fps * 0.5);
  const originRevealStart = fadeFrames;
  const originRevealEnd = originRevealStart + Math.round(fps * 0.5);
  const arrowsBlock = Math.round(fps * 1.2); // each arrow gets a 1.2s slot
  const arrowsStart = originRevealEnd + Math.round(fps * 0.2);
  const fadeOutStart = total - fadeFrames;

  // Container fade + scale-in
  const containerFade = interpolate(
    frame,
    [0, fadeFrames, fadeOutStart, total],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const containerScale = interpolate(
    frame,
    [0, fadeFrames],
    [0.97, 1.0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  // Origin pulse — slow breathing so the eye returns to center.
  const originReveal = interpolate(
    frame,
    [originRevealStart, originRevealEnd],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );
  const pulseStrength = highlightOrigin ? 0.18 : 0.08;
  const pulse = 1 + pulseStrength * Math.sin((frame - originRevealEnd) * 0.06);

  // Helper — convert normalized 0–1 to viewport pixels.
  // We render at 1920×1080 (channel-mandatory minimum).
  const W = 1920;
  const H = 1080;
  const px = (n: number) => n * W;
  const py = (n: number) => n * H;

  // Single shaft of light: a soft radial gradient anchored at origin,
  // rendered behind everything else.
  const shaftFade = interpolate(
    frame,
    [originRevealStart, originRevealEnd + fadeFrames],
    [0, 0.45],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity: containerFade,
        transform: `scale(${containerScale})`,
      }}
    >
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        style={{ position: "absolute", inset: 0 }}
      >
        <defs>
          {/* Single shaft of light from origin */}
          <radialGradient id="originShaft" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={theme.accent} stopOpacity={shaftFade} />
            <stop offset="60%" stopColor={theme.accent} stopOpacity={shaftFade * 0.18} />
            <stop offset="100%" stopColor={theme.accent} stopOpacity={0} />
          </radialGradient>

          {/* Reusable arrowhead marker — referenced by each arc by id. */}
          <marker
            id="arrowhead"
            viewBox="0 0 12 12"
            refX="9"
            refY="6"
            markerWidth="9"
            markerHeight="9"
            orient="auto-start-reverse"
          >
            <path
              d="M0,1 L10,6 L0,11 Z"
              fill={theme.accent}
              stroke={theme.accent}
              strokeWidth={1}
            />
          </marker>
        </defs>

        {/* Light shaft — placed at origin */}
        <circle
          cx={px(origin.x)}
          cy={py(origin.y)}
          r={Math.min(W, H) * 0.46}
          fill="url(#originShaft)"
        />

        {/* Faint Europe outline cue — hand-drawn rectangle vignette, geometric.
            Uses theme muted to suggest a frame without being a real map. */}
        <rect
          x={W * 0.12}
          y={H * 0.16}
          width={W * 0.76}
          height={H * 0.68}
          fill="none"
          stroke={theme.muted}
          strokeWidth={1}
          strokeDasharray="2 8"
          opacity={0.35 * containerFade}
          rx={6}
        />

        {/* Arrows — each one gets its own time slot */}
        {destinations.map((d, i) => {
          const slotStart = arrowsStart + i * arrowsBlock;
          const drawEnd = slotStart + drawDuration;
          const labelStart = drawEnd + labelDelay;
          const labelEnd = labelStart + labelDuration;

          // pathProgress 0→1 controls how much of the arc has drawn
          const pathProgress = interpolate(
            frame,
            [slotStart, drawEnd],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.inOut(Easing.cubic),
            }
          );

          // Compute quadratic bezier from origin to destination with a curved
          // control point. Curve outward (perpendicular to mid-line) by 8% of
          // the line length, alternating sides per arrow for elegant fan.
          const x0 = px(origin.x);
          const y0 = py(origin.y);
          const x1 = px(d.pos.x);
          const y1 = py(d.pos.y);
          const midX = (x0 + x1) / 2;
          const midY = (y0 + y1) / 2;
          const dx = x1 - x0;
          const dy = y1 - y0;
          const len = Math.hypot(dx, dy);
          const perpX = -dy / len;
          const perpY = dx / len;
          const curveAmount = len * 0.12 * (i % 2 === 0 ? 1 : -1);
          const cx = midX + perpX * curveAmount;
          const cy = midY + perpY * curveAmount;

          const pathD = `M ${x0} ${y0} Q ${cx} ${cy} ${x1} ${y1}`;
          const arrowColor = ARROW_COLORS_FALLBACK[i % ARROW_COLORS_FALLBACK.length];

          // We use stroke-dasharray + stroke-dashoffset to draw the arc.
          const pathLen = approxArcLength(x0, y0, cx, cy, x1, y1);
          const dashOffset = (1 - pathProgress) * pathLen;

          // Arrowhead reveal: only show after path is fully drawn
          const arrowOpacity = pathProgress >= 1 ? 1 : 0;

          // Destination dot opacity — appears synchronized with arrow tip
          const dotOpacity = interpolate(
            frame,
            [drawEnd - 4, drawEnd + 6],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          // Label fade in
          const labelOpacity = interpolate(
            frame,
            [labelStart, labelEnd],
            [0, 1],
            {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            }
          );

          // Determine label position — outside the arrow tip, biased toward
          // the destination. Offset based on quadrant relative to origin.
          const dirX = (x1 - x0) >= 0 ? 1 : -1;
          const dirY = (y1 - y0) >= 0 ? 1 : -1;
          const labelX = x1 + dirX * 24;
          const labelY = y1 + dirY * 14;
          const labelAnchor = dirX === 1 ? "start" : "end";

          return (
            <g key={d.name}>
              {/* Arc path */}
              <path
                d={pathD}
                stroke={arrowColor}
                strokeWidth={4}
                fill="none"
                strokeDasharray={pathLen}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                markerEnd={arrowOpacity > 0 ? "url(#arrowhead)" : undefined}
                opacity={containerFade}
              />

              {/* Glow under the path while drawing */}
              <path
                d={pathD}
                stroke={arrowColor}
                strokeWidth={10}
                fill="none"
                strokeDasharray={pathLen}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                opacity={0.18 * containerFade}
                filter="blur(2px)"
              />

              {/* Destination dot */}
              <circle
                cx={x1}
                cy={y1}
                r={9}
                fill={arrowColor}
                opacity={dotOpacity * containerFade}
              />
              <circle
                cx={x1}
                cy={y1}
                r={16}
                fill="none"
                stroke={arrowColor}
                strokeWidth={1.5}
                opacity={dotOpacity * 0.45 * containerFade}
              />

              {/* City label — uses SVG text with paint-order stroke for crisp
                  alpha edges (paint-order works in SVG, unlike HTML text). */}
              <text
                x={labelX}
                y={labelY}
                fill={theme.text}
                fontFamily={theme.fontHeading}
                fontWeight={theme.headingWeight ?? 700}
                fontSize={32}
                letterSpacing="0.06em"
                textAnchor={labelAnchor}
                opacity={labelOpacity * containerFade}
                stroke="#000"
                strokeWidth={2}
                paintOrder="stroke fill"
                style={{
                  // Add the soft drop-shadow on top of the SVG stroke
                  filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.55))",
                }}
              >
                {d.name.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* Origin marker — drawn last so it sits on top */}
        <g
          transform={`translate(${px(origin.x)}, ${py(origin.y)}) scale(${pulse})`}
          opacity={originReveal * containerFade}
        >
          <circle
            r={28}
            fill="none"
            stroke={theme.accent}
            strokeWidth={2}
            opacity={0.45}
          />
          <circle r={14} fill={theme.accent} />
          <circle r={6} fill={theme.bg} />
        </g>
        <text
          x={px(origin.x)}
          y={py(origin.y) + 56}
          fill={theme.text}
          fontFamily={theme.fontHeading}
          fontWeight={theme.headingWeight ?? 700}
          fontSize={28}
          letterSpacing="0.18em"
          textAnchor="middle"
          opacity={originReveal * containerFade}
          stroke="#000"
          strokeWidth={2}
          paintOrder="stroke fill"
          style={{ filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.55))" }}
        >
          {originName.toUpperCase()}
        </text>
      </svg>
    </AbsoluteFill>
  );
};

/** Approximate the arc length of a quadratic bezier (sufficient for stroke-dash). */
function approxArcLength(
  x0: number,
  y0: number,
  cx: number,
  cy: number,
  x1: number,
  y1: number
): number {
  const steps = 16;
  let total = 0;
  let prevX = x0;
  let prevY = y0;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const omt = 1 - t;
    const x = omt * omt * x0 + 2 * omt * t * cx + t * t * x1;
    const y = omt * omt * y0 + 2 * omt * t * cy + t * t * y1;
    total += Math.hypot(x - prevX, y - prevY);
    prevX = x;
    prevY = y;
  }
  return total;
}
