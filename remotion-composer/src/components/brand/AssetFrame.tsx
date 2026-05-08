/**
 * AssetFrame — branded frame around copyright-free photos / clips / any node.
 *
 * 5 variants:
 *   - parchment   : Huxley-default warm cream border with soft amber glow
 *   - boardroom   : MM-default geometric brass border on deep navy plate
 *   - polaroid    : universal — historical-photo white border, slight rotation
 *   - document    : MM-leaning paper texture, optional CLASSIFIED stamp
 *   - filmstrip   : for video clips — perforated edges
 *
 * Pass `src` for a simple image frame, or pass `children` to wrap arbitrary
 * Remotion nodes (e.g. an OffthreadVideo) inside the frame.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type AssetFrameVariant = "parchment" | "boardroom" | "polaroid" | "document" | "filmstrip";

export interface AssetFrameProps {
  variant: AssetFrameVariant;

  /** Image URL. Either src or children must be provided. */
  src?: string;

  /** Wrap arbitrary content (e.g., <OffthreadVideo>) instead of an Img. */
  children?: React.ReactNode;

  /** Aspect ratio of the inner asset (e.g., "16/9", "4/3", "1/1"). Default "4/3". */
  aspectRatio?: string;

  /** Caption text under the frame. Optional. */
  captionText?: string;

  /** Stamp text overlay (only renders for variant="document"). E.g. "CLASSIFIED". */
  stamp?: "CLASSIFIED" | "REDACTED" | string;

  /** Frame width in pixels. Default 1300. */
  width?: number;

  /** Total component duration in frames. Default = fade + textCardHold + fade. */
  durationFrames?: number;

  theme?: Partial<BrandTheme>;
}

export const AssetFrame: React.FC<AssetFrameProps> = ({
  variant,
  src,
  children,
  aspectRatio = "4/3",
  captionText,
  stamp,
  width = 1300,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? fadeFrames + (theme.textCardHoldFrames ?? 120) + fadeFrames;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = interpolate(frame, [0, fadeFrames], [0.98, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const frameStyle = getFrameStyle(variant, theme, width, aspectRatio);

  return (
    <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div
        style={{
          opacity,
          transform: `scale(${scale}) ${variant === "polaroid" ? "rotate(-1.6deg)" : ""}`,
          ...frameStyle.outer,
        }}
      >
        <div style={frameStyle.inner}>
          {children ? (
            children
          ) : src ? (
            <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : null}

          {variant === "filmstrip" ? <FilmstripPerforations theme={theme} /> : null}

          {variant === "document" && stamp ? (
            <div
              style={{
                position: "absolute",
                top: "20%",
                left: "50%",
                transform: "translate(-50%, 0) rotate(-8deg)",
                color: theme.stampRed ?? "#b41e1e",
                fontFamily: theme.fontMono ?? "Courier New, monospace",
                fontSize: 64,
                fontWeight: 900,
                letterSpacing: "0.15em",
                border: `4px solid ${theme.stampRed ?? "#b41e1e"}`,
                padding: "8px 20px",
                opacity: 0.92,
                pointerEvents: "none",
                textShadow: "0 2px 4px rgba(0,0,0,0.35)",
              }}
            >
              {stamp}
            </div>
          ) : null}
        </div>

        {captionText ? (
          <div
            style={{
              marginTop: 18,
              fontFamily: theme.fontBody,
              fontSize: 24,
              fontStyle: "italic",
              color: theme.text,
              textAlign: "center",
              maxWidth: width,
              letterSpacing: "0.02em",
            }}
          >
            {captionText}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const FilmstripPerforations: React.FC<{ theme: BrandTheme }> = ({ theme }) => {
  const holes = Array.from({ length: 14 });
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 16,
          background: "#0a0a0a",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-around",
          padding: "0 12px",
        }}
      >
        {holes.map((_, i) => (
          <div
            key={`top-${i}`}
            style={{ width: 18, height: 8, background: theme.bg, borderRadius: 1 }}
          />
        ))}
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 16,
          background: "#0a0a0a",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-around",
          padding: "0 12px",
        }}
      >
        {holes.map((_, i) => (
          <div
            key={`bot-${i}`}
            style={{ width: 18, height: 8, background: theme.bg, borderRadius: 1 }}
          />
        ))}
      </div>
    </>
  );
};

interface FrameStyles {
  outer: React.CSSProperties;
  inner: React.CSSProperties;
}

function getFrameStyle(
  variant: AssetFrameVariant,
  theme: BrandTheme,
  width: number,
  aspectRatio: string
): FrameStyles {
  const innerBase: React.CSSProperties = {
    position: "relative",
    width: "100%",
    aspectRatio,
    overflow: "hidden",
    background: "#000",
  };

  switch (variant) {
    case "parchment":
      return {
        outer: {
          width,
          padding: 18,
          background: "#1f1612",
          border: `2px solid ${theme.accent}`,
          borderRadius: 4,
          boxShadow: `0 0 36px ${theme.accent}33, 0 12px 36px rgba(0,0,0,0.5)`,
        },
        inner: { ...innerBase, border: `1px solid ${theme.accent}80` },
      };

    case "boardroom":
      return {
        outer: {
          width,
          padding: 12,
          background: theme.bg,
          border: `1px solid ${theme.accent}`,
          borderRadius: 2,
          boxShadow: `0 0 0 1px rgba(0,0,0,0.6), 0 16px 48px rgba(0,0,0,0.65)`,
          position: "relative",
        },
        inner: { ...innerBase },
      };

    case "polaroid":
      return {
        outer: {
          width,
          padding: "16px 16px 64px 16px",
          background: "#f5ead0",
          borderRadius: 2,
          boxShadow: `0 8px 24px rgba(0,0,0,0.5)`,
        },
        inner: { ...innerBase, background: "#0d0d1a" },
      };

    case "document":
      return {
        outer: {
          width,
          padding: 24,
          background: "#1a1814",
          border: `1px solid ${theme.muted ?? "#6a6a7a"}`,
          borderRadius: 0,
          boxShadow: `0 8px 24px rgba(0,0,0,0.55)`,
          position: "relative",
        },
        inner: { ...innerBase, background: "#0d0d0d" },
      };

    case "filmstrip":
      return {
        outer: {
          width,
          padding: 0,
          background: "#0a0a0a",
        },
        inner: { ...innerBase, marginTop: 16, marginBottom: 16, background: "#000" },
      };
  }
}
