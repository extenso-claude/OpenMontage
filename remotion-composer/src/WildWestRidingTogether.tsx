import React from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";

export const WILD_WEST_RIDING_TOGETHER_DURATION_FRAMES = 360; // 12s @ 30fps

// Reusable deterministic seed RNG
const seeded = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
};

const STARS = (() => {
  const rng = seeded(0x1f2e3d4c);
  return Array.from({ length: 110 }, () => ({
    x: rng() * 100,
    y: rng() * 50,
    phase: rng() * Math.PI * 2,
    size: 1 + rng() * 2.4,
  }));
})();

// Mid-distant cactus silhouettes (parallax mid-layer)
const MID_CACTI = (() => {
  const rng = seeded(0xa1b2c3d4);
  return Array.from({ length: 8 }, () => ({
    x: rng() * 120,
    y: 60 + rng() * 8,
    height: 80 + rng() * 90,
    flip: rng() > 0.5,
  }));
})();

// Foreground tumbleweed-ish dust patches (fastest layer)
const FG_DUST = (() => {
  const rng = seeded(0xdeadbeef);
  return Array.from({ length: 28 }, () => ({
    x: rng() * 120,
    y: 70 + rng() * 28,
    size: 1.5 + rng() * 4,
    opacity: 0.18 + rng() * 0.4,
  }));
})();

const Cactus: React.FC<{ height: number; flip: boolean }> = ({
  height,
  flip,
}) => {
  // simple silhouette cactus shape via SVG
  const w = height * 0.55;
  return (
    <svg
      width={w}
      height={height}
      viewBox="0 0 100 180"
      style={{ transform: flip ? "scaleX(-1)" : "none" }}
    >
      <path
        d="M 45 180 L 45 80 Q 45 60 30 60 Q 18 60 18 75 L 18 110 Q 18 118 26 118 Q 32 118 32 110 L 32 90 M 55 180 L 55 50 Q 55 30 70 30 Q 82 30 82 45 L 82 80 Q 82 88 74 88 Q 68 88 68 80 L 68 65 M 45 180 L 55 180 Z"
        fill="#0a0512"
        stroke="#1d0e3a"
        strokeWidth="2"
      />
    </svg>
  );
};

export const WildWestRidingTogether: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const t = frame / fps;
  const progress = frame / durationInFrames;

  // ── PARALLAX SCROLL SPEEDS ────────────────────────────────────────
  // Camera tracks the riders moving right. World scrolls LEFT.
  // Each layer moves at its own speed; closer = faster.
  const totalScroll = 1400; // px traveled over the full duration
  const scroll = progress * totalScroll;

  const starParallax = scroll * 0.08; // very slow
  const skyParallax = scroll * 0.15;
  const bgParallax = scroll * 0.55; // mid background layer
  const cactusParallax = scroll * 0.85; // mid-foreground
  const fgDustParallax = scroll * 1.4; // very fast foreground
  const groundShimmer = Math.sin(t * 1.5) * 2;

  // ── HORSE GALLOP CYCLE ────────────────────────────────────────────
  // Both horses gallop. Cowgirl is foreground (slower amplitude appearance
  // because she's closer to camera), cowboy mid-ground (further).
  const gallopHz = 2.6;
  const cowgirlBob = Math.sin(t * Math.PI * 2 * gallopHz) * 14;
  const cowgirlTilt = Math.sin(t * Math.PI * 2 * gallopHz + 0.4) * 1.5;
  // cowboy slightly out of phase (so they don't bob in lockstep)
  const cowboyBob = Math.sin(t * Math.PI * 2 * gallopHz + 1.1) * 11;
  const cowboyTilt = Math.sin(t * Math.PI * 2 * gallopHz + 1.5) * 1.3;

  // Atmospheric breathing
  const moonlightAlpha = 0.18 + Math.sin(t * 0.4) * 0.05;

  // Master fade
  const masterOpacity = interpolate(
    frame,
    [0, 24, durationInFrames - 30, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Background scaled to be wider than viewport so we can scroll within it.
  // We'll TILE it horizontally for endless feel using two copies.
  const bgScale = 1.25;
  const bgRenderWidth = width * bgScale * 1.05;

  // Foreground ground gradient pan
  const groundOffset = -scroll * 0.95;

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#100726", opacity: masterOpacity }}
    >
      {/* Layer 1: Sky gradient base */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, #0d0727 0%, #2a1860 35%, #4a2d7a 65%, #5b3a8a 100%)",
        }}
      />

      {/* Layer 2: Star field — very slow drift */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg width={width} height={height}>
          <g transform={`translate(${-starParallax % width}, 0)`}>
            {STARS.map((s, i) => {
              const tw = 0.5 + 0.5 * Math.abs(Math.sin(t * 1.3 + s.phase));
              return (
                <circle
                  key={i}
                  cx={(s.x / 100) * width}
                  cy={(s.y / 100) * height}
                  r={s.size}
                  fill="#fff5d4"
                  opacity={tw}
                />
              );
            })}
          </g>
          {/* duplicated star band for seamless wrap */}
          <g transform={`translate(${(-starParallax % width) + width}, 0)`}>
            {STARS.map((s, i) => {
              const tw = 0.5 + 0.5 * Math.abs(Math.sin(t * 1.3 + s.phase));
              return (
                <circle
                  key={`d-${i}`}
                  cx={(s.x / 100) * width}
                  cy={(s.y / 100) * height}
                  r={s.size}
                  fill="#fff5d4"
                  opacity={tw}
                />
              );
            })}
          </g>
        </svg>
      </AbsoluteFill>

      {/* Layer 3: Moon */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            top: 110,
            left: width * 0.7 - skyParallax,
            width: 150,
            height: 150,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, #fff7d4 0%, #ffe9a0 35%, rgba(255,234,160,0.4) 60%, rgba(255,234,160,0) 80%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 80,
            left: width * 0.7 - 100 - skyParallax,
            width: 380,
            height: 380,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, rgba(255,234,160,0.22) 0%, rgba(255,234,160,0.07) 40%, rgba(255,234,160,0) 70%)",
            mixBlendMode: "screen",
          }}
        />
      </AbsoluteFill>

      {/* Layer 4: Background SVG, tiled twice for seamless scroll */}
      <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            transform: `translateX(${-bgParallax % bgRenderWidth}px)`,
            display: "flex",
            height: "100%",
          }}
        >
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                left: i * bgRenderWidth,
                top: 0,
                width: bgRenderWidth,
                height: "100%",
              }}
            >
              <Img
                src={staticFile("wild-west/background.svg")}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: "center bottom",
                }}
              />
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* Layer 5: Moonlight wash */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 75% 25%, rgba(140,170,255,0.22) 0%, rgba(80,40,140,0) 55%)",
          mixBlendMode: "screen",
          opacity: moonlightAlpha,
          pointerEvents: "none",
        }}
      />

      {/* Layer 6: Mid-distant cacti silhouettes */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {MID_CACTI.map((c, i) => {
          const baseX = (c.x / 100) * width * 2.5;
          const x = ((baseX - cactusParallax) % (width * 2.5) + width * 2.5) %
            (width * 2.5) - width * 0.4;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: (c.y / 100) * height,
                opacity: 0.85,
              }}
            >
              <Cactus height={c.height} flip={c.flip} />
            </div>
          );
        })}
      </AbsoluteFill>

      {/* Layer 7: Ground shimmer (subtle moving dust band) */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: height * 0.32,
            background:
              "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(60,30,80,0.25) 50%, rgba(20,10,40,0.55) 100%)",
            transform: `translateX(${groundOffset * 0.05}px) translateY(${groundShimmer}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Layer 8: Cowboy on horse — mid-ground, slightly behind */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: width * 0.46,
            top: height * 0.42,
            width: 460,
            height: 460,
            transform: `translateY(${cowboyBob}px) rotate(${cowboyTilt}deg)`,
            filter:
              "drop-shadow(0 16px 14px rgba(0,0,0,0.55)) brightness(0.92)",
          }}
        >
          <Img
            src={staticFile("wild-west/cowboy.svg")}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        </div>
      </AbsoluteFill>

      {/* Layer 9: Foreground dust trail (behind cowboy hooves) */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg width={width} height={height}>
          {[0, 1, 2, 3, 4].map((i) => {
            const phase = (t * 4 + i * 0.2) % 1;
            const px = width * 0.46 + 280 + i * 30 + phase * 50;
            const py = height * 0.42 + 380 + Math.sin(phase * Math.PI) * 8;
            const r = 6 + phase * 22;
            const op = (1 - phase) * 0.4;
            return (
              <circle
                key={`cb-${i}`}
                cx={px}
                cy={py}
                r={r}
                fill="#bda47a"
                opacity={op}
              />
            );
          })}
          {/* Cowgirl hoof dust */}
          {[0, 1, 2, 3, 4, 5].map((i) => {
            const phase = (t * 4.6 + i * 0.18) % 1;
            const px = -10 + 290 + i * 36 + phase * 60;
            const py = height * 0.55 + 400 + Math.sin(phase * Math.PI) * 10;
            const r = 8 + phase * 28;
            const op = (1 - phase) * 0.55;
            return (
              <circle
                key={`cg-${i}`}
                cx={px}
                cy={py}
                r={r}
                fill="#d6c089"
                opacity={op}
              />
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* Layer 10: Cowgirl on horse — foreground left */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: -10,
            bottom: -50,
            width: 720,
            height: 720,
            transform: `translateY(${cowgirlBob}px) rotate(${cowgirlTilt}deg)`,
            transformOrigin: "bottom center",
            filter: "drop-shadow(0 22px 18px rgba(0,0,0,0.7))",
          }}
        >
          <Img
            src={staticFile("wild-west/cowgirl.svg")}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "bottom center",
            }}
          />
        </div>
      </AbsoluteFill>

      {/* Layer 11: Foreground dust streaks (very fast parallax) */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg width={width} height={height}>
          {FG_DUST.map((d, i) => {
            const x =
              ((d.x / 100) * width * 2 - fgDustParallax) %
              (width * 2);
            const wrappedX = x < -50 ? x + width * 2 : x;
            return (
              <circle
                key={i}
                cx={wrappedX}
                cy={(d.y / 100) * height}
                r={d.size}
                fill="#e0cfa0"
                opacity={d.opacity}
              />
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* Layer 12: Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.6) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Layer 13: Soft film grain */}
      <AbsoluteFill
        style={{
          background:
            "repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,0.014) 0 1px, transparent 1px 3px)",
          mixBlendMode: "overlay",
          opacity: 0.55,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
