/**
 * CTABanner — bottom-band call-to-action strip.
 *
 * Slides up from below over fadeFrames, holds, slides back down.
 * 10 presets cover YouTube + Spotify subscribe / follow / comment / rate / share.
 *
 * The platform brand color tints the icon area; the rest of the strip uses
 * the channel's theme — keeps Huxley's warmth and MM's noir intact even when
 * the CTA is for YouTube or Spotify.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type CTAPreset =
  | "youtube_subscribe"
  | "youtube_comment"
  | "youtube_share"
  | "spotify_follow"
  | "spotify_comment"
  | "spotify_rate"
  | "spotify_share"
  | "both_subscribe"
  | "both_comment"
  | "both_rate";

export interface CTABannerProps {
  preset: CTAPreset;
  /** Override the action text. Optional — defaults are platform-aware. */
  customText?: string;
  /** Banner position. Default "bottom". */
  position?: "bottom" | "top";
  /** How many seconds the banner is fully visible (in addition to fade in/out). Default 5s. */
  holdSeconds?: number;
  /** Total component duration in frames. Default = fade + hold + fade. */
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

const YOUTUBE_RED = "#FF0000";
const SPOTIFY_GREEN = "#1DB954";

interface PresetConfig {
  platform: "youtube" | "spotify" | "both";
  icon: string;          // simple text glyph; replace with SVG later
  action: string;        // verb phrase
  message: string;       // CTA copy
  brandColor: string;
}

const PRESETS: Record<CTAPreset, PresetConfig> = {
  youtube_subscribe: {
    platform: "youtube",
    icon: "▶",
    action: "Subscribe",
    message: "Subscribe on YouTube to join our circle of dreamers",
    brandColor: YOUTUBE_RED,
  },
  youtube_comment: {
    platform: "youtube",
    icon: "💬",
    action: "Comment below",
    message: "Tell us where you're listening from in the comments",
    brandColor: YOUTUBE_RED,
  },
  youtube_share: {
    platform: "youtube",
    icon: "↗",
    action: "Share this episode",
    message: "Share with someone who'd find peace in this story",
    brandColor: YOUTUBE_RED,
  },
  spotify_follow: {
    platform: "spotify",
    icon: "♪",
    action: "Follow on Spotify",
    message: "Follow on Spotify so the next story finds you when you need it",
    brandColor: SPOTIFY_GREEN,
  },
  spotify_comment: {
    platform: "spotify",
    icon: "💬",
    action: "Leave a comment",
    message: "Share your thoughts on Spotify — we read every one",
    brandColor: SPOTIFY_GREEN,
  },
  spotify_rate: {
    platform: "spotify",
    icon: "★",
    action: "Rate the show",
    message: "If this helps you sleep, a rating on Spotify means the world",
    brandColor: SPOTIFY_GREEN,
  },
  spotify_share: {
    platform: "spotify",
    icon: "↗",
    action: "Share this episode",
    message: "Share with someone who could use a quiet hour",
    brandColor: SPOTIFY_GREEN,
  },
  both_subscribe: {
    platform: "both",
    icon: "+",
    action: "Subscribe / Follow",
    message: "Find us on YouTube or Spotify — join our circle of dreamers",
    brandColor: "#c9a84c",   // brass — neutral
  },
  both_comment: {
    platform: "both",
    icon: "💬",
    action: "Comment below",
    message: "Wherever you're listening, leave a comment — we read them all",
    brandColor: "#c9a84c",
  },
  both_rate: {
    platform: "both",
    icon: "★",
    action: "Rate the show",
    message: "A rating on YouTube or Spotify keeps these stories possible",
    brandColor: "#c9a84c",
  },
};

export const CTABanner: React.FC<CTABannerProps> = ({
  preset,
  customText,
  position = "bottom",
  holdSeconds = 5,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);
  const cfg = PRESETS[preset];

  const fadeFrames = theme.fadeFrames ?? 36;
  const holdFrames = Math.max(theme.holdMinFrames ?? 96, holdSeconds * fps);
  const total = durationFrames ?? fadeFrames + holdFrames + fadeFrames;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const slideY = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [60, 0, 0, 60], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const anchor: React.CSSProperties = position === "top"
    ? { top: 48, transform: `translateY(-${slideY}px)` }
    : { bottom: 48, transform: `translateY(${slideY}px)` };

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          marginLeft: -360,
          width: 720,
          minHeight: 96,
          background: theme.bg,
          border: `2px solid ${theme.accent}`,
          borderRadius: 6,
          boxShadow: `0 16px 48px rgba(0,0,0,0.55)`,
          display: "flex",
          alignItems: "center",
          padding: "18px 28px",
          gap: 24,
          opacity,
          fontFamily: theme.fontBody,
          color: theme.text,
          ...anchor,
        }}
      >
        {/* Platform icon block — uses platform brand color */}
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: 4,
            background: cfg.brandColor,
            color: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 36,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {cfg.icon}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 26,
              lineHeight: 1.1,
              color: theme.accent,
              marginBottom: 6,
              letterSpacing: "0.01em",
            }}
          >
            {cfg.action}
          </div>
          <div
            style={{
              fontSize: 18,
              lineHeight: 1.35,
              color: theme.text,
            }}
          >
            {customText ?? cfg.message}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
