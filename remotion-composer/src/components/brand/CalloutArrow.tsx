/**
 * CalloutArrow — infographic-style annotation pointing to a target on a wide shot.
 *
 * Used for "weapon used", "exit path", "hidden door" infographic moments.
 *
 * Renders a curved arrow from a label box to a target point. Multiple
 * callouts can be stacked by composing several CalloutArrow instances.
 *
 * Coordinates are normalized 0–1 across the full screen.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface CalloutArrowProps {
  /** Target point as { x, y } in 0–1 normalized space. */
  target: { x: number; y: number };
  /** Label position as { x, y } in 0–1 normalized space — should be away from target. */
  label: { x: number; y: number };
  /** Title of the callout (e.g., "Weapon used"). */
  title: string;
  /** Optional supporting text under the title. */
  description?: string;
  /** Optional small icon glyph in the label (emoji or unicode). */
  glyph?: string;
  /** Reveal time in seconds — when this callout becomes visible. */
  revealAtSeconds?: number;
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

export const CalloutArrow: React.FC<CalloutArrowProps> = ({
  target,
  label,
  title,
  description,
  glyph,
  revealAtSeconds = 0,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps, width: vw, height: vh } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 5 * fps;
  const startFrame = Math.round(revealAtSeconds * fps);
  const fadeOutStart = total - fadeFrames;

  const localFrame = frame - startFrame;
  if (localFrame < 0) return null;

  const opacity = interpolate(localFrame, [0, 18, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const targetX = target.x * vw;
  const targetY = target.y * vh;
  const labelX = label.x * vw;
  const labelY = label.y * vh;

  // Arrow draw progress
  const drawProgress = interpolate(localFrame, [0, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Pulse on target dot
  const pulse = (Math.sin((localFrame / fps) * Math.PI * 2) + 1) / 2; // 0..1

  // Curved path between label and target
  const midX = (labelX + targetX) / 2;
  const midY = (labelY + targetY) / 2 - 60; // arc upward
  const path = `M ${labelX} ${labelY} Q ${midX} ${midY} ${targetX} ${targetY}`;

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      <svg
        viewBox={`0 0 ${vw} ${vh}`}
        width={vw}
        height={vh}
        style={{ position: "absolute", inset: 0 }}
      >
        {/* Curved path */}
        <path
          d={path}
          fill="none"
          stroke={theme.accent}
          strokeWidth={2.5}
          strokeDasharray="6 6"
          strokeDashoffset={(1 - drawProgress) * 600}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${theme.accent}88)` }}
        />
        {/* Target circle (pulsing) */}
        <circle cx={targetX} cy={targetY} r={8} fill={theme.accent} />
        <circle
          cx={targetX}
          cy={targetY}
          r={14 + pulse * 10}
          fill="none"
          stroke={theme.accent}
          strokeOpacity={1 - pulse}
          strokeWidth={2}
        />
      </svg>

      {/* Label box */}
      <div
        style={{
          position: "absolute",
          left: labelX,
          top: labelY,
          transform: "translate(-50%, -100%)",
          background: theme.bg,
          border: `1px solid ${theme.accent}`,
          borderRadius: 4,
          padding: "12px 16px",
          minWidth: 220,
          maxWidth: 320,
          boxShadow: `0 8px 24px rgba(0,0,0,0.55)`,
          fontFamily: theme.fontBody,
          color: theme.text,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: description ? 6 : 0 }}>
          {glyph ? (
            <div
              style={{
                fontSize: 20,
                color: theme.accent,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 28,
              }}
            >
              {glyph}
            </div>
          ) : null}
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontSize: 18,
              fontWeight: 700,
              color: theme.accent,
              letterSpacing: "0.04em",
              lineHeight: 1.2,
            }}
          >
            {title}
          </div>
        </div>
        {description ? (
          <div
            style={{
              fontSize: 14,
              lineHeight: 1.4,
              color: theme.text,
            }}
          >
            {description}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
