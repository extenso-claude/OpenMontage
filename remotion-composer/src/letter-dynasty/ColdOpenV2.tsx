/**
 * Letter Dynasty — Cold Open (Approach B: Parallax Canvas Pan).
 *
 * 13 beats over 103.47s including a 14.4s sleep-network CTA tail.
 * The master canvas (bg/cold-open-trading-floor-wide.svg, 1707x1024) sits
 * behind every beat; a virtual camera glides across it as the narration
 * progresses. Characters/events composite on top per beat.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { MM, MMSvg, svgLib } from "./MMSvg";
import {
  Beat,
  BeatSpec,
  DustParticles,
  FilmGrain,
  FPS,
  LightShaftAcross,
  PeriodTitle,
  Plate,
  TEXT_STROKE,
  Vignette,
  ease,
  easeOut,
  parallax,
  useBeatFrame,
  useBeatProgress,
} from "./beat-helpers";

const COLD_OPEN_DURATION_S = 103.47;
export const LETTER_COLD_OPEN_V2_DURATION_FRAMES = Math.ceil(
  COLD_OPEN_DURATION_S * FPS
);

const BEATS: Record<string, BeatSpec> = {
  CO1: { id: "CO-01", start: 0.0, end: 8.12 },
  CO2: { id: "CO-02", start: 8.12, end: 15.76 },
  CO3: { id: "CO-03", start: 15.76, end: 25.46 },
  CO4: { id: "CO-04", start: 26.02, end: 33.22 },
  CO5: { id: "CO-05", start: 34.14, end: 43.16 },
  CO6: { id: "CO-06", start: 43.86, end: 51.0 },
  CO7: { id: "CO-07", start: 51.0, end: 58.22 },
  CO8: { id: "CO-08", start: 59.0, end: 66.7 },
  CO9: { id: "CO-09", start: 66.7, end: 73.22 },
  CO10: { id: "CO-10", start: 73.22, end: 80.28 },
  CO11: { id: "CO-11", start: 80.28, end: 88.5 },
  CTA1: { id: "CO-12-CTA", start: 88.5, end: 95.78 },
  CTA2: { id: "CO-13-CTA", start: 95.78, end: 102.92 },
};

/**
 * Master parallax canvas — the trading floor wide vista.
 * Camera glides left-to-right across it from beat CO-01 through CO-11.
 * The pan offset is a function of overall frame position within the
 * 0-88.5s narrative section.
 */
const MasterCanvas: React.FC<{ visible: boolean }> = ({ visible }) => {
  const frame = useCurrentFrame();
  const narrativeEnd = 88.5 * FPS;
  // 0->1 across narrative; pan -25% to +25% of viewport
  const t = Math.max(0, Math.min(1, frame / narrativeEnd));
  const panX = interpolate(t, [0, 1], [200, -400], { easing: ease });
  const dollyScale = interpolate(t, [0, 1], [1.05, 1.18], { easing: ease });
  return (
    <AbsoluteFill
      style={{
        opacity: visible ? 1 : 0,
        transform: `translateX(${panX}px) scale(${dollyScale})`,
      }}
    >
      <MMSvg
        src={svgLib("bg/cold-open-trading-floor-wide.svg")}
        mode="ink-cream"
        preserveAspectRatio="xMidYMid slice"
      />
    </AbsoluteFill>
  );
};

// ── CO-01: Establishing wide of trading floor ─────────────────────────────
const Beat1: React.FC = () => {
  const f = useBeatFrame(BEATS.CO1);
  const p = useBeatProgress(BEATS.CO1);
  return (
    <Beat spec={BEATS.CO1}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.8} />
      <DustParticles frame={f} count={30} intensity={0.25} />
      <LightShaftAcross frame={f} intensity={0.3 + p * 0.15} />
    </Beat>
  );
};

// ── CO-02: Brokers turn heads / Nathan close-up ───────────────────────────
const Beat2: React.FC = () => {
  const f = useBeatFrame(BEATS.CO2);
  const p = useBeatProgress(BEATS.CO2);
  // First half: brokers row visible; second half: zoom to Nathan
  const nathanScale = interpolate(p, [0.4, 1], [0.6, 1.1], { easing: ease });
  const nathanOpacity = interpolate(p, [0.35, 0.6], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.CO2}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.78} />
      {/*  Broker row, lower half */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingBottom: "10%" }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${15 + i * 18}%`,
              bottom: "10%",
              width: "10%",
              height: "32%",
              opacity: 0.7,
              transform: `translate(0, ${Math.sin((f + i * 30) * 0.1) * 3}px)`,
            }}
          >
            <MMSvg src={svgLib("lib/broker-silhouette.svg")} mode="silhouette" />
          </div>
        ))}
      </AbsoluteFill>
      {/*  Nathan zoom-in */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          opacity: nathanOpacity,
        }}
      >
        <div
          style={{
            width: "26%",
            height: "70%",
            transform: `scale(${nathanScale})`,
          }}
        >
          <MMSvg src={svgLib("lib/nathan-rothschild-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.4} />
    </Beat>
  );
};

// ── CO-03: "selling quietly..." — bond papers slide out ───────────────────
const Beat3: React.FC = () => {
  const f = useBeatFrame(BEATS.CO3);
  const p = useBeatProgress(BEATS.CO3);
  return (
    <Beat spec={BEATS.CO3}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.75} />
      {/*  Nathan center-left */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: "22%",
            height: "65%",
            transform: "translate(-25%, 0)",
          }}
        >
          <MMSvg src={svgLib("lib/nathan-rothschild-portrait.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      {/*  Bond papers slide right one per ~1.5s of beat */}
      {[0, 1, 2, 3, 4].map((i) => {
        const startP = 0.35 + i * 0.13;
        const localP = Math.max(0, Math.min(1, (p - startP) / 0.4));
        const x = interpolate(localP, [0, 1], [-100, 600 + i * 40], { easing: ease });
        const opacity = interpolate(localP, [0, 0.1, 0.85, 1.0], [0, 1, 1, 0.6]);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: "45%",
              top: `${30 + i * 6}%`,
              width: "15%",
              height: "12%",
              transform: `translate(${x}px, 0) rotate(${(i - 2) * 4}deg)`,
              opacity,
            }}
          >
            <MMSvg src={svgLib("unique/bond-paper-consols.svg")} mode="navy-cream" />
          </div>
        );
      })}
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── CO-04: Bond closeup with failed rally arrow ───────────────────────────
const Beat4: React.FC = () => {
  const f = useBeatFrame(BEATS.CO4);
  const p = useBeatProgress(BEATS.CO4);
  // Arrow tries to rise then falls
  const arrowY = interpolate(
    p,
    [0, 0.35, 0.55, 1.0],
    [50, -40, -50, 80],
    { easing: ease }
  );
  const arrowOpacity = interpolate(p, [0.1, 0.25, 0.85, 1.0], [0, 1, 1, 0.3]);
  return (
    <Beat spec={BEATS.CO4}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.78} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "40%", height: "55%" }}>
          <MMSvg src={svgLib("unique/bond-paper-consols.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      {/*  Failed rally arrow (procedural triangle) */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          transform: `translate(0, ${arrowY}px)`,
          opacity: arrowOpacity,
        }}
      >
        <div
          style={{
            width: 0,
            height: 0,
            borderLeft: "26px solid transparent",
            borderRight: "26px solid transparent",
            borderBottom: `42px solid ${MM.gold}`,
            opacity: 0.85,
            filter: "drop-shadow(0 0 18px #c9a84c)",
          }}
        />
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── CO-05: Panic + Wellington thought + cascade sell ──────────────────────
const Beat5: React.FC = () => {
  const f = useBeatFrame(BEATS.CO5);
  const p = useBeatProgress(BEATS.CO5);
  // 0-0.33 panic stagger; 0.33-0.55 Wellington fades up; 0.55-1 papers fly
  const wellingtonOpacity = interpolate(p, [0.3, 0.5, 0.85, 1], [0, 0.55, 0.55, 0]);
  return (
    <Beat spec={BEATS.CO5}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.8} />
      {/*  Panicked brokers — staggered sway */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "center", paddingBottom: "8%" }}>
        {[0, 1, 2, 3, 4].map((i) => {
          const sway = Math.sin((f + i * 11) * 0.25) * (6 + p * 12);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${10 + i * 17}%`,
                bottom: "8%",
                width: "12%",
                height: "38%",
                transform: `translate(${sway}px, ${Math.abs(sway) * 0.4}px)`,
              }}
            >
              <MMSvg src={svgLib("lib/broker-silhouette.svg")} mode="silhouette" />
            </div>
          );
        })}
      </AbsoluteFill>
      {/*  Wellington fades up center */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          opacity: wellingtonOpacity,
        }}
      >
        <div style={{ width: "32%", height: "75%" }}>
          <MMSvg src={svgLib("lib/wellington-silhouette.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

// ── CO-06: Market collapse — chart drops fall fall fall ───────────────────
const Beat6: React.FC = () => {
  const f = useBeatFrame(BEATS.CO6);
  const p = useBeatProgress(BEATS.CO6);
  // Three drop steps at p ≈ 0.05, 0.30, 0.55
  const stops = [0.05, 0.3, 0.55];
  const yAt = (px: number): number => {
    let y = 100;
    for (const s of stops) {
      if (px >= s) y -= 70;
    }
    // Smooth between stops
    for (const s of stops) {
      const mid = s + 0.05;
      if (px > s && px < mid) {
        y += interpolate(px, [s, mid], [70, 0], { easing: easeOut });
      }
    }
    return y;
  };
  const lineY = yAt(p);
  return (
    <Beat spec={BEATS.CO6}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.75} />
      {/*  Procedural chart line (single dropping line) */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width="60%" height="60%" viewBox="0 0 600 600">
          <defs>
            <filter id="glowRed">
              <feGaussianBlur stdDeviation="4" />
            </filter>
          </defs>
          <polyline
            points={`50,${100} 200,${100} 200,${100 + (lineY < 100 ? 0 : 0)} 250,${
              100 + Math.max(0, 70 * (p > 0.05 ? 1 : 0))
            } 350,${
              100 + Math.max(0, 140 * (p > 0.3 ? 1 : 0))
            } 450,${
              100 + Math.max(0, 210 * (p > 0.55 ? 1 : 0))
            } 550,${100 + Math.max(0, 210 * (p > 0.55 ? 1 : 0))}`}
            fill="none"
            stroke={MM.red}
            strokeWidth={6}
            filter="url(#glowRed)"
          />
        </svg>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── CO-07: Agents emerge from shadow ──────────────────────────────────────
const Beat7: React.FC = () => {
  const f = useBeatFrame(BEATS.CO7);
  const p = useBeatProgress(BEATS.CO7);
  return (
    <Beat spec={BEATS.CO7}>
      <Plate />
      <MasterCanvas visible />
      <Vignette intensity={0.8} />
      {/*  Agents fade in from corners */}
      {[
        { left: "12%", bottom: "12%", w: "10%", h: "32%", delay: 0.1 },
        { left: "32%", bottom: "10%", w: "10%", h: "30%", delay: 0.25 },
        { left: "55%", bottom: "12%", w: "10%", h: "32%", delay: 0.4 },
        { left: "75%", bottom: "10%", w: "10%", h: "30%", delay: 0.55 },
      ].map((a, i) => {
        const localP = Math.max(0, Math.min(1, (p - a.delay) / 0.3));
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: a.left,
              bottom: a.bottom,
              width: a.w,
              height: a.h,
              opacity: localP,
              transform: `translateY(${(1 - localP) * 30}px)`,
            }}
          >
            <MMSvg src={svgLib("unique/rothschild-agent-anonymous.svg")} mode="silhouette" />
          </div>
        );
      })}
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── CO-08: Agents collecting + transition to city ─────────────────────────
const Beat8: React.FC = () => {
  const f = useBeatFrame(BEATS.CO8);
  const p = useBeatProgress(BEATS.CO8);
  // Pickup motion + transition to gloomy rooftops bg in second half
  const cityOpacity = interpolate(p, [0.5, 1.0], [0, 0.7], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.CO8}>
      <Plate />
      <MasterCanvas visible={p < 0.6} />
      <AbsoluteFill style={{ opacity: cityOpacity }}>
        <MMSvg src={svgLib("bg/london-rooftops-gloomy.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.8} />
      {/*  Agents picking up papers in foreground */}
      {[
        { left: "20%", bottom: "10%" },
        { left: "60%", bottom: "8%" },
      ].map((a, i) => {
        const bob = Math.sin((f + i * 20) * 0.15) * 4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: a.left,
              bottom: a.bottom,
              width: "12%",
              height: "35%",
              opacity: 1 - cityOpacity,
              transform: `translate(0, ${bob}px)`,
            }}
          >
            <MMSvg src={svgLib("unique/rothschild-agent-anonymous.svg")} mode="silhouette" />
          </div>
        );
      })}
    </Beat>
  );
};

// ── CO-09: Gloomy London + courier arriving at Whitehall ──────────────────
const Beat9: React.FC = () => {
  const f = useBeatFrame(BEATS.CO9);
  const p = useBeatProgress(BEATS.CO9);
  const drift = -parallax(f, 14);
  const courierX = interpolate(p, [0.45, 0.95], [-1500, -200], { easing: ease });
  return (
    <Beat spec={BEATS.CO9}>
      <Plate />
      <AbsoluteFill style={{ transform: `translate(${drift}px, 0)` }}>
        <MMSvg src={svgLib("bg/london-rooftops-gloomy.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.78} />
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "flex-end" }}>
        <div
          style={{
            width: "20%",
            height: "30%",
            transform: `translate(${courierX}px, -40px)`,
          }}
        >
          <MMSvg src={svgLib("lib/courier-rider-horse.svg")} mode="silhouette" />
        </div>
      </AbsoluteFill>
      <DustParticles frame={f} count={20} intensity={0.4} />
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── CO-10: Whitehall dawn + letter on table + candle ──────────────────────
const Beat10: React.FC = () => {
  const f = useBeatFrame(BEATS.CO10);
  const p = useBeatProgress(BEATS.CO10);
  const letterY = interpolate(p, [0.3, 0.55], [-60, 0], { easing: easeOut });
  const letterOpacity = interpolate(p, [0.25, 0.5], [0, 1], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.CO10}>
      <Plate />
      <MMSvg src={svgLib("bg/whitehall-dawn.svg")} mode="ink-cream" />
      <Vignette intensity={0.7} />
      {/*  Letter falls onto frame */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "flex-end",
          paddingBottom: "8%",
          opacity: letterOpacity,
        }}
      >
        <div
          style={{
            width: "28%",
            height: "28%",
            transform: `translate(0, ${letterY}px)`,
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      {/*  Candle in corner */}
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "flex-end", padding: "8%" }}>
        <div style={{ width: "8%", height: "30%" }}>
          <MMSvg src={svgLib("lib/candle-single.svg")} mode="navy-gold" />
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.4} />
    </Beat>
  );
};

// ── CO-11: Two letters + Europe map pull-back ─────────────────────────────
const Beat11: React.FC = () => {
  const f = useBeatFrame(BEATS.CO11);
  const p = useBeatProgress(BEATS.CO11);
  const lightGap = interpolate(p, [0, 0.5], [0, 1], { extrapolateRight: "clamp" });
  const pullBack = interpolate(p, [0.4, 1], [1.0, 0.6], { extrapolateRight: "clamp", easing: ease });
  const mapOpacity = interpolate(p, [0.5, 1], [0, 0.7], { extrapolateRight: "clamp" });
  return (
    <Beat spec={BEATS.CO11}>
      <Plate />
      {/*  Europe map fading in behind */}
      <AbsoluteFill style={{ opacity: mapOpacity, transform: `scale(${pullBack * 1.2})` }}>
        <MMSvg src={svgLib("lib/europe-map.svg")} mode="ink-cream" />
      </AbsoluteFill>
      <Vignette intensity={0.75} />
      {/*  Two letters facing each other */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `scale(${pullBack})` }}>
        <div
          style={{
            width: "20%",
            height: "20%",
            transform: "translate(-180px, 0) rotate(15deg)",
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", transform: `scale(${pullBack})` }}>
        <div
          style={{
            width: "20%",
            height: "20%",
            transform: "translate(180px, 0) rotate(-15deg) scaleX(-1)",
          }}
        >
          <MMSvg src={svgLib("lib/letter-sealed-wax.svg")} mode="navy-cream" />
        </div>
      </AbsoluteFill>
      {/*  Light gap glow */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(245,240,228,${
            lightGap * 0.45
          }) 0%, rgba(245,240,228,0) 18%)`,
          mixBlendMode: "screen",
        }}
      />
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── CTA-1: Follow card ────────────────────────────────────────────────────
const BeatCTA1: React.FC = () => {
  const f = useBeatFrame(BEATS.CTA1);
  const p = useBeatProgress(BEATS.CTA1);
  return (
    <Beat spec={BEATS.CTA1}>
      <Plate />
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 36,
            color: MM.cream,
            textAlign: "center",
            padding: "0 12%",
            lineHeight: 1.5,
            opacity: interpolate(p, [0, 0.2], [0, 1], { extrapolateRight: "clamp" }),
            ...TEXT_STROKE,
          }}
        >
          If these stories speak to you,
          <br />
          if you find comfort in the lessons found
          <br />
          in the quiet corners of history…
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.25} />
    </Beat>
  );
};

// ── CTA-2: Circle of Dreamers + closing fade ──────────────────────────────
const BeatCTA2: React.FC = () => {
  const f = useBeatFrame(BEATS.CTA2);
  const p = useBeatProgress(BEATS.CTA2);
  const fadeToBlack = interpolate(p, [0.7, 1], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <Beat spec={BEATS.CTA2}>
      <Plate />
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", opacity: fadeToBlack }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 78,
            color: MM.gold,
            letterSpacing: "0.06em",
            ...TEXT_STROKE,
          }}
        >
          MIDNIGHT MAGNATES
        </div>
        <div
          style={{
            marginTop: 18,
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 28,
            color: MM.cream,
            letterSpacing: "0.18em",
            ...TEXT_STROKE,
          }}
        >
          JOIN THE CIRCLE OF DREAMERS
        </div>
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.3} />
    </Beat>
  );
};

// ── Composition root ──────────────────────────────────────────────────────
export const LetterDynastyColdOpenV2: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
      <Audio src={staticFile("letter-dynasty-cold-open.mp3")} volume={1} />
      <Beat1 />
      <Beat2 />
      <Beat3 />
      <Beat4 />
      <Beat5 />
      <Beat6 />
      <Beat7 />
      <Beat8 />
      <Beat9 />
      <Beat10 />
      <Beat11 />
      <BeatCTA1 />
      <BeatCTA2 />
      <FilmGrain frame={frame} opacity={0.045} />
    </AbsoluteFill>
  );
};
