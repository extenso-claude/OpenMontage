/**
 * LowerThird — name + role strip in lower-third position.
 *
 * 5 variants:
 *   - simple_left       : name + role, bottom-left, accent underline
 *   - simple_right      : same, bottom-right
 *   - dual_line         : category tag above name (e.g., "ECONOMIST" / "Robert Lucas")
 *   - boxed             : full plate with brass border, denser typography
 *   - news_ticker       : horizontal strip across full width with accent block
 *
 * Slides in from the side, holds, slides out.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type LowerThirdVariant =
  | "simple_left"
  | "simple_right"
  | "dual_line"
  | "boxed"
  | "news_ticker";

export interface LowerThirdProps {
  variant: LowerThirdVariant;
  /** Primary text — usually a name. */
  name: string;
  /** Secondary text — role, title, organization. */
  role?: string;
  /** Used by `dual_line` and `news_ticker` — small all-caps category tag. */
  category?: string;
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  variant,
  name,
  role,
  category,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 5 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const slideFromRight = variant === "simple_right";
  const slideOffset = interpolate(
    frame,
    [0, fadeFrames, fadeOutStart, total],
    [slideFromRight ? 60 : -60, 0, 0, slideFromRight ? 60 : -60],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  if (variant === "simple_left" || variant === "simple_right") {
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            bottom: 80,
            [variant === "simple_left" ? "left" : "right"]: 80,
            textAlign: variant === "simple_left" ? "left" : "right",
            opacity,
            transform: `translateX(${slideOffset}px)`,
            fontFamily: theme.fontBody,
            color: theme.text,
            paddingTop: 18,
            borderTop: `3px solid ${theme.accent}`,
            minWidth: 540,
            background: `linear-gradient(to ${variant === "simple_left" ? "right" : "left"}, ${theme.bg}EE 0%, ${theme.bg}AA 70%, transparent 100%)`,
            paddingLeft: 22,
            paddingRight: 22,
            paddingBottom: 18,
          }}
        >
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 56,
              lineHeight: 1.1,
              color: theme.text,
            }}
          >
            {name}
          </div>
          {role ? (
            <div style={{ fontSize: 30, color: theme.accent, marginTop: 10, letterSpacing: "0.04em" }}>
              {role}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "dual_line") {
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: 80,
            opacity,
            transform: `translateX(${slideOffset}px)`,
            fontFamily: theme.fontBody,
            color: theme.text,
          }}
        >
          {category ? (
            <div
              style={{
                fontSize: 22,
                letterSpacing: "0.32em",
                textTransform: "uppercase",
                color: theme.accent,
                marginBottom: 10,
                fontFamily: theme.fontBody,
                fontWeight: 600,
              }}
            >
              {category}
            </div>
          ) : null}
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 44,
              color: theme.text,
              lineHeight: 1.1,
              borderLeft: `4px solid ${theme.accent}`,
              paddingLeft: 18,
            }}
          >
            {name}
          </div>
          {role ? (
            <div
              style={{
                fontSize: 26,
                color: theme.muted ?? theme.text,
                marginTop: 8,
                fontStyle: "italic",
                paddingLeft: 22,
              }}
            >
              {role}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    );
  }

  if (variant === "boxed") {
    return (
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: 80,
            opacity,
            transform: `translateX(${slideOffset}px)`,
            fontFamily: theme.fontBody,
            color: theme.text,
            background: theme.bg,
            border: `1px solid ${theme.accent}`,
            padding: "16px 26px",
            boxShadow: `0 8px 32px rgba(0,0,0,0.6)`,
            minWidth: 360,
          }}
        >
          {category ? (
            <div
              style={{
                fontSize: 20,
                letterSpacing: "0.28em",
                textTransform: "uppercase",
                color: theme.accent,
                marginBottom: 8,
                paddingBottom: 8,
                borderBottom: `1px solid ${theme.accent}55`,
                fontWeight: 600,
              }}
            >
              {category}
            </div>
          ) : null}
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 40,
              color: theme.text,
              lineHeight: 1.1,
            }}
          >
            {name}
          </div>
          {role ? (
            <div
              style={{
                fontSize: 24,
                color: theme.text,
                marginTop: 6,
                opacity: 0.9,
              }}
            >
              {role}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    );
  }

  // news_ticker
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 0,
          right: 0,
          opacity,
          height: 110,
          display: "flex",
          alignItems: "stretch",
          background: `${theme.bg}F0`,
          borderTop: `3px solid ${theme.accent}`,
          borderBottom: `1px solid ${theme.accent}66`,
          fontFamily: theme.fontBody,
        }}
      >
        {category ? (
          <div
            style={{
              background: theme.accent,
              color: theme.bg,
              padding: "0 36px",
              display: "flex",
              alignItems: "center",
              fontFamily: theme.fontHeading,
              fontWeight: 800,
              fontSize: 24,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              flexShrink: 0,
            }}
          >
            {category}
          </div>
        ) : null}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            paddingLeft: 32,
            paddingRight: 32,
            color: theme.text,
            flex: 1,
            transform: `translateX(${slideOffset}px)`,
          }}
        >
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 36,
              lineHeight: 1.1,
            }}
          >
            {name}
          </div>
          {role ? (
            <div
              style={{
                fontSize: 22,
                color: theme.muted ?? theme.text,
                marginTop: 4,
              }}
            >
              {role}
            </div>
          ) : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
