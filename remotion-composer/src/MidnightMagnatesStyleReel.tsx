/**
 * MidnightMagnatesStyleReel — six-shot motion-design reel demonstrating the
 * Midnight Magnates visual vocabulary. Designed as a reusable shot library:
 * each shot is self-contained and can be lifted into real episodes.
 *
 * Shots:
 *  1. Title sequence       (kinetic typography + gold rule motif)
 *  2. Vault door           (geometric SVG primitives + cool-blue shaft of light)
 *  3. Skyline at midnight  (silhouette + single warm-gold window)
 *  4. Chess hierarchy      (object positioning + long shadows under gold shaft)
 *  5. CLASSIFIED document  (channel-signature redaction + slow stamp slam)
 *  6. Closing observation  (italic serif quote + gold underline draw)
 *
 * Playbook: midnight-magnates.yaml
 *  - 1920×1080 @ 24fps
 *  - Slow noir reveals, scale 0.97 → 1.0, no bouncy easing
 *  - Single shaft of light per scene
 *  - Cream #f5f0e4 text only — never raw white
 *  - 2px black stroke + soft drop shadow on burned-in text
 *  - Stamp red #b41e1e used only for CLASSIFIED
 */
import React from "react";
import {
  AbsoluteFill,
  Series,
  useCurrentFrame,
  interpolate,
  Easing,
} from "remotion";
import mmTheme from "./components/brand/themes/midnight_magnates.json";
import { resolveTheme, BrandTheme } from "./components/brand/theme";

const FPS = 24;
const sec = (s: number) => Math.round(s * FPS);

const SHOT_TITLE = sec(6);
const SHOT_VAULT = sec(7);
const SHOT_SKYLINE = sec(7);
const SHOT_CHESS = sec(7);
const SHOT_CLASSIFIED = sec(8);
const SHOT_QUOTE = sec(9);

export const MIDNIGHT_MAGNATES_REEL_DURATION_FRAMES =
  SHOT_TITLE + SHOT_VAULT + SHOT_SKYLINE + SHOT_CHESS + SHOT_CLASSIFIED + SHOT_QUOTE;

const FADE_IN = 36; // 1.5s entrance per playbook
const FADE_OUT = 36; // 1.5s exit per playbook

// Stroke + shadow string used on every burned-in cream text element.
// 8 offset shadows simulate a 2px black outline (paint-order isn't honored
// for HTML text in Chromium, so we layer offsets); final entry is the soft drop.
const TEXT_STROKE_SHADOW =
  "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000, " +
  "1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000, " +
  "0 4px 14px rgba(0,0,0,0.55)";

// ─────────────────────────────────────────────────────────────────────────
// Shared shot wrapper — handles entrance scale + fade in/out per playbook
// ─────────────────────────────────────────────────────────────────────────
const ShotContainer: React.FC<{
  bg: string;
  duration: number;
  children: React.ReactNode;
}> = ({ bg, duration, children }) => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, FADE_IN], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [duration - FADE_OUT, duration],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const opacity = Math.min(fadeIn, fadeOut);
  const scale = interpolate(frame, [0, FADE_IN], [0.97, 1.0], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <AbsoluteFill
      style={{
        background: bg,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 1 — TITLE SEQUENCE
// ─────────────────────────────────────────────────────────────────────────
const TitleShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();
  const title = "MIDNIGHT MAGNATES";
  const subtitle = "The Quiet Architecture of Power";

  const titleStart = FADE_IN;
  const titleSpread = 30;
  const ruleStart = titleStart + titleSpread + 12;
  const ruleEnd = ruleStart + 30;
  const subStart = ruleEnd + 8;

  const ruleProgress = interpolate(frame, [ruleStart, ruleEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const subOpacity = interpolate(frame, [subStart, subStart + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: 700,
            fontSize: 88,
            color: theme.text,
            letterSpacing: "0.08em",
            textShadow: TEXT_STROKE_SHADOW,
            display: "flex",
          }}
        >
          {title.split("").map((char, i) => {
            const charStart = titleStart + (i / title.length) * titleSpread;
            const o = interpolate(frame, [charStart, charStart + 8], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            return (
              <span key={i} style={{ opacity: o, whiteSpace: "pre" }}>
                {char}
              </span>
            );
          })}
        </div>
        <div
          style={{
            width: 640,
            height: 2,
            background: theme.accent,
            marginTop: 28,
            transform: `scaleX(${ruleProgress})`,
            transformOrigin: "center",
            boxShadow: `0 0 18px ${theme.accent}66`,
          }}
        />
        <div
          style={{
            fontFamily: theme.fontBody,
            fontStyle: "italic",
            fontSize: 32,
            color: theme.text,
            marginTop: 30,
            opacity: subOpacity,
            letterSpacing: "0.04em",
            textShadow: TEXT_STROKE_SHADOW,
          }}
        >
          {subtitle}
        </div>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 2 — VAULT DOOR
// ─────────────────────────────────────────────────────────────────────────
const VaultShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();

  // Slow rotation (15° over the duration)
  const rotation = interpolate(frame, [0, duration], [0, 15], {
    easing: Easing.inOut(Easing.cubic),
  });

  // Cool-blue shaft grows from a center point
  const lightStart = FADE_IN;
  const lightEnd = duration - FADE_OUT;
  const lightRadius = interpolate(frame, [lightStart, lightEnd], [40, 420], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const lightOpacity = interpolate(
    frame,
    [lightStart, lightStart + 30],
    [0, 0.6],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const blueShaft = "#4a6fa5";

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width={1080} height={1080} viewBox="-540 -540 1080 1080">
          <defs>
            <radialGradient id="vaultLight">
              <stop
                offset="0%"
                stopColor={blueShaft}
                stopOpacity={lightOpacity * 1.5}
              />
              <stop
                offset="40%"
                stopColor={blueShaft}
                stopOpacity={lightOpacity * 0.55}
              />
              <stop offset="100%" stopColor={blueShaft} stopOpacity={0} />
            </radialGradient>
          </defs>
          <circle cx={0} cy={0} r={lightRadius} fill="url(#vaultLight)" />
          <g transform={`rotate(${rotation})`}>
            {/* Concentric rings */}
            <circle
              cx={0}
              cy={0}
              r={420}
              fill="none"
              stroke={theme.accent}
              strokeWidth={3}
              opacity={0.85}
            />
            <circle
              cx={0}
              cy={0}
              r={400}
              fill="none"
              stroke={theme.accent}
              strokeWidth={1.5}
              opacity={0.5}
            />
            <circle
              cx={0}
              cy={0}
              r={320}
              fill="none"
              stroke={theme.accent}
              strokeWidth={2}
              opacity={0.7}
            />
            <circle
              cx={0}
              cy={0}
              r={240}
              fill="none"
              stroke={theme.accent}
              strokeWidth={1.5}
              opacity={0.55}
            />
            <circle
              cx={0}
              cy={0}
              r={140}
              fill="none"
              stroke={theme.accent}
              strokeWidth={1.2}
              opacity={0.6}
            />
            {/* Radial spokes */}
            {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
              const r = (deg * Math.PI) / 180;
              return (
                <line
                  key={deg}
                  x1={0}
                  y1={0}
                  x2={Math.cos(r) * 420}
                  y2={Math.sin(r) * 420}
                  stroke={theme.accent}
                  strokeWidth={1.5}
                  opacity={0.32}
                />
              );
            })}
            {/* Bolt heads */}
            {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map(
              (deg) => {
                const r = (deg * Math.PI) / 180;
                return (
                  <circle
                    key={deg}
                    cx={Math.cos(r) * 410}
                    cy={Math.sin(r) * 410}
                    r={5}
                    fill={theme.accent}
                    opacity={0.75}
                  />
                );
              }
            )}
            {/* Center handle */}
            <circle
              cx={0}
              cy={0}
              r={40}
              fill={theme.bg}
              stroke={theme.accent}
              strokeWidth={2}
            />
            <circle cx={0} cy={0} r={6} fill={theme.accent} />
          </g>
        </svg>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 3 — SKYLINE AT MIDNIGHT
// ─────────────────────────────────────────────────────────────────────────
const SkylineShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();

  // Silhouette materializes from shadow
  const silOpacity = interpolate(frame, [FADE_IN, FADE_IN + 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Single warm-gold window switches on at 50% mark
  const windowStart = Math.floor(duration * 0.5);
  const windowOpacity = interpolate(
    frame,
    [windowStart, windowStart + 18],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  // Subtle warm flicker (single soft pulse, not strobing)
  const flicker = 0.88 + 0.12 * Math.sin((frame - windowStart) * 0.06);

  const buildings = [
    { x: 0, w: 180, h: 360 },
    { x: 180, w: 140, h: 480 },
    { x: 320, w: 100, h: 280 },
    { x: 420, w: 200, h: 580 },
    { x: 620, w: 120, h: 320 },
    { x: 740, w: 160, h: 460 },
    { x: 900, w: 140, h: 380 },
    { x: 1040, w: 220, h: 640 },
    { x: 1260, w: 140, h: 360 },
    { x: 1400, w: 180, h: 500 },
    { x: 1580, w: 120, h: 300 },
    { x: 1700, w: 220, h: 560 },
  ];
  const lit = buildings[3];
  const winX = lit.x + lit.w / 2 - 8;
  const winY = 1080 - lit.h + 110;

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill>
        <svg
          width={1920}
          height={1080}
          style={{ position: "absolute", inset: 0 }}
        >
          <defs>
            <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={theme.bg} />
              <stop offset="100%" stopColor="#0c1220" />
            </linearGradient>
            <radialGradient id="winGlow">
              <stop offset="0%" stopColor={theme.accent} stopOpacity={1} />
              <stop offset="100%" stopColor={theme.accent} stopOpacity={0} />
            </radialGradient>
          </defs>
          <rect x={0} y={0} width={1920} height={1080} fill="url(#sky)" />

          {/* Faint stars */}
          {[
            [120, 80],
            [340, 130],
            [580, 60],
            [840, 110],
            [1180, 90],
            [1480, 70],
            [1780, 130],
            [220, 200],
            [1620, 220],
          ].map(([x, y], i) => (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={1.4}
              fill={theme.text}
              opacity={0.4 * silOpacity}
            />
          ))}

          {/* Buildings */}
          {buildings.map((b, i) => (
            <g key={i} opacity={silOpacity}>
              <rect
                x={b.x}
                y={1080 - b.h}
                width={b.w}
                height={b.h}
                fill="#02050b"
              />
              <rect
                x={b.x}
                y={1080 - b.h}
                width={2}
                height={b.h}
                fill={theme.muted}
                opacity={0.18}
              />
            </g>
          ))}

          {/* Lit window glow */}
          <circle
            cx={winX + 8}
            cy={winY + 12}
            r={80 * flicker}
            fill="url(#winGlow)"
            opacity={windowOpacity * 0.65}
          />
          <rect
            x={winX}
            y={winY}
            width={16}
            height={26}
            fill={theme.accent}
            opacity={windowOpacity * flicker}
          />

          {/* Foreground street line */}
          <rect
            x={0}
            y={1075}
            width={1920}
            height={5}
            fill="#000"
            opacity={silOpacity * 0.8}
          />
        </svg>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 4 — CHESS HIERARCHY
// ─────────────────────────────────────────────────────────────────────────
const ChessShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();

  const boardOpacity = interpolate(frame, [FADE_IN, FADE_IN + 36], [0, 0.22], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lightOpacity = interpolate(frame, [60, 130], [0, 0.5], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pieces = [
    { name: "king", cx: 960, cy: 720, height: 220, slideStart: 36, fromX: 0 },
    {
      name: "queen",
      cx: 1180,
      cy: 720,
      height: 180,
      slideStart: 60,
      fromX: 220,
    },
    {
      name: "pawn1",
      cx: 760,
      cy: 760,
      height: 110,
      slideStart: 84,
      fromX: -180,
    },
    {
      name: "pawn2",
      cx: 1380,
      cy: 760,
      height: 110,
      slideStart: 84,
      fromX: 180,
    },
  ];

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill>
        <svg
          width={1920}
          height={1080}
          style={{ position: "absolute", inset: 0 }}
        >
          <defs>
            <linearGradient id="chessLight" x1="0" y1="0" x2="0.6" y2="1">
              <stop
                offset="0%"
                stopColor={theme.accent}
                stopOpacity={0.45 * lightOpacity}
              />
              <stop
                offset="100%"
                stopColor={theme.accent}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

          {/* Single shaft of warm gold light from upper-left */}
          <polygon
            points="600,0 1000,0 1300,1080 800,1080"
            fill="url(#chessLight)"
          />

          {/* Faint chessboard (perspective trapezoid) */}
          <g opacity={boardOpacity}>
            <polygon
              points="500,820 1420,820 1500,920 420,920"
              fill="#0c1220"
              stroke={theme.muted}
              strokeWidth={1}
            />
            {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <line
                key={i}
                x1={500 + (i * 920) / 8}
                y1={820}
                x2={420 + (i * 1080) / 8}
                y2={920}
                stroke={theme.muted}
                strokeWidth={0.6}
              />
            ))}
          </g>

          {/* Pieces */}
          {pieces.map((p) => {
            const slide = interpolate(
              frame,
              [p.slideStart, p.slideStart + 36],
              [0, 1],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.cubic),
              }
            );
            const x = p.cx + p.fromX * (1 - slide);
            const opacity = slide;
            const shadowLength = p.height * 1.9;

            return (
              <g key={p.name} opacity={opacity}>
                {/* Long shadow stretched right (light from upper-left) */}
                <polygon
                  points={`${x - 25},${p.cy + 8} ${x + 25},${p.cy + 8} ${
                    x + 25 + shadowLength
                  },${p.cy + 30} ${x - 25 + shadowLength},${p.cy + 30}`}
                  fill="#000"
                  opacity={0.6}
                />

                {p.name === "king" && (
                  <>
                    <rect
                      x={x - 32}
                      y={p.cy - p.height + 50}
                      width={64}
                      height={p.height - 50}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.6}
                    />
                    <ellipse
                      cx={x}
                      cy={p.cy - p.height + 50}
                      rx={44}
                      ry={14}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.6}
                    />
                    {/* Crown cross */}
                    <rect
                      x={x - 3}
                      y={p.cy - p.height - 10}
                      width={6}
                      height={32}
                      fill={theme.accent}
                    />
                    <rect
                      x={x - 13}
                      y={p.cy - p.height + 5}
                      width={26}
                      height={6}
                      fill={theme.accent}
                    />
                  </>
                )}

                {p.name === "queen" && (
                  <>
                    <rect
                      x={x - 28}
                      y={p.cy - p.height + 40}
                      width={56}
                      height={p.height - 40}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.5}
                    />
                    <ellipse
                      cx={x}
                      cy={p.cy - p.height + 40}
                      rx={38}
                      ry={12}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.5}
                    />
                    {[-20, -10, 0, 10, 20].map((dx, i) => (
                      <polygon
                        key={i}
                        points={`${x + dx - 3},${p.cy - p.height + 28} ${
                          x + dx + 3
                        },${p.cy - p.height + 28} ${x + dx},${
                          p.cy - p.height + 6
                        }`}
                        fill={theme.accent}
                      />
                    ))}
                  </>
                )}

                {(p.name === "pawn1" || p.name === "pawn2") && (
                  <>
                    <rect
                      x={x - 18}
                      y={p.cy - p.height + 28}
                      width={36}
                      height={p.height - 28}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.2}
                    />
                    <circle
                      cx={x}
                      cy={p.cy - p.height + 26}
                      r={20}
                      fill="#02050b"
                      stroke={theme.accent}
                      strokeWidth={1.2}
                    />
                  </>
                )}
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 5 — CLASSIFIED DOCUMENT
// ─────────────────────────────────────────────────────────────────────────
const ClassifiedShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();

  const pageOpacity = interpolate(frame, [FADE_IN, FADE_IN + 36], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const linesStart = FADE_IN + 36;
  const redactStart = linesStart + 30;
  const stampStart = Math.floor(duration * 0.62);

  const stampScale = interpolate(
    frame,
    [stampStart, stampStart + 14],
    [1.5, 1.0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );
  const stampOpacity = interpolate(
    frame,
    [stampStart, stampStart + 8],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const lines = [
    { y: 240, w: 540, redact: false, redactX: 0, redactW: 0 },
    { y: 282, w: 580, redact: true, redactX: 60, redactW: 380 },
    { y: 324, w: 560, redact: false, redactX: 0, redactW: 0 },
    { y: 366, w: 600, redact: true, redactX: 0, redactW: 460 },
    { y: 408, w: 540, redact: false, redactX: 0, redactW: 0 },
    { y: 450, w: 580, redact: true, redactX: 120, redactW: 320 },
    { y: 492, w: 560, redact: false, redactX: 0, redactW: 0 },
    { y: 534, w: 540, redact: false, redactX: 0, redactW: 0 },
    { y: 576, w: 600, redact: true, redactX: 40, redactW: 460 },
    { y: 618, w: 560, redact: false, redactX: 0, redactW: 0 },
  ];

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width={1920} height={1080}>
          {/* Page shadow */}
          <ellipse
            cx={960}
            cy={950}
            rx={400}
            ry={20}
            fill="#000"
            opacity={pageOpacity * 0.55}
          />

          <g
            transform={`translate(960 540) rotate(-2) translate(-360 -400)`}
            opacity={pageOpacity}
          >
            {/* Cream paper page (opaque per playbook alpha rule) */}
            <rect x={0} y={0} width={720} height={800} fill="#e8e0c8" />

            {/* Header */}
            <text
              x={40}
              y={80}
              fontFamily="Courier New, monospace"
              fontSize={26}
              fontWeight={700}
              fill="#2a2418"
              letterSpacing="0.18em"
            >
              MEMO · INTERNAL CIRCULATION
            </text>
            <line
              x1={40}
              y1={104}
              x2={680}
              y2={104}
              stroke="#2a2418"
              strokeWidth={1.5}
            />
            <text
              x={40}
              y={146}
              fontFamily="Courier New, monospace"
              fontSize={18}
              fill="#3a3122"
            >
              DATE: 1815 / 06 / 18
            </text>
            <text
              x={40}
              y={172}
              fontFamily="Courier New, monospace"
              fontSize={18}
              fill="#3a3122"
            >
              SUBJECT: WATERLOO — DISPATCH STATUS
            </text>

            {/* Body lines */}
            {lines.map((ln, i) => {
              const lineFrame = linesStart + i * 4;
              const lineO = interpolate(
                frame,
                [lineFrame, lineFrame + 12],
                [0, 1],
                { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
              );
              let redactW = 0;
              if (ln.redact) {
                const rs = redactStart + i * 6;
                redactW = interpolate(frame, [rs, rs + 18], [0, ln.redactW], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.out(Easing.cubic),
                });
              }
              return (
                <g key={i} opacity={lineO}>
                  <rect
                    x={40}
                    y={ln.y}
                    width={ln.w}
                    height={14}
                    fill="#3a3122"
                    opacity={0.4}
                  />
                  {ln.redact && (
                    <rect
                      x={40 + ln.redactX}
                      y={ln.y - 4}
                      width={redactW}
                      height={22}
                      fill="#0a0a0a"
                    />
                  )}
                </g>
              );
            })}

            {/* CLASSIFIED stamp — channel-signature red, used sparingly */}
            <g
              transform={`translate(420 600) rotate(8) scale(${stampScale}) translate(-150 -50)`}
              opacity={stampOpacity}
            >
              <rect
                x={0}
                y={0}
                width={300}
                height={100}
                fill="none"
                stroke="#b41e1e"
                strokeWidth={6}
              />
              <rect
                x={8}
                y={8}
                width={284}
                height={84}
                fill="none"
                stroke="#b41e1e"
                strokeWidth={2}
              />
              <text
                x={150}
                y={68}
                fontFamily="Courier New, monospace"
                fontSize={48}
                fontWeight={900}
                fill="#b41e1e"
                textAnchor="middle"
                letterSpacing="0.15em"
              >
                CLASSIFIED
              </text>
            </g>
          </g>
        </svg>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// SHOT 6 — CLOSING OBSERVATION
// ─────────────────────────────────────────────────────────────────────────
const QuoteShot: React.FC<{ theme: BrandTheme; duration: number }> = ({
  theme,
  duration,
}) => {
  const frame = useCurrentFrame();

  const quoteO = interpolate(frame, [FADE_IN, FADE_IN + 48], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const underlineStart = FADE_IN + 64;
  const underlineProg = interpolate(
    frame,
    [underlineStart, underlineStart + 36],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    }
  );
  const markStart = underlineStart + 52;
  const markO = interpolate(frame, [markStart, markStart + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <ShotContainer bg={theme.bg} duration={duration}>
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontStyle: "italic",
            fontSize: 56,
            color: theme.text,
            opacity: quoteO,
            textAlign: "center",
            maxWidth: 1200,
            lineHeight: 1.4,
            letterSpacing: "0.01em",
            textShadow: TEXT_STROKE_SHADOW,
          }}
        >
          “Power is what does not need to announce itself.”
        </div>
        <div
          style={{
            width: 280,
            height: 1.5,
            background: theme.accent,
            marginTop: 40,
            transform: `scaleX(${underlineProg})`,
            transformOrigin: "center",
            boxShadow: `0 0 14px ${theme.accent}66`,
          }}
        />
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: 700,
            fontSize: 18,
            color: theme.muted,
            marginTop: 32,
            letterSpacing: "0.32em",
            opacity: markO,
          }}
        >
          MIDNIGHT MAGNATES
        </div>
      </AbsoluteFill>
    </ShotContainer>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────────────
export const MidnightMagnatesStyleReel: React.FC = () => {
  const theme = resolveTheme(mmTheme as Partial<BrandTheme>);
  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <Series>
        <Series.Sequence durationInFrames={SHOT_TITLE}>
          <TitleShot theme={theme} duration={SHOT_TITLE} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SHOT_VAULT}>
          <VaultShot theme={theme} duration={SHOT_VAULT} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SHOT_SKYLINE}>
          <SkylineShot theme={theme} duration={SHOT_SKYLINE} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SHOT_CHESS}>
          <ChessShot theme={theme} duration={SHOT_CHESS} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SHOT_CLASSIFIED}>
          <ClassifiedShot theme={theme} duration={SHOT_CLASSIFIED} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={SHOT_QUOTE}>
          <QuoteShot theme={theme} duration={SHOT_QUOTE} />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
