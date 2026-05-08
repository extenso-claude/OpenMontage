/**
 * DocumentReveal — text document with animated highlights / redactions / signature.
 *
 * 3 variants:
 *   - highlight   : phrase gets a sweeping marker-style highlight in real time
 *   - redact      : phrase gets covered by an animated black bar (CLASSIFIED feel)
 *   - signature   : signature line on the document writes itself in over time
 *
 * Renders document text directly (typewriter feel) — no source PNG required.
 * For real source documents, drop the image as `backgroundSrc` and overlay
 * highlights/redactions on top using the `regions` prop.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";
import { Stamp } from "./Stamp";

export type DocumentRevealVariant = "highlight" | "redact" | "signature";

/** Bounding region in normalized 0–1 coords (relative to backgroundSrc). */
export interface DocRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  /** When (in seconds from scene start) this region animates in. */
  revealAtSeconds?: number;
  /**
   * If set, the document zooms to this region when it reveals (Ken Burns–style).
   * Brand review feedback: "when we focus on a paper asset, zoom in a bit as we
   * highlight certain words/text." Set on at most one region per scene to avoid
   * camera fights. Default false.
   */
  focusOnReveal?: boolean;
}

export interface DocumentRevealProps {
  variant: DocumentRevealVariant;

  /** Document body text. Newlines honored. Used when backgroundSrc is omitted. */
  bodyText?: string;
  /** Optional document image (e.g., scan of a real letter). */
  backgroundSrc?: string;
  /** Required title bar at top (e.g., "WAR DEPARTMENT MEMORANDUM"). */
  documentTitle?: string;
  /** Optional metadata (e.g., "Date: October 28, 1929 — File 7421-A"). */
  metadata?: string;

  /** Phrases to highlight or redact (only when bodyText is provided).
   *  When backgroundSrc is provided, use `regions` instead.
   */
  phrases?: string[];

  /** Region bounding boxes on the source image (when using backgroundSrc). */
  regions?: DocRegion[];

  /** Signature text — written letter-by-letter for the `signature` variant. */
  signatureText?: string;

  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

const PAPER_BG = "#f0e6d2";   // parchment cream
const INK = "#1a1410";

export const DocumentReveal: React.FC<DocumentRevealProps> = ({
  variant,
  bodyText,
  backgroundSrc,
  documentTitle,
  metadata,
  phrases,
  regions,
  signatureText,
  durationFrames,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 8 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Reveal phrases sequentially across the body
  const usableFrames = total - fadeFrames * 2;
  const phraseStartFrame = (i: number, count: number) =>
    fadeFrames + ((i + 0.4) / Math.max(count, 1)) * usableFrames * 0.85;

  // Zoom-to-region when one region is flagged focusOnReveal — Ken Burns
  // pushed slightly into the highlighted area for the second half of the scene.
  // We apply transform: translate(...) scale(k) on the document container.
  // CSS reads scale first (around center), then translate, so the recenter
  // translation is -k * (offset_in_original_pixels).
  const DOC_W_PX = 1100; // matches the document container width below
  const DOC_H_PX = 720; // matches the document container min-height
  const FOCUS_MAX_ZOOM = 1.18;
  const focusRegion = regions?.find((r) => r.focusOnReveal);
  const focusStartFrame = focusRegion
    ? Math.round((focusRegion.revealAtSeconds ?? 0.4) * fps)
    : 0;
  const focusProgress = focusRegion
    ? interpolate(frame, [focusStartFrame, focusStartFrame + Math.round(fps * 1.2)], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;
  const focusZoom = 1 + (FOCUS_MAX_ZOOM - 1) * focusProgress;
  const focusOffsetX = focusRegion
    ? (focusRegion.x + focusRegion.width / 2 - 0.5) * DOC_W_PX
    : 0;
  const focusOffsetY = focusRegion
    ? (focusRegion.y + focusRegion.height / 2 - 0.5) * DOC_H_PX
    : 0;
  const focusTx = -focusZoom * focusOffsetX * focusProgress;
  const focusTy = -focusZoom * focusOffsetY * focusProgress;

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity }}>
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 80 }}>
        <div
          style={{
            position: "relative",
            width: 1100,
            minHeight: 720,
            background: PAPER_BG,
            border: `4px double ${theme.muted ?? "#6a6a7a"}`,
            boxShadow: `0 24px 64px rgba(0,0,0,0.65), inset 0 0 80px rgba(150,120,80,0.15)`,
            padding: 64,
            color: INK,
            fontFamily: theme.fontBody,
            overflow: "hidden",
            transform: `translate(${focusTx}px, ${focusTy}px) scale(${focusZoom})`,
            transformOrigin: "center center",
            transition: "none",
          }}
        >
          {/* Aged-paper grain overlay */}
          <AbsoluteFill
            style={{
              background: `radial-gradient(circle at 20% 30%, transparent 60%, rgba(80,60,30,0.18) 100%), radial-gradient(circle at 80% 70%, transparent 60%, rgba(80,60,30,0.12) 100%)`,
              pointerEvents: "none",
            }}
          />

          {/* Background image (optional) */}
          {backgroundSrc ? (
            <div style={{ position: "absolute", inset: 64 }}>
              <Img
                src={backgroundSrc}
                style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }}
              />
            </div>
          ) : null}

          {/* Title bar */}
          {documentTitle ? (
            <div
              style={{
                fontFamily: theme.fontHeading,
                fontSize: 28,
                color: INK,
                fontWeight: 700,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                borderBottom: `2px solid ${INK}`,
                paddingBottom: 12,
                marginBottom: 18,
                textAlign: "center",
              }}
            >
              {documentTitle}
            </div>
          ) : null}

          {metadata ? (
            <div
              style={{
                fontFamily: theme.fontBody,
                fontSize: 22,
                color: "#5a4a3a",
                marginBottom: 24,
                fontStyle: "italic",
                textAlign: "center",
                fontWeight: 500,
              }}
            >
              {metadata}
            </div>
          ) : null}

          {/* Body */}
          {bodyText ? (
            <BodyWithPhraseAnimations
              text={bodyText}
              phrases={phrases ?? []}
              phraseAnimation={variant === "redact" ? "redact" : variant === "signature" ? "none" : "highlight"}
              theme={theme}
              frame={frame}
              total={total}
              startFn={(i: number) => phraseStartFrame(i, (phrases ?? []).length)}
            />
          ) : null}

          {/* Region overlays (when source image is supplied) */}
          {backgroundSrc && regions ? (
            <div style={{ position: "absolute", inset: 64 }}>
              {regions.map((r, i) => {
                const rev = (r.revealAtSeconds ?? (i + 0.4) * 1.0) * fps;
                const reveal = interpolate(frame, [rev, rev + 24], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                });
                if (reveal === 0) return null;
                if (variant === "redact") {
                  return (
                    <div
                      key={i}
                      style={{
                        position: "absolute",
                        left: `${r.x * 100}%`,
                        top: `${r.y * 100}%`,
                        width: `${r.width * reveal * 100}%`,
                        height: `${r.height * 100}%`,
                        background: "#0a0a0a",
                        boxShadow: "0 0 0 1px #000 inset",
                      }}
                    />
                  );
                }
                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      left: `${r.x * 100}%`,
                      top: `${r.y * 100}%`,
                      width: `${r.width * reveal * 100}%`,
                      height: `${r.height * 100}%`,
                      background: `${theme.accent}66`,
                      mixBlendMode: "multiply",
                    }}
                  />
                );
              })}
            </div>
          ) : null}

          {/* Signature variant */}
          {variant === "signature" && signatureText ? (
            <Signature
              text={signatureText}
              theme={theme}
              frame={frame}
              total={total}
              fps={fps}
            />
          ) : null}

        </div>
      </AbsoluteFill>

      {/* Stamp for redact variant — uses the shared Stamp component so the
          impact animation is identical wherever it appears. Rendered OUTSIDE
          the focus-zoom transform so the stamp lands on screen, not on the
          zoomed-in document. */}
      {variant === "redact" ? (
        <Stamp
          preset="redacted"
          impactAtSeconds={(total / fps) * 0.62}
          durationFrames={total}
          theme={themeOverride}
        />
      ) : null}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// Body text with phrase highlight or redact animations
// ─────────────────────────────────────────────────────────────────────────

const BodyWithPhraseAnimations: React.FC<{
  text: string;
  phrases: string[];
  phraseAnimation: "highlight" | "redact" | "none";
  theme: BrandTheme;
  frame: number;
  total: number;
  startFn: (i: number) => number;
}> = ({ text, phrases, phraseAnimation, theme, frame, startFn }) => {
  // Build segments: alternating plain / phrase / plain ...
  let segments: Array<{ text: string; phraseIdx?: number }> = [{ text }];
  phrases.forEach((p, idx) => {
    const next: typeof segments = [];
    segments.forEach((s) => {
      if (s.phraseIdx !== undefined || !s.text.includes(p)) {
        next.push(s);
        return;
      }
      const parts = s.text.split(p);
      parts.forEach((part, i) => {
        if (part) next.push({ text: part });
        if (i < parts.length - 1) next.push({ text: p, phraseIdx: idx });
      });
    });
    segments = next;
  });

  return (
    <div
      style={{
        fontFamily: theme.fontBody,
        fontSize: 28,
        lineHeight: 1.55,
        color: INK,
        whiteSpace: "pre-wrap",
      }}
    >
      {segments.map((seg, i) => {
        if (seg.phraseIdx === undefined || phraseAnimation === "none") {
          return <span key={i}>{seg.text}</span>;
        }
        const start = startFn(seg.phraseIdx);
        const reveal = interpolate(frame, [start, start + 18], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        if (phraseAnimation === "highlight") {
          return (
            <span
              key={i}
              style={{
                background: `linear-gradient(90deg, #f5d54a${"AA"} 0%, #f5d54a${"AA"} ${reveal * 100}%, transparent ${reveal * 100}%)`,
                paddingLeft: 2,
                paddingRight: 2,
              }}
            >
              {seg.text}
            </span>
          );
        }
        // redact
        return (
          <span key={i} style={{ position: "relative" }}>
            <span style={{ visibility: "hidden" }}>{seg.text}</span>
            <span
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                bottom: 0,
                background: "#0a0a0a",
                width: `${reveal * 100}%`,
                boxShadow: "0 0 0 1px #000 inset",
              }}
            />
          </span>
        );
      })}
    </div>
  );
};

const Signature: React.FC<{
  text: string;
  theme: BrandTheme;
  frame: number;
  total: number;
  fps: number;
}> = ({ text, theme, frame, total, fps }) => {
  const start = total - 4 * fps;
  const charsPerSec = 6;
  const chars = Math.max(0, Math.floor((frame - start) * (charsPerSec / fps)));
  const visible = text.slice(0, chars);

  return (
    <div style={{ position: "absolute", bottom: 80, right: 96 }}>
      <div
        style={{
          fontFamily: '"Brush Script MT", "Lucida Handwriting", cursive',
          fontSize: 56,
          color: theme.stampRed ?? "#1a3060",
          fontStyle: "italic",
          letterSpacing: "0.04em",
          minHeight: 80,
          minWidth: 320,
          borderBottom: `1px solid ${INK}`,
          paddingBottom: 6,
        }}
      >
        {visible}
      </div>
      <div
        style={{
          fontSize: 18,
          fontFamily: theme.fontBody,
          color: "#5a4a3a",
          marginTop: 6,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          fontWeight: 600,
        }}
      >
        Signature
      </div>
    </div>
  );
};

// (ClassifiedStamp moved to shared Stamp component — see ./Stamp.tsx)
