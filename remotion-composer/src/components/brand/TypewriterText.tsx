/**
 * TypewriterText — chars-per-second text reveal with optional blinking cursor.
 *
 * Channel-themed font and color. Sleep-safe default of 12 chars/sec.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface TypewriterTextProps {
  /** Required text. Newlines (\n) are honored. */
  text: string;

  /** Reveal speed. Default 12 (slow, sleep-safe). Faster = more frenetic — discouraged for sleep content. */
  charsPerSecond?: number;

  /** Show a blinking cursor at the current reveal position. Default true. */
  cursorVisible?: boolean;

  /** Cursor character. Default "▍". Use "_" or "│" for a more terminal feel. */
  cursorChar?: string;

  /** Pixel size for the rendered text. Default 56. */
  fontSize?: number;

  /** Vertical alignment. Default "center". */
  vAlign?: "top" | "center" | "bottom";

  /** Total frames the component holds for. Default = reveal time + theme.holdMinFrames + fade out. */
  durationFrames?: number;

  theme?: Partial<BrandTheme>;
}

export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  charsPerSecond = 12,
  cursorVisible = true,
  cursorChar = "▍",
  fontSize = 56,
  vAlign = "center",
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const charsPerFrame = charsPerSecond / fps;
  const revealFrames = Math.ceil(text.length / charsPerFrame);
  const total = durationFrames ?? revealFrames + (theme.holdMinFrames ?? 96) + fadeFrames;

  const charsRevealed = Math.min(text.length, Math.floor(frame * charsPerFrame));
  const visibleText = text.slice(0, charsRevealed);

  // Cursor blink — 2-frame on/off cycle (12fps blink at 24fps)
  const cursorOn = cursorVisible && Math.floor(frame / 12) % 2 === 0;

  const fadeOutStart = Math.max(revealFrames, total - fadeFrames);
  const opacity = interpolate(frame, [0, 8, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const justify =
    vAlign === "top" ? "flex-start" : vAlign === "bottom" ? "flex-end" : "center";

  return (
    <AbsoluteFill
      style={{
        justifyContent: justify,
        alignItems: "center",
        background: theme.bg,
        padding: vAlign === "top" ? "120px 80px 80px" : vAlign === "bottom" ? "80px 80px 120px" : 80,
      }}
    >
      <div
        style={{
          opacity,
          fontFamily: theme.fontHeading,
          fontWeight: theme.headingWeight ?? 700,
          fontSize,
          color: theme.text,
          lineHeight: 1.4,
          maxWidth: "85%",
          textAlign: "center",
          whiteSpace: "pre-wrap",
          letterSpacing: "0.005em",
        }}
      >
        {visibleText}
        {cursorOn ? (
          <span style={{ color: theme.accent, marginLeft: 6 }}>{cursorChar}</span>
        ) : (
          <span style={{ visibility: "hidden", marginLeft: 6 }}>{cursorChar}</span>
        )}
      </div>
    </AbsoluteFill>
  );
};
