/**
 * Stamp — reusable "stamp-down" impact overlay (CLASSIFIED, REDACTED, TOP SECRET, etc.).
 *
 * The stamp drops in from above with overshoot, lands with a tiny rotation
 * jitter, and holds. Replaces the inline stamps that previously lived in
 * DocumentReveal and MidnightMagnatesStyleReel so brand demos and chapters
 * share a single, well-tuned animation.
 *
 * Animation timeline (frames are relative to scene start, not absolute):
 *   0  → impact-6      : invisible, scale 1.6 (held above)
 *   impact-6 → impact  : drops 80px, scale 1.6 → 1.0, rotation snaps
 *   impact → +5        : ±2° rotation jitter (settle)
 *   impact+5 → end-fade: hold
 *   last 12 frames     : optional fade out
 *
 * Pass `impactAtSeconds` to choose when the stamp lands — defaults to 60% of
 * the scene duration so the rest of the scene plays first.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type StampPreset = "classified" | "redacted" | "top_secret" | "approved" | "draft";

export interface StampProps {
  /** Choose a preset OR pass `text` directly. */
  preset?: StampPreset;
  /** Custom text. Overrides `preset`. */
  text?: string;
  /** Stamp color. Defaults to theme.stampRed (or red-fallback). */
  color?: string;

  /** Where on screen the stamp lands. 0–1 normalized to viewport. Default 0.5,0.5. */
  position?: { x: number; y: number };
  /** Final tilt angle in degrees. Default −8. */
  rotationDeg?: number;
  /** Final scale factor. Default 1.0. */
  scale?: number;

  /** When the stamp lands (seconds from scene start). Default 60% of duration. */
  impactAtSeconds?: number;
  /** Total frames the stamp is on screen. Default = remaining scene from impact. */
  durationFrames?: number;
  /** Render a subtle ink-bleed rectangle behind the text. Default true. */
  inkBleed?: boolean;
  /** Fade out at the end. Default false (stamp holds). */
  fadeOutAtEnd?: boolean;

  theme?: Partial<BrandTheme>;
}

const PRESET_TEXT: Record<StampPreset, string> = {
  classified: "CLASSIFIED",
  redacted: "REDACTED",
  top_secret: "TOP SECRET",
  approved: "APPROVED",
  draft: "DRAFT",
};

export const Stamp: React.FC<StampProps> = ({
  preset,
  text,
  color: colorOverride,
  position = { x: 0.5, y: 0.5 },
  rotationDeg = -8,
  scale: finalScale = 1.0,
  impactAtSeconds,
  durationFrames,
  inkBleed = true,
  fadeOutAtEnd = false,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const total = durationFrames ?? durationInFrames;
  const impact =
    impactAtSeconds !== undefined
      ? Math.round(impactAtSeconds * fps)
      : Math.round(total * 0.6);
  const local = frame - impact;

  // Pre-impact: held above the page, invisible.
  if (local < -8) return null;

  // Drop animation — 8 frames before impact, scale 1.6→1.0, drop 80px → 0.
  const dropProgress = interpolate(local, [-8, 0], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dropY = (1 - dropProgress) * -80;
  const dropScale = interpolate(local, [-8, 0], [1.6, finalScale], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dropOpacity = interpolate(local, [-8, -2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Settle jitter — spring-driven rotation wobble for 5 frames after impact.
  const settle = spring({
    frame: Math.max(0, local),
    fps,
    config: { damping: 8, stiffness: 180, mass: 0.6 },
  });
  const jitterDeg = (1 - settle) * 4 * Math.sin(local * 0.9);

  // Optional fade-out at end of scene
  const fadeOut = fadeOutAtEnd
    ? interpolate(frame, [total - 12, total], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  const stampText = text ?? PRESET_TEXT[preset ?? "classified"];
  const stampColor = colorOverride ?? theme.stampRed ?? "#b41e1e";

  const rotation = rotationDeg + jitterDeg;
  const screenX = `${position.x * 100}%`;
  const screenY = `${position.y * 100}%`;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: screenY,
          left: screenX,
          transform: `translate(-50%, calc(-50% + ${dropY}px)) rotate(${rotation}deg) scale(${dropScale})`,
          transformOrigin: "center center",
          opacity: dropOpacity * fadeOut,
        }}
      >
        <div
          style={{
            position: "relative",
            color: stampColor,
            fontFamily: theme.fontMono ?? "Courier New, monospace",
            fontSize: 110,
            fontWeight: 900,
            letterSpacing: "0.16em",
            border: `8px solid ${stampColor}`,
            padding: "16px 36px 12px",
            textShadow: "0 2px 4px rgba(0,0,0,0.3)",
            // Faint inner border to mimic a real stamp die
            boxShadow: `inset 0 0 0 3px ${stampColor}`,
            background: inkBleed ? `${stampColor}1A` : "transparent",
            mixBlendMode: "multiply",
          }}
        >
          {stampText}
        </div>
      </div>
    </AbsoluteFill>
  );
};
