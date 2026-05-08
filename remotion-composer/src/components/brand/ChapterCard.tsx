/**
 * ChapterCard — full-screen chapter divider, 3s default.
 *
 * Channel-themed by default, BUT accepts per-chapter overrides so an
 * individual chapter can take on a time-period or topic flavor (e.g. a Bass
 * Reeves chapter wears wild-west colors and a star glyph). The override only
 * tints THIS chapter card — the rest of the video stays in channel theme.
 *
 * Render plan:
 *   - 0.0–0.6s : background fades up; underline accent draws across
 *   - 0.6–2.4s : eyebrow ("Chapter N") and title hold; decorative icon scales in
 *   - 2.4–3.0s : fade out
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface ChapterOverrides {
  /** Color overrides applied only to this chapter card. */
  paletteOverride?: {
    bg?: string;
    accent?: string;
    text?: string;
    muted?: string;
  };
  /** Font overrides applied only to this chapter card. */
  fontOverride?: {
    heading?: string;
    body?: string;
  };
  /** Decorative glyph above the title — emoji or unicode (e.g., "★", "⚔︎", "♛"). */
  decorativeGlyph?: string;
  /** Background image URL — overlaid with a dim plate to keep text legible. */
  backgroundImageSrc?: string;
  /** 0–1, how dark the overlay sits on the bg image. Default 0.65. */
  backgroundOverlayOpacity?: number;
  /** Quiet caption underneath title — e.g., "Wild West, 1880s". */
  era?: string;
}

export interface ChapterCardProps {
  chapterNumber?: number | string;       // "1", "I", "Prologue"; omit to hide eyebrow
  eyebrow?: string;                       // e.g. "Chapter Three"; auto-built from chapterNumber if omitted
  title: string;                          // required
  subtitle?: string;
  overrides?: ChapterOverrides;
  durationFrames?: number;                // default 3s @ fps
  theme?: Partial<BrandTheme>;
}

export const ChapterCard: React.FC<ChapterCardProps> = ({
  chapterNumber,
  eyebrow,
  title,
  subtitle,
  overrides,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const baseTheme = resolveTheme(themeOverride);

  // Layer chapter overrides on top of channel theme
  const theme: BrandTheme = {
    ...baseTheme,
    bg: overrides?.paletteOverride?.bg ?? baseTheme.bg,
    accent: overrides?.paletteOverride?.accent ?? baseTheme.accent,
    text: overrides?.paletteOverride?.text ?? baseTheme.text,
    muted: overrides?.paletteOverride?.muted ?? baseTheme.muted,
    fontHeading: overrides?.fontOverride?.heading ?? baseTheme.fontHeading,
    fontBody: overrides?.fontOverride?.body ?? baseTheme.fontBody,
  };

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 3 * fps;
  const fadeOutStart = total - fadeFrames;
  const overlayOpacity = overrides?.backgroundOverlayOpacity ?? 0.65;

  const eyebrowText = eyebrow ?? (chapterNumber !== undefined ? `Chapter ${chapterNumber}` : null);

  const cardOpacity = interpolate(frame, [0, fadeFrames * 0.4, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Eyebrow + title rise + scale
  const titleRise = interpolate(frame, [10, 38], [16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eyebrowOpacity = interpolate(frame, [4, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Underline draws left → right over 0.5s
  const underlineProgress = interpolate(frame, [16, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Decorative glyph scale-in
  const glyphScale = interpolate(frame, [6, 26], [0.6, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glyphOpacity = interpolate(frame, [6, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Subtitle reveal slightly later
  const subtitleOpacity = interpolate(frame, [22, 42], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: theme.bg, overflow: "hidden" }}>
      {/* Background image (optional) */}
      {overrides?.backgroundImageSrc ? (
        <>
          <Img
            src={overrides.backgroundImageSrc}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(0.85)" }}
          />
          <AbsoluteFill style={{ background: theme.bg, opacity: overlayOpacity }} />
        </>
      ) : null}

      {/* Subtle radial vignette for depth */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, transparent 30%, ${theme.bg} 95%)`,
          pointerEvents: "none",
        }}
      />

      {/* Content */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 80,
          opacity: cardOpacity,
        }}
      >
        {/* Decorative glyph */}
        {overrides?.decorativeGlyph ? (
          <div
            style={{
              fontSize: 72,
              color: theme.accent,
              marginBottom: 18,
              opacity: glyphOpacity,
              transform: `scale(${glyphScale})`,
              lineHeight: 1,
            }}
          >
            {overrides.decorativeGlyph}
          </div>
        ) : null}

        {/* Eyebrow ("Chapter N") */}
        {eyebrowText ? (
          <div
            style={{
              fontFamily: theme.fontBody,
              fontSize: 28,
              fontWeight: 600,
              letterSpacing: "0.32em",
              textTransform: "uppercase",
              color: theme.accent,
              opacity: eyebrowOpacity,
              marginBottom: 22,
            }}
          >
            {eyebrowText}
          </div>
        ) : null}

        {/* Title */}
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: theme.headingWeight ?? 700,
            fontSize: 88,
            lineHeight: 1.08,
            color: theme.text,
            textAlign: "center",
            maxWidth: "84%",
            opacity: titleOpacity,
            transform: `translateY(${titleRise}px)`,
            letterSpacing: "0.005em",
          }}
        >
          {title}
        </div>

        {/* Animated underline */}
        <div
          style={{
            marginTop: 30,
            height: 2,
            width: 320,
            background: theme.accent,
            transform: `scaleX(${underlineProgress})`,
            transformOrigin: "left",
            boxShadow: `0 0 16px ${theme.accent}88`,
          }}
        />

        {/* Subtitle */}
        {subtitle ? (
          <div
            style={{
              marginTop: 28,
              fontFamily: theme.fontBody,
              fontSize: 30,
              fontStyle: "italic",
              color: theme.text,
              opacity: subtitleOpacity * 0.9,
              maxWidth: "70%",
              textAlign: "center",
              lineHeight: 1.45,
            }}
          >
            {subtitle}
          </div>
        ) : null}

        {/* Era caption */}
        {overrides?.era ? (
          <div
            style={{
              marginTop: 36,
              fontFamily: theme.fontBody,
              fontSize: 22,
              fontWeight: 600,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: theme.muted ?? theme.text,
              opacity: subtitleOpacity * 0.85,
            }}
          >
            {overrides.era}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// Era preset helpers — shorthand the asset director can pass to overrides.
//
// Example for a Bass Reeves chapter:
//   <ChapterCard
//     title="The Marshal They Forgot"
//     overrides={ERA_PRESETS.wild_west}
//   />
//
// These are starting points — the asset director should still tweak per
// chapter. Era ≠ design system — it's a reference, not a lock.
// ─────────────────────────────────────────────────────────────────────────

export const ERA_PRESETS: Record<string, ChapterOverrides> = {
  wild_west: {
    paletteOverride: { bg: "#2a1810", accent: "#c97842", text: "#f0d8b0", muted: "#8a6e54" },
    fontOverride: { heading: "Playfair Display, Georgia, serif" },
    decorativeGlyph: "★",
    era: "Wild West · 1870s–1900s",
  },
  ancient_rome: {
    paletteOverride: { bg: "#1a1410", accent: "#c9a84c", text: "#f0e6d2" },
    fontOverride: { heading: "EB Garamond, Georgia, serif" },
    decorativeGlyph: "Ⅹ",
    era: "Ancient Rome",
  },
  medieval: {
    paletteOverride: { bg: "#1c0e0a", accent: "#a02828", text: "#e8d8b8" },
    fontOverride: { heading: "Cormorant Garamond, Georgia, serif" },
    decorativeGlyph: "✠",
    era: "Medieval Europe",
  },
  industrial: {
    paletteOverride: { bg: "#1a1a1c", accent: "#b8923a", text: "#d8d4c8" },
    decorativeGlyph: "⚙",
    era: "Industrial Era",
  },
  roaring_20s: {
    paletteOverride: { bg: "#0a0a14", accent: "#d4a54a", text: "#f0e6d2" },
    fontOverride: { heading: "Playfair Display, Georgia, serif" },
    decorativeGlyph: "✦",
    era: "The Roaring Twenties",
  },
  cold_war: {
    paletteOverride: { bg: "#14181c", accent: "#8a9a4a", text: "#d8d4c8", muted: "#6a6a7a" },
    decorativeGlyph: "☢",
    era: "Cold War · 1947–1991",
  },
  belle_epoque: {
    paletteOverride: { bg: "#181420", accent: "#c97a8a", text: "#f0e6d2" },
    fontOverride: { heading: "Cormorant Garamond, Georgia, serif" },
    decorativeGlyph: "❦",
    era: "Belle Époque",
  },
  ancient_east: {
    paletteOverride: { bg: "#1a1a14", accent: "#c46a4a", text: "#f0e0c8" },
    fontOverride: { heading: "Cormorant Garamond, Georgia, serif" },
    decorativeGlyph: "壽",
    era: "Imperial East Asia",
  },
};
