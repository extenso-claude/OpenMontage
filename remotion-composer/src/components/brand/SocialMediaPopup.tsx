/**
 * SocialMediaPopup — UI mockup of a text message thread, tweet, or news headline.
 *
 * 3 variants:
 *   - text_message  : iMessage-style chat bubbles with typing indicator
 *   - tweet         : Twitter/X post card with avatar, handle, body, timestamp
 *   - headline      : newspaper / press headline card
 *
 * Used for "the message read..." or "the headline ran..." reveal moments.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type SocialMediaVariant = "text_message" | "tweet" | "headline";

export interface MessageBubble {
  side: "left" | "right";
  text: string;
  /** Optional timestamp */
  time?: string;
  /** Seconds (from scene start) when this bubble appears. */
  revealAtSeconds?: number;
}

export interface SocialMediaPopupProps {
  variant: SocialMediaVariant;

  // text_message
  bubbles?: MessageBubble[];
  contactName?: string;

  // tweet
  authorName?: string;
  authorHandle?: string;
  avatarSrc?: string;
  body?: string;
  timestamp?: string;
  /** Tweet metrics — replies / retweets / likes */
  stats?: { replies?: number; retweets?: number; likes?: number };

  // headline
  publication?: string;
  headlineText?: string;
  subheadline?: string;
  dateLine?: string;

  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

export const SocialMediaPopup: React.FC<SocialMediaPopupProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(props.theme);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = props.durationFrames ?? 7 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
      }}
    >
      {props.variant === "text_message" ? (
        <TextMessage {...props} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
      {props.variant === "tweet" ? (
        <Tweet {...props} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
      {props.variant === "headline" ? (
        <Headline {...props} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// text_message
// ─────────────────────────────────────────────────────────────────────────

const TextMessage: React.FC<{
  bubbles?: MessageBubble[];
  contactName?: string;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ bubbles = [], contactName = "Unknown", theme, frame, fps, total }) => {
  const usable = total - (theme.fadeFrames ?? 36) * 2;
  const slot = usable / Math.max(bubbles.length, 1);

  return (
    <div
      style={{
        width: 820,
        background: "#1c1c1e",
        borderRadius: 48,
        padding: "32px 24px 40px",
        border: `2px solid ${theme.muted ?? "#3a3a4a"}`,
        boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        fontFamily:
          'system-ui, -apple-system, "SF Pro", "Helvetica Neue", Arial, sans-serif',
        color: "#fff",
      }}
    >
      {/* Header */}
      <div
        style={{
          textAlign: "center",
          paddingBottom: 20,
          marginBottom: 20,
          borderBottom: "1px solid #2a2a2e",
        }}
      >
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            background: `${theme.accent}33`,
            margin: "0 auto 10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 32,
            color: theme.accent,
            fontWeight: 700,
            border: `2px solid ${theme.accent}88`,
          }}
        >
          {contactName.charAt(0).toUpperCase()}
        </div>
        <div style={{ fontSize: 22, fontWeight: 600 }}>{contactName}</div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: "0 12px" }}>
        {bubbles.map((b, i) => {
          const reveal = (b.revealAtSeconds ?? (i + 0.5) * (slot / fps)) * fps;
          const showTyping = frame > reveal - 18 && frame < reveal;
          const visible = frame >= reveal;
          const scale = interpolate(frame, [reveal, reveal + 12], [0.85, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          if (!visible && !showTyping) return null;

          if (showTyping) {
            return (
              <div
                key={i}
                style={{
                  alignSelf: b.side === "right" ? "flex-end" : "flex-start",
                  background: "#3a3a3c",
                  borderRadius: 26,
                  padding: "14px 22px",
                  display: "flex",
                  gap: 6,
                }}
              >
                {[0, 1, 2].map((d) => {
                  const dotPhase = (frame * 4 + d * 4) % 24;
                  return (
                    <div
                      key={d}
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: "50%",
                        background: dotPhase < 12 ? "#aaa" : "#666",
                      }}
                    />
                  );
                })}
              </div>
            );
          }

          return (
            <div
              key={i}
              style={{
                alignSelf: b.side === "right" ? "flex-end" : "flex-start",
                maxWidth: "78%",
                padding: "16px 24px",
                borderRadius: 28,
                fontSize: 26,
                lineHeight: 1.35,
                background: b.side === "right" ? "#0b84fe" : "#3a3a3c",
                color: "#fff",
                transform: `scale(${scale})`,
                transformOrigin: b.side === "right" ? "bottom right" : "bottom left",
                boxShadow: "0 1px 1px rgba(0,0,0,0.18)",
              }}
            >
              {b.text}
              {b.time ? (
                <div style={{ fontSize: 16, color: "#9a9a9a", marginTop: 6, textAlign: "right" }}>
                  {b.time}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// tweet
// ─────────────────────────────────────────────────────────────────────────

const Tweet: React.FC<{
  authorName?: string;
  authorHandle?: string;
  avatarSrc?: string;
  body?: string;
  timestamp?: string;
  stats?: { replies?: number; retweets?: number; likes?: number };
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ authorName = "Unknown", authorHandle = "@unknown", avatarSrc, body = "", timestamp, stats, theme, frame, fps }) => {
  const bodyChars = Math.floor((frame / fps) * 18);
  const visibleBody = body.slice(0, bodyChars);
  const showStats = bodyChars >= body.length;
  const statsOpacity = interpolate(frame, [(body.length / 18) * fps, (body.length / 18) * fps + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: 1040,
        background: "#15202b",
        borderRadius: 22,
        padding: 36,
        border: "1px solid #38444d",
        color: "#e7e9ea",
        fontFamily:
          'system-ui, -apple-system, "SF Pro", Arial, sans-serif',
        boxShadow: "0 16px 48px rgba(0,0,0,0.55)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <div
          style={{
            width: 84,
            height: 84,
            borderRadius: "50%",
            background: "#3a3a4a",
            overflow: "hidden",
            border: `2px solid ${theme.muted ?? "#5a5a6a"}`,
            flexShrink: 0,
          }}
        >
          {avatarSrc ? (
            <Img src={avatarSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                color: "#a0a0a0",
                fontWeight: 700,
                fontSize: 36,
              }}
            >
              {authorName.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 28 }}>{authorName}</div>
          <div style={{ color: "#71767b", fontSize: 22 }}>{authorHandle}</div>
        </div>
      </div>

      <div
        style={{
          marginTop: 20,
          fontSize: 32,
          lineHeight: 1.45,
          color: "#e7e9ea",
          minHeight: 110,
        }}
      >
        {visibleBody}
        {bodyChars < body.length ? <span style={{ opacity: 0.6 }}>▍</span> : null}
      </div>

      {timestamp ? (
        <div style={{ marginTop: 18, color: "#71767b", fontSize: 20, opacity: showStats ? 1 : 0 }}>
          {timestamp}
        </div>
      ) : null}

      {stats ? (
        <div
          style={{
            marginTop: 20,
            paddingTop: 20,
            borderTop: "1px solid #38444d",
            display: "flex",
            gap: 44,
            opacity: statsOpacity,
            fontSize: 22,
            color: "#71767b",
          }}
        >
          {stats.replies !== undefined ? <div>💬 {stats.replies.toLocaleString()}</div> : null}
          {stats.retweets !== undefined ? <div>🔁 {stats.retweets.toLocaleString()}</div> : null}
          {stats.likes !== undefined ? <div>♡ {stats.likes.toLocaleString()}</div> : null}
        </div>
      ) : null}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// headline
// ─────────────────────────────────────────────────────────────────────────

const Headline: React.FC<{
  publication?: string;
  headlineText?: string;
  subheadline?: string;
  dateLine?: string;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ publication, headlineText, subheadline, dateLine, theme, frame }) => {
  const pubOpacity = interpolate(frame, [4, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const headlineOpacity = interpolate(frame, [16, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subOpacity = interpolate(frame, [32, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lineProgress = interpolate(frame, [20, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div
      style={{
        width: 1100,
        background: "#f4ecdc",
        padding: 56,
        boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        color: "#1a1410",
        fontFamily: '"Times New Roman", "EB Garamond", Georgia, serif',
        position: "relative",
      }}
    >
      <div
        style={{
          textAlign: "center",
          fontWeight: 900,
          fontSize: 38,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          opacity: pubOpacity,
        }}
      >
        {publication ?? "THE MORNING POST"}
      </div>
      <div
        style={{
          height: 4,
          background: "#1a1410",
          margin: "16px auto 28px",
          width: `${lineProgress * 100}%`,
          maxWidth: 800,
        }}
      />

      {dateLine ? (
        <div
          style={{
            textAlign: "center",
            fontSize: 14,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "#5a4a3a",
            marginBottom: 24,
            opacity: pubOpacity,
          }}
        >
          {dateLine}
        </div>
      ) : null}

      <div
        style={{
          textAlign: "center",
          fontSize: 64,
          fontWeight: 900,
          lineHeight: 1.05,
          letterSpacing: "0.005em",
          opacity: headlineOpacity,
        }}
      >
        {headlineText}
      </div>

      {subheadline ? (
        <div
          style={{
            textAlign: "center",
            marginTop: 24,
            fontSize: 22,
            fontStyle: "italic",
            color: "#3a2a1a",
            opacity: subOpacity,
            maxWidth: 800,
            margin: "24px auto 0",
            lineHeight: 1.45,
          }}
        >
          {subheadline}
        </div>
      ) : null}
    </div>
  );
};
