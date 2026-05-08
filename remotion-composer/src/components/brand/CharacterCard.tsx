/**
 * CharacterCard — figure / organization intro card.
 *
 * Auto-alternates top-right (even sceneIndex) and top-left (odd) for variety.
 * Override via `position` prop. Channel-themed frame + plate.
 *
 * Default schema (per brand review): name + dates + role only. The `stats[]`
 * field is opt-in via `showStats` — older asset manifests with stats won't
 * render them unless explicitly requested.
 *
 * Text limits enforced via auto-shrink: each field has a max width, and the
 * font scales DOWN (never up) until the text fits. Floor is 85% of base so
 * text stays legible at 1080p (was 70% — too small).
 *
 * Sleep-safe: 1.5s fade in, hold for at least 4s, 1.5s fade out.
 *
 * @version 0.2.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type CharacterCardPosition = "top-right" | "top-left" | "bottom-right" | "bottom-left";

export interface CharacterCardProps {
  /** Required — figure or organization name. */
  name: string;

  /** Role / title / one-line descriptor (e.g., "Stoic philosopher, 121–180 AD"). */
  role?: string;

  /** Date range, lifespan, or era (e.g., "1809–1865"). */
  dates?: string;

  /**
   * Up to 2 short stat lines (e.g., "Net worth: ~$2T (today's dollars)").
   * NOT shown by default — pass `showStats` to enable. Brand review feedback
   * was "card has too much extra information; just need name/year/role".
   */
  stats?: [string?, string?];

  /** Opt-in: render the `stats[]` lines under the role. */
  showStats?: boolean;

  /** Public URL or imported asset for the portrait. Optional. */
  portraitSrc?: string;

  /** Explicit position. Omit to alternate from sceneIndex. */
  position?: CharacterCardPosition;

  /** Even values land top-right; odd land top-left. Ignored if `position` is set. */
  sceneIndex?: number;

  /** Total frames the card is on screen (including fade in/out). Default = 5s @ fps. */
  durationFrames?: number;

  theme?: Partial<BrandTheme>;
}

const MAX_CHARS = {
  name: 30,
  role: 50,
  dates: 25,
  stat: 25,
};

function autoShrinkFontSize(baseSize: number, text: string, maxChars: number): number {
  if (!text) return baseSize;
  if (text.length <= maxChars) return baseSize;
  // Linear shrink to a floor at 85% of base — keep readable at 1080p.
  const ratio = maxChars / text.length;
  return Math.max(baseSize * 0.85, baseSize * ratio);
}

export const CharacterCard: React.FC<CharacterCardProps> = ({
  name,
  role,
  dates,
  stats,
  showStats = false,
  portraitSrc,
  position,
  sceneIndex = 0,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const totalFrames = durationFrames ?? 5 * fps;
  const fadeOutStart = Math.max(fadeFrames, totalFrames - fadeFrames);

  // Resolve position — explicit or alternating
  const resolved: CharacterCardPosition =
    position ?? (sceneIndex % 2 === 0 ? "top-right" : "top-left");

  const opacity = interpolate(
    frame,
    [0, fadeFrames, fadeOutStart, totalFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Slight slide-in offset based on side
  const slideX = interpolate(frame, [0, fadeFrames], [resolved.endsWith("right") ? 30 : -30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Anchor styles per position
  const anchorStyle: React.CSSProperties = (() => {
    const base: React.CSSProperties = { position: "absolute", padding: 32 };
    switch (resolved) {
      case "top-right":
        return { ...base, top: 48, right: 48 };
      case "top-left":
        return { ...base, top: 48, left: 48 };
      case "bottom-right":
        return { ...base, bottom: 48, right: 48 };
      case "bottom-left":
        return { ...base, bottom: 48, left: 48 };
    }
  })();

  const cardWidth = 880;
  const portraitW = 200;
  const portraitH = 250;
  const showStatsRow = showStats && stats && stats.some(Boolean);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          ...anchorStyle,
          opacity,
          transform: `translateX(${slideX}px)`,
          width: cardWidth,
          background: theme.bg,
          border: `2px solid ${theme.accent}`,
          borderRadius: 4,
          padding: 24,
          boxShadow: `0 0 0 1px ${theme.bg}, 0 8px 32px rgba(0,0,0,0.45)`,
          display: "flex",
          gap: 18,
          alignItems: "flex-start",
          fontFamily: theme.fontBody,
          color: theme.text,
        }}
      >
        {portraitSrc ? (
          <div
            style={{
              width: portraitW,
              height: portraitH,
              flexShrink: 0,
              border: `3px solid ${theme.accent}`,
              overflow: "hidden",
              background: theme.muted ?? "#3a3a4a",
              boxShadow: `0 4px 16px rgba(0,0,0,0.5)`,
            }}
          >
            <Img
              src={portraitSrc}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        ) : null}

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: autoShrinkFontSize(48, name, MAX_CHARS.name),
              lineHeight: 1.15,
              color: theme.text,
              marginBottom: 8,
            }}
          >
            {name}
          </div>

          {dates ? (
            <div
              style={{
                fontFamily: theme.fontBody,
                fontStyle: "italic",
                fontSize: autoShrinkFontSize(28, dates, MAX_CHARS.dates),
                color: theme.accent,
                marginBottom: 14,
                letterSpacing: "0.05em",
                fontWeight: 600,
              }}
            >
              {dates}
            </div>
          ) : null}

          {role ? (
            <div
              style={{
                fontFamily: theme.fontBody,
                fontSize: autoShrinkFontSize(28, role, MAX_CHARS.role),
                lineHeight: 1.4,
                color: theme.text,
                marginBottom: showStatsRow ? 16 : 0,
              }}
            >
              {role}
            </div>
          ) : null}

          {showStatsRow ? (
            <div
              style={{
                borderTop: `1px solid ${theme.accent}55`,
                paddingTop: 12,
                color: theme.muted ?? theme.text,
                fontFamily: theme.fontBody,
                lineHeight: 1.5,
              }}
            >
              {stats?.[0] ? (
                <div style={{ fontSize: autoShrinkFontSize(24, stats[0], MAX_CHARS.stat) }}>
                  {stats[0]}
                </div>
              ) : null}
              {stats?.[1] ? (
                <div style={{ fontSize: autoShrinkFontSize(24, stats[1], MAX_CHARS.stat) }}>
                  {stats[1]}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
