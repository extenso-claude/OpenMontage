/**
 * ClockReveal — animated analog clock face that sweeps from 12:00 to a target time.
 *
 * Used for "It was 11:58 PM when..." moments. Optional date label below.
 *
 * @version 0.1.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

export interface ClockRevealProps {
  /** Target time in 24-hour format. e.g. "23:58" for 11:58 PM. */
  targetTime: string;
  /** Date label shown below the clock. e.g. "1929 · October 28th". */
  dateLabel?: string;
  /** Caption above the clock. e.g. "The hour the bell tolled". */
  caption?: string;
  /** Total frames. Default = 5s @ fps. */
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
}

function parseHHMM(s: string): { hours: number; minutes: number } {
  const [h, m] = s.split(":").map((x) => parseInt(x, 10));
  return { hours: h ?? 12, minutes: m ?? 0 };
}

export const ClockReveal: React.FC<ClockRevealProps> = ({
  targetTime,
  dateLabel,
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
  const sweepStart = 12;
  const sweepEnd = total - fadeFrames - 18;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const { hours, minutes } = parseHHMM(targetTime);
  // Hour angle: hours mod 12 = 0..12, plus minutes/60 of an hour
  const targetHourAngle = ((hours % 12) + minutes / 60) * 30;       // 360/12 = 30°/hour
  const targetMinuteAngle = minutes * 6;                            // 360/60 = 6°/min

  const sweepProgress = interpolate(frame, [sweepStart, sweepEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // ease-out cubic
  const eased = 1 - Math.pow(1 - sweepProgress, 3);

  const hourAngle = eased * targetHourAngle;
  // Minute hand spins multiple turns to feel deliberate
  const minuteAngle = eased * (targetMinuteAngle + 720); // +2 full turns

  const showText = sweepProgress > 0.85;
  const textOpacity = interpolate(sweepProgress, [0.85, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const tickAngles = Array.from({ length: 12 }).map((_, i) => i * 30);
  const minuteTickAngles = Array.from({ length: 60 }).map((_, i) => i * 6);

  return (
    <AbsoluteFill style={{ background: theme.bg, opacity }}>
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 36 }}>
        {caption ? (
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontSize: 24,
              color: theme.muted ?? theme.text,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
            }}
          >
            {caption}
          </div>
        ) : null}

        <svg viewBox="-110 -110 220 220" width={720} height={720}>
          {/* outer ring */}
          <circle cx={0} cy={0} r={100} fill="none" stroke={theme.accent} strokeWidth={2} />
          <circle cx={0} cy={0} r={96} fill={`${theme.bg}EE`} stroke="none" />

          {/* minute ticks */}
          {minuteTickAngles.map((a) => (
            <line
              key={`m-${a}`}
              x1={0}
              y1={-92}
              x2={0}
              y2={-88}
              stroke={theme.muted ?? theme.text}
              strokeWidth={0.5}
              transform={`rotate(${a})`}
              opacity={0.5}
            />
          ))}

          {/* hour ticks */}
          {tickAngles.map((a) => (
            <line
              key={`h-${a}`}
              x1={0}
              y1={-94}
              x2={0}
              y2={-82}
              stroke={theme.text}
              strokeWidth={a % 90 === 0 ? 3 : 2}
              transform={`rotate(${a})`}
            />
          ))}

          {/* hour numerals (12, 3, 6, 9 only — clean) */}
          {[
            { n: "XII", x: 0, y: -64 },
            { n: "III", x: 64, y: 6 },
            { n: "VI", x: 0, y: 76 },
            { n: "IX", x: -64, y: 6 },
          ].map((p) => (
            <text
              key={p.n}
              x={p.x}
              y={p.y}
              fontFamily={theme.fontHeading}
              fontSize={14}
              fill={theme.text}
              textAnchor="middle"
              dominantBaseline="middle"
              fontWeight={700}
            >
              {p.n}
            </text>
          ))}

          {/* hour hand */}
          <line
            x1={0}
            y1={6}
            x2={0}
            y2={-50}
            stroke={theme.text}
            strokeWidth={5}
            strokeLinecap="round"
            transform={`rotate(${hourAngle})`}
          />
          {/* minute hand */}
          <line
            x1={0}
            y1={8}
            x2={0}
            y2={-78}
            stroke={theme.accent}
            strokeWidth={3}
            strokeLinecap="round"
            transform={`rotate(${minuteAngle})`}
          />
          {/* center dot */}
          <circle cx={0} cy={0} r={4.5} fill={theme.accent} />
          <circle cx={0} cy={0} r={1.5} fill={theme.bg} />
        </svg>

        {/* Time + date readout (appears as the sweep finishes) */}
        <div style={{ textAlign: "center", opacity: textOpacity }}>
          <div
            style={{
              fontFamily: theme.fontHeading,
              fontWeight: theme.headingWeight ?? 700,
              fontSize: 56,
              color: theme.accent,
              letterSpacing: "0.05em",
            }}
          >
            {showText ? targetTime : ""}
          </div>
          {dateLabel ? (
            <div
              style={{
                fontFamily: theme.fontBody,
                fontSize: 18,
                color: theme.text,
                marginTop: 8,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              {dateLabel}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
