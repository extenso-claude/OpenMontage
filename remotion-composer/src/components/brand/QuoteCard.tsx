/**
 * QuoteCard — full-screen quote with optional portrait.
 *
 * 4 variants:
 *   - centered_no_portrait    : classic quote, decorative quotation marks
 *   - portrait_left           : portrait left, quote right
 *   - portrait_right          : portrait right, quote left
 *   - attributed_minimal      : small quote with subtle attribution, no decoration
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type QuoteCardVariant =
  | "centered_no_portrait"
  | "portrait_left"
  | "portrait_right"
  | "attributed_minimal";

export interface QuoteCardProps {
  variant: QuoteCardVariant;
  quote: string;
  attribution?: string;        // e.g., "Marcus Aurelius, Meditations"
  portraitSrc?: string;        // required for portrait_left and portrait_right
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  variant,
  quote,
  attribution,
  portraitSrc,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 6 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const quoteRise = interpolate(frame, [12, 36], [16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const attributionOpacity = interpolate(frame, [30, 54], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Decorative quotation marks scale in
  const marksScale = interpolate(frame, [4, 24], [0.6, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const marksOpacity = interpolate(frame, [4, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Vignette for visual focus
  const Vignette: React.FC = () => (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at center, transparent 35%, ${theme.bg} 95%)`,
        pointerEvents: "none",
      }}
    />
  );

  // ─── centered_no_portrait ────────────────────────────────────────────
  if (variant === "centered_no_portrait") {
    return (
      <AbsoluteFill style={{ background: theme.bg, opacity }}>
        <Vignette />
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 120 }}>
          <div style={{ position: "relative", maxWidth: "78%" }}>
            <div
              style={{
                position: "absolute",
                left: -40,
                top: -90,
                fontFamily: theme.fontHeading,
                fontSize: 240,
                color: theme.accent,
                opacity: marksOpacity * 0.4,
                transform: `scale(${marksScale})`,
                lineHeight: 1,
                pointerEvents: "none",
              }}
            >
              &ldquo;
            </div>
            <div
              style={{
                fontFamily: theme.fontHeading,
                fontWeight: theme.headingWeight ?? 700,
                fontSize: 56,
                lineHeight: 1.4,
                color: theme.text,
                textAlign: "center",
                fontStyle: "italic",
                transform: `translateY(${quoteRise}px)`,
              }}
            >
              {quote}
            </div>
            {attribution ? (
              <div
                style={{
                  marginTop: 32,
                  fontFamily: theme.fontBody,
                  fontSize: 22,
                  color: theme.accent,
                  textAlign: "center",
                  opacity: attributionOpacity,
                  letterSpacing: "0.06em",
                }}
              >
                — {attribution}
              </div>
            ) : null}
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ─── portrait variants ───────────────────────────────────────────────
  if (variant === "portrait_left" || variant === "portrait_right") {
    const portraitFirst = variant === "portrait_left";
    return (
      <AbsoluteFill style={{ background: theme.bg, opacity }}>
        <Vignette />
        <AbsoluteFill
          style={{
            display: "flex",
            flexDirection: portraitFirst ? "row" : "row-reverse",
            alignItems: "center",
            justifyContent: "center",
            padding: 100,
            gap: 80,
          }}
        >
          {portraitSrc ? (
            <div
              style={{
                width: 380,
                height: 460,
                flexShrink: 0,
                background: theme.muted,
                border: `2px solid ${theme.accent}`,
                overflow: "hidden",
                boxShadow: `0 16px 48px rgba(0,0,0,0.6)`,
                transform: `scale(${marksScale})`,
              }}
            >
              <Img src={portraitSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
          ) : null}
          <div style={{ flex: 1, maxWidth: 800 }}>
            <div
              style={{
                fontFamily: theme.fontHeading,
                fontSize: 80,
                color: theme.accent,
                lineHeight: 0.4,
                opacity: marksOpacity * 0.7,
                marginBottom: 14,
              }}
            >
              &ldquo;
            </div>
            <div
              style={{
                fontFamily: theme.fontHeading,
                fontWeight: theme.headingWeight ?? 700,
                fontSize: 42,
                lineHeight: 1.4,
                color: theme.text,
                fontStyle: "italic",
                transform: `translateY(${quoteRise}px)`,
              }}
            >
              {quote}
            </div>
            {attribution ? (
              <div
                style={{
                  marginTop: 28,
                  fontFamily: theme.fontBody,
                  fontSize: 20,
                  color: theme.accent,
                  opacity: attributionOpacity,
                  letterSpacing: "0.06em",
                }}
              >
                — {attribution}
              </div>
            ) : null}
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ─── attributed_minimal ──────────────────────────────────────────────
  return (
    <AbsoluteFill style={{ background: theme.bg, opacity }}>
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 160 }}>
        <div style={{ maxWidth: "70%", textAlign: "center" }}>
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontSize: 38,
              lineHeight: 1.5,
              color: theme.text,
              fontStyle: "italic",
              transform: `translateY(${quoteRise}px)`,
            }}
          >
            {quote}
          </div>
          {attribution ? (
            <div
              style={{
                marginTop: 24,
                fontFamily: theme.fontBody,
                fontSize: 14,
                color: theme.muted ?? theme.text,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                opacity: attributionOpacity,
              }}
            >
              {attribution}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
