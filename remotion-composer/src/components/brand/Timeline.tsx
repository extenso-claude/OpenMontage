/**
 * Timeline — time-scrubbing visualization with 4 variants.
 *
 *   - horizontal        : left-to-right scrub with year markers and event nodes
 *   - vertical_chapter  : top-to-bottom for long-form chapter dividers
 *   - dynasty           : multiple parallel lifelines
 *   - branching         : single line forks at decision point
 *
 * Beat-synchronization: each event accepts an optional `revealAtSeconds`.
 * If set, the event reveals at that timestamp. If not, events distribute
 * evenly across the available time. Mix-and-match is supported — explicit
 * timestamps win, the rest fill the gaps proportionally.
 *
 * @version 0.2.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export type TimelineVariant =
  | "horizontal"
  | "vertical_chapter"
  | "dynasty"
  | "branching";

export interface TimelineEvent {
  year: string;
  label: string;
  type?: "birth" | "death" | "battle" | "decision" | "milestone" | "fall" | "rise";
  /** When (in seconds from scene start) this event appears. Optional — if absent, distributed evenly. */
  revealAtSeconds?: number;
  /** Optional 1-line description. */
  description?: string;
}

export interface TimelineLifeline {
  name: string;
  /** Start year for this lifeline's track (used to position the line). */
  startYear: string;
  endYear: string;
  events: TimelineEvent[];
  /** Optional accent color override per lifeline. */
  accentColor?: string;
}

export interface BranchOption {
  label: string;
  outcome: string;
  /** "took" path is bolder; "untaken" is dimmer/dashed. */
  taken: boolean;
}

export interface TimelineProps {
  variant: TimelineVariant;

  // Used by horizontal / vertical_chapter / branching
  events?: TimelineEvent[];

  // Used by dynasty
  lifelines?: TimelineLifeline[];

  // Used by branching
  branchPoint?: { year: string; label: string };
  branches?: BranchOption[];

  /** Total frames the component is on screen. Default = 8s @ fps. */
  durationFrames?: number;

  /** Optional title/caption. */
  title?: string;

  theme?: Partial<BrandTheme>;
}

// Compute reveal frame for each event — explicit takes priority, else even distribution.
function computeRevealFrames(
  events: TimelineEvent[],
  fps: number,
  totalFrames: number,
  fadeFrames: number,
): number[] {
  const usable = totalFrames - fadeFrames * 2;
  return events.map((e, i) => {
    if (e.revealAtSeconds !== undefined) {
      return Math.round(e.revealAtSeconds * fps);
    }
    // Distribute evenly over the usable window, starting after the fade-in
    const slot = events.length > 1 ? i / (events.length - 1) : 0.5;
    return fadeFrames + Math.round(slot * usable);
  });
}

export const Timeline: React.FC<TimelineProps> = ({
  variant,
  events = [],
  lifelines = [],
  branchPoint,
  branches = [],
  durationFrames,
  title,
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

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
      }}
    >
      {title ? (
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: theme.headingWeight ?? 700,
            fontSize: 32,
            color: theme.accent,
            letterSpacing: "0.05em",
            marginBottom: 32,
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
      ) : null}

      {variant === "horizontal" ? (
        <Horizontal events={events} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
      {variant === "vertical_chapter" ? (
        <VerticalChapter events={events} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
      {variant === "dynasty" ? (
        <Dynasty lifelines={lifelines} theme={theme} frame={frame} fps={fps} total={total} />
      ) : null}
      {variant === "branching" ? (
        <Branching
          branchPoint={branchPoint}
          branches={branches}
          theme={theme}
          frame={frame}
          fps={fps}
          total={total}
        />
      ) : null}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// horizontal
// ─────────────────────────────────────────────────────────────────────────

const Horizontal: React.FC<{
  events: TimelineEvent[];
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ events, theme, frame, fps, total }) => {
  const reveals = computeRevealFrames(events, fps, total, theme.fadeFrames ?? 36);

  return (
    <div style={{ width: "100%", maxWidth: 1700, position: "relative", height: 320 }}>
      {/* Spine */}
      <div
        style={{
          position: "absolute",
          top: 150,
          left: 40,
          right: 40,
          height: 3,
          background: `linear-gradient(to right, ${theme.accent}66, ${theme.accent}, ${theme.accent}66)`,
        }}
      />
      {events.map((e, i) => {
        const revealFrame = reveals[i] ?? 0;
        const revealed = frame >= revealFrame;
        const scale = interpolate(frame, [revealFrame, revealFrame + 18], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const x = events.length > 1 ? (i / (events.length - 1)) * 100 : 50;
        const above = i % 2 === 0;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `calc(${x}% )`,
              top: 150,
              transform: `translateX(-50%)`,
              opacity: revealed ? 1 : 0,
            }}
          >
            <div
              style={{
                width: 22,
                height: 22,
                background: theme.accent,
                borderRadius: "50%",
                transform: `translate(-11px, -11px) scale(${scale})`,
                boxShadow: `0 0 28px ${theme.accent}AA`,
              }}
            />
            <div
              style={{
                position: "absolute",
                [above ? "bottom" : "top"]: 30,
                left: 0,
                transform: "translateX(-50%)",
                textAlign: "center",
                width: 320,
                opacity: scale,
              }}
            >
              <div
                style={{
                  fontFamily: theme.fontHeading,
                  fontSize: 32,
                  color: theme.accent,
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                }}
              >
                {e.year}
              </div>
              <div
                style={{
                  fontFamily: theme.fontBody,
                  fontSize: 22,
                  color: theme.text,
                  marginTop: 8,
                  lineHeight: 1.35,
                }}
              >
                {e.label}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// vertical_chapter
// ─────────────────────────────────────────────────────────────────────────

const VerticalChapter: React.FC<{
  events: TimelineEvent[];
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ events, theme, frame, fps, total }) => {
  const reveals = computeRevealFrames(events, fps, total, theme.fadeFrames ?? 36);

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 800,
        position: "relative",
        paddingLeft: 60,
        display: "flex",
        flexDirection: "column",
        gap: 24,
      }}
    >
      {/* Spine */}
      <div
        style={{
          position: "absolute",
          top: 8,
          bottom: 8,
          left: 24,
          width: 2,
          background: `linear-gradient(to bottom, ${theme.accent}66, ${theme.accent}, ${theme.accent}33)`,
        }}
      />
      {events.map((e, i) => {
        const revealFrame = reveals[i] ?? 0;
        const slide = interpolate(frame, [revealFrame, revealFrame + 24], [-30, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const opacityE = interpolate(frame, [revealFrame, revealFrame + 18], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <div
            key={i}
            style={{
              position: "relative",
              display: "flex",
              alignItems: "flex-start",
              gap: 16,
              transform: `translateX(${slide}px)`,
              opacity: opacityE,
            }}
          >
            <div
              style={{
                position: "absolute",
                left: -50,
                top: 6,
                width: 16,
                height: 16,
                background: theme.accent,
                borderRadius: "50%",
                border: `3px solid ${theme.bg}`,
                boxShadow: `0 0 0 2px ${theme.accent}, 0 0 16px ${theme.accent}AA`,
              }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontFamily: theme.fontHeading,
                  fontSize: 22,
                  color: theme.accent,
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                }}
              >
                {e.year} — {e.label}
              </div>
              {e.description ? (
                <div
                  style={{
                    fontFamily: theme.fontBody,
                    fontSize: 16,
                    color: theme.text,
                    marginTop: 6,
                    lineHeight: 1.45,
                  }}
                >
                  {e.description}
                </div>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// dynasty
// ─────────────────────────────────────────────────────────────────────────

const Dynasty: React.FC<{
  lifelines: TimelineLifeline[];
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ lifelines, theme, frame, fps, total }) => {
  const fadeFrames = theme.fadeFrames ?? 36;
  // Each lifeline's spine reveals over the first 1.5s, events over the rest
  const spineReveal = interpolate(frame, [fadeFrames, fadeFrames + 36], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 1500,
        display: "flex",
        flexDirection: "column",
        gap: 36,
      }}
    >
      {lifelines.map((life, idx) => {
        const accent = life.accentColor ?? theme.accent;
        const reveals = computeRevealFrames(life.events, fps, total, fadeFrames);
        return (
          <div key={idx} style={{ position: "relative", height: 90 }}>
            <div
              style={{
                position: "absolute",
                top: 4,
                fontFamily: theme.fontHeading,
                fontSize: 18,
                color: accent,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              {life.name}
            </div>
            <div
              style={{
                position: "absolute",
                top: 50,
                left: 0,
                right: 0,
                height: 2,
                background: accent,
                opacity: 0.4,
                transform: `scaleX(${spineReveal})`,
                transformOrigin: "left",
              }}
            />
            {/* Start/end year markers */}
            <div
              style={{
                position: "absolute",
                top: 56,
                left: 0,
                color: theme.muted ?? theme.text,
                fontFamily: theme.fontBody,
                fontSize: 13,
                opacity: spineReveal,
              }}
            >
              {life.startYear}
            </div>
            <div
              style={{
                position: "absolute",
                top: 56,
                right: 0,
                color: theme.muted ?? theme.text,
                fontFamily: theme.fontBody,
                fontSize: 13,
                opacity: spineReveal,
              }}
            >
              {life.endYear}
            </div>
            {life.events.map((e, i) => {
              const revealFrame = reveals[i] ?? 0;
              const x = life.events.length > 1 ? (i + 0.5) / life.events.length : 0.5;
              const scale = interpolate(frame, [revealFrame, revealFrame + 18], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    top: 30,
                    left: `calc(${x * 100}% - 8px)`,
                    width: 16,
                    height: 36,
                    transform: `scale(${scale})`,
                    transformOrigin: "center bottom",
                  }}
                >
                  <div
                    style={{
                      width: 16,
                      height: 16,
                      background: accent,
                      borderRadius: "50%",
                      boxShadow: `0 0 8px ${accent}AA`,
                    }}
                  />
                  <div
                    style={{
                      width: 1,
                      height: 16,
                      background: accent,
                      margin: "0 auto",
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      bottom: -22,
                      left: "50%",
                      transform: "translateX(-50%)",
                      whiteSpace: "nowrap",
                      fontFamily: theme.fontBody,
                      fontSize: 11,
                      color: theme.text,
                      opacity: scale,
                    }}
                  >
                    <span style={{ color: accent, fontWeight: 700 }}>{e.year}</span>{" "}
                    {e.label}
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// branching
// ─────────────────────────────────────────────────────────────────────────

const Branching: React.FC<{
  branchPoint?: { year: string; label: string };
  branches: BranchOption[];
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ branchPoint, branches, theme, frame, total }) => {
  const fadeFrames = theme.fadeFrames ?? 36;
  const spineReveal = interpolate(frame, [fadeFrames, fadeFrames + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const branchReveal = interpolate(
    frame,
    [fadeFrames + 24, total - fadeFrames - 12],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        width: "100%",
        maxWidth: 1200,
        position: "relative",
        height: 360,
      }}
    >
      {/* Pre-branch spine */}
      <div
        style={{
          position: "absolute",
          top: 178,
          left: 0,
          width: "40%",
          height: 3,
          background: theme.accent,
          opacity: 0.85,
          transform: `scaleX(${spineReveal})`,
          transformOrigin: "left",
        }}
      />
      {/* Branch point label */}
      {branchPoint && spineReveal > 0.6 ? (
        <div
          style={{
            position: "absolute",
            top: 130,
            left: "40%",
            transform: "translate(-50%, 0)",
            textAlign: "center",
            fontFamily: theme.fontHeading,
            color: theme.accent,
            opacity: (spineReveal - 0.6) / 0.4,
          }}
        >
          <div style={{ fontSize: 18, letterSpacing: "0.04em" }}>{branchPoint.year}</div>
          <div
            style={{
              fontSize: 14,
              color: theme.text,
              fontFamily: theme.fontBody,
              marginTop: 4,
            }}
          >
            {branchPoint.label}
          </div>
        </div>
      ) : null}
      {/* Branch fork */}
      {branches.map((b, i) => {
        const isUpper = i === 0;
        const yOffset = isUpper ? -90 : 90;
        const branchOpacity = b.taken ? 1 : 0.45;
        const dasharray = b.taken ? "0" : "8 6";
        return (
          <div key={i}>
            <svg
              style={{
                position: "absolute",
                top: 178,
                left: "40%",
                width: "60%",
                height: 200,
                overflow: "visible",
              }}
              viewBox="0 0 600 200"
              preserveAspectRatio="none"
            >
              <path
                d={`M 0,0 Q 200,0 300,${yOffset}`}
                fill="none"
                stroke={theme.accent}
                strokeWidth={3}
                strokeOpacity={branchOpacity * branchReveal}
                strokeDasharray={dasharray}
              />
              <path
                d={`M 300,${yOffset} L 600,${yOffset}`}
                fill="none"
                stroke={theme.accent}
                strokeWidth={3}
                strokeOpacity={branchOpacity * branchReveal}
                strokeDasharray={dasharray}
              />
            </svg>
            <div
              style={{
                position: "absolute",
                top: 178 + yOffset - 30,
                right: 0,
                width: 320,
                opacity: branchReveal * branchOpacity,
                color: theme.text,
                textAlign: "right",
              }}
            >
              <div
                style={{
                  fontFamily: theme.fontHeading,
                  fontSize: 18,
                  color: theme.accent,
                  letterSpacing: "0.04em",
                }}
              >
                {b.label} {b.taken ? "" : "(not taken)"}
              </div>
              <div
                style={{
                  fontFamily: theme.fontBody,
                  fontSize: 14,
                  marginTop: 4,
                  color: theme.text,
                  lineHeight: 1.4,
                }}
              >
                {b.outcome}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
