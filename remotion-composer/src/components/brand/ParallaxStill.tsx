/**
 * ParallaxStill — pseudo-3D parallax from 2–3 image layers (CSS, no WebGL).
 *
 * The asset director provides background / midground / foreground layers
 * (typically extracted via subject-removal: original image as bg, subject
 * cutout as fg, optional midground for scene depth). Each layer pans + zooms
 * at a different rate to suggest depth. Honest: this is "fake 3D" — for true
 * depth-mapped parallax we'd need a depth model + WebGL.
 *
 * Common asset prep:
 *   - Use Pexels/Pixabay for the bg image.
 *   - Use rembg (or similar) to extract the subject as an alpha PNG → fg.
 *   - Optional: light particle PNG as midground.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface ParallaxStillProps {
  /** Required — back image (full scene). */
  backgroundSrc: string;
  /** Optional — middle layer (typically thin subject or particle overlay). */
  midgroundSrc?: string;
  /** Optional — foreground (typically subject cutout with alpha). */
  foregroundSrc?: string;
  /** "left", "right", "in", "out" — direction of pseudo-camera move. */
  motion?: "left" | "right" | "in" | "out";
  /** Total frames. Default = 7s @ fps. */
  durationFrames?: number;
  /** Optional caption text overlay. */
  caption?: string;
  theme?: Partial<BrandTheme>;
}

export const ParallaxStill: React.FC<ParallaxStillProps> = ({
  backgroundSrc,
  midgroundSrc,
  foregroundSrc,
  motion = "right",
  durationFrames,
  caption,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 7 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Linear pan progress 0 → 1 across the whole clip (sleep-safe slow drift)
  const t = interpolate(frame, [0, total], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Layer offsets — bg moves least, fg moves most. Direction-dependent.
  const dirX = motion === "left" ? -1 : motion === "right" ? 1 : 0;
  const dirZoom = motion === "in" ? 1 : motion === "out" ? -1 : 0;

  const bgPanX = dirX * t * 30;        // pixels — barely visible
  const mgPanX = dirX * t * 80;
  const fgPanX = dirX * t * 140;

  const bgScale = 1.05 + dirZoom * t * 0.04;
  const mgScale = 1.08 + dirZoom * t * 0.07;
  const fgScale = 1.10 + dirZoom * t * 0.10;

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity, overflow: "hidden" }}>
      {/* Background */}
      <Img
        src={backgroundSrc}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translateX(${bgPanX}px) scale(${bgScale})`,
          filter: "saturate(0.85) brightness(0.85)",
        }}
      />

      {/* Subtle vignette to blend layers */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, transparent 50%, ${theme.bg}AA 100%)`,
          pointerEvents: "none",
        }}
      />

      {/* Midground */}
      {midgroundSrc ? (
        <Img
          src={midgroundSrc}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `translateX(${mgPanX}px) scale(${mgScale})`,
            mixBlendMode: "screen",
          }}
        />
      ) : null}

      {/* Foreground */}
      {foregroundSrc ? (
        <Img
          src={foregroundSrc}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "contain",
            transform: `translateX(${fgPanX}px) scale(${fgScale})`,
          }}
        />
      ) : null}

      {/* Caption */}
      {caption ? (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: theme.fontBody,
            fontStyle: "italic",
            fontSize: 22,
            color: theme.text,
            background: `linear-gradient(to top, ${theme.bg}DD, transparent)`,
            padding: "30px 80px 12px",
            letterSpacing: "0.04em",
          }}
        >
          {caption}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
