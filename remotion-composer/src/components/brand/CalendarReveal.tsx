/**
 * CalendarReveal — animated month grid with a target date circled.
 *
 * Renders a stylized calendar page (month + year), draws a circle around the
 * target day, optionally highlights additional supporting days. Brand-themed
 * paper texture via subtle gradient.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface CalendarRevealProps {
  /** Month name (e.g. "October"). */
  month: string;
  /** Year label (e.g. "1929"). */
  year: string | number;
  /** Day of month to circle (1–31). */
  targetDay: number;
  /** Day-of-week the 1st falls on (0 = Sunday, 6 = Saturday). Default 0. */
  firstDayOfWeek?: number;
  /** Total days in this month. Default 31. */
  daysInMonth?: number;
  /** Additional days that should be marked but not circled. */
  supportingDays?: number[];
  /** Caption above the calendar. */
  caption?: string;
  /** Total frames. Default = 5s @ fps. */
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

const WEEKDAY_LABELS = ["S", "M", "T", "W", "T", "F", "S"];

export const CalendarReveal: React.FC<CalendarRevealProps> = ({
  month,
  year,
  targetDay,
  firstDayOfWeek = 0,
  daysInMonth = 31,
  supportingDays = [],
  caption,
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

  // Header reveal
  const headerOpacity = interpolate(frame, [4, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Grid fill — each day appears with stagger
  const gridStart = 18;
  const gridDuration = Math.max(48, total - fadeFrames - 30);
  // Circle reveal happens after grid fills
  const circleStart = gridStart + gridDuration - 18;
  const circleProgress = interpolate(frame, [circleStart, circleStart + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Build week rows
  const cells: Array<number | null> = [];
  for (let i = 0; i < firstDayOfWeek; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  const rows: Array<Array<number | null>> = [];
  for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7));

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity }}>
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 24 }}>
        {caption ? (
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontSize: 22,
              color: theme.muted ?? theme.text,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              opacity: headerOpacity,
            }}
          >
            {caption}
          </div>
        ) : null}

        <div
          style={{
            background: `linear-gradient(180deg, ${theme.bg} 0%, ${theme.muted}22 100%)`,
            border: `2px solid ${theme.accent}`,
            padding: 48,
            width: 920,
            boxShadow: `0 16px 48px rgba(0,0,0,0.6)`,
          }}
        >
          {/* Month + year header */}
          <div
            style={{
              textAlign: "center",
              marginBottom: 32,
              borderBottom: `1px solid ${theme.accent}55`,
              paddingBottom: 18,
              opacity: headerOpacity,
            }}
          >
            <div
              style={{
                fontFamily: theme.fontHeading,
                fontWeight: theme.headingWeight ?? 700,
                fontSize: 56,
                color: theme.accent,
                letterSpacing: "0.04em",
              }}
            >
              {month}
            </div>
            <div
              style={{
                fontFamily: theme.fontBody,
                fontSize: 26,
                color: theme.text,
                letterSpacing: "0.18em",
                marginTop: 6,
              }}
            >
              {year}
            </div>
          </div>

          {/* Weekday header */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 8, marginBottom: 12, opacity: headerOpacity }}>
            {WEEKDAY_LABELS.map((d, i) => (
              <div
                key={i}
                style={{
                  textAlign: "center",
                  fontFamily: theme.fontBody,
                  fontSize: 18,
                  color: theme.muted ?? theme.text,
                  letterSpacing: "0.18em",
                }}
              >
                {d}
              </div>
            ))}
          </div>

          {/* Day grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 8 }}>
            {cells.map((day, i) => {
              if (day === null) return <div key={`e-${i}`} />;
              const cellRevealStart = gridStart + (i / cells.length) * gridDuration * 0.6;
              const cellOpacity = interpolate(frame, [cellRevealStart, cellRevealStart + 12], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              const isTarget = day === targetDay;
              const isSupporting = supportingDays.includes(day);
              return (
                <div
                  key={`d-${i}`}
                  style={{
                    position: "relative",
                    aspectRatio: "1 / 1",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: theme.fontBody,
                    fontSize: 26,
                    color: isTarget ? theme.accent : theme.text,
                    fontWeight: isTarget ? 700 : 400,
                    opacity: cellOpacity,
                  }}
                >
                  {isSupporting ? (
                    <div
                      style={{
                        position: "absolute",
                        inset: 4,
                        background: `${theme.accent}22`,
                        border: `1px solid ${theme.accent}55`,
                      }}
                    />
                  ) : null}
                  {isTarget ? (
                    <svg
                      viewBox="0 0 100 100"
                      style={{ position: "absolute", inset: -2, pointerEvents: "none" }}
                    >
                      <circle
                        cx={50}
                        cy={50}
                        r={42}
                        fill="none"
                        stroke={theme.accent}
                        strokeWidth={4}
                        strokeDasharray="270"
                        strokeDashoffset={(1 - circleProgress) * 270}
                        strokeLinecap="round"
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                  ) : null}
                  <span style={{ position: "relative", zIndex: 1 }}>{day}</span>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
