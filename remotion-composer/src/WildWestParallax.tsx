import React from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

export const WILD_WEST_PARALLAX_DURATION_FRAMES = 300; // 10s @ 30fps

const STAR_SEEDS: { x: number; y: number; phase: number; size: number }[] = (() => {
  const stars: { x: number; y: number; phase: number; size: number }[] = [];
  // deterministic pseudo-random — same render every time
  let s = 0x9e3779b9;
  const rng = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
  for (let i = 0; i < 90; i++) {
    stars.push({
      x: rng() * 100,
      y: rng() * 45, // upper portion of frame only
      phase: rng() * Math.PI * 2,
      size: 1 + rng() * 2.2,
    });
  }
  return stars;
})();

const DUST_SEEDS: { x: number; y: number; speed: number; size: number; opacity: number }[] = (() => {
  const dust: { x: number; y: number; speed: number; size: number; opacity: number }[] = [];
  let s = 0x12345678;
  const rng = () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
  for (let i = 0; i < 30; i++) {
    dust.push({
      x: rng() * 120 - 10,
      y: 60 + rng() * 35,
      speed: 0.6 + rng() * 1.6,
      size: 1.5 + rng() * 3,
      opacity: 0.15 + rng() * 0.35,
    });
  }
  return dust;
})();

export const WildWestParallax: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  const t = frame / fps; // seconds
  const progress = frame / durationInFrames; // 0..1

  // ── BACKGROUND PAN ────────────────────────────────────────────────
  // Background is overscaled so we can pan within it without revealing edges.
  // Camera pans right-to-left across the scene (background drifts right).
  const bgScale = 1.22;
  const bgPanX = interpolate(progress, [0, 1], [-130, 130]); // px
  const bgPanY = Math.sin(t * 0.3) * 8; // very subtle vertical sway

  // ── COWBOY GALLOP ────────────────────────────────────────────────
  // Enters from right, gallops across mid-ground, exits left.
  // Cycle: 1.0s in, hold/cross over 7s, 1.0s out fade only at very end.
  const cowboyEnter = 0.0;
  const cowboyExit = 1.0;
  const cowboyX = interpolate(
    progress,
    [cowboyEnter, cowboyExit],
    [width + 480, -560], // start off-right, end off-left
    { easing: Easing.inOut(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  // horse-canter bob: vertical bounce ~ 12px @ ~2.6Hz
  const cowboyBob = Math.sin(t * Math.PI * 2 * 2.4) * 10;
  // very subtle pitch wobble
  const cowboyTilt = Math.sin(t * Math.PI * 2 * 2.4 + 0.4) * 1.2;
  // dust kick up under the horse — increases mid-cross, fades at edges
  const cowboyOnscreen = cowboyX > -560 && cowboyX < width + 480;

  // ── COWGIRL IDLE (on horseback) ──────────────────────────────────
  // Foreground-left, subtle horse-idle bob + breath + minute sway.
  const cowgirlSway = Math.sin(t * Math.PI * 2 * 0.4) * 5;
  // horse-idle bob: small, slow vertical motion (horse breathing/shifting)
  const cowgirlBob = Math.sin(t * Math.PI * 2 * 0.65) * 4;
  // tiny horse head dip
  const cowgirlTilt = Math.sin(t * Math.PI * 2 * 0.65 + 0.6) * 0.6;
  const cowgirlBreath = Math.sin(t * Math.PI * 2 * 0.32) * 0.006 + 1;
  // gentle entrance fade
  const cowgirlOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  // ── ATMOSPHERIC TINT ─────────────────────────────────────────────
  // Subtle moonlight glow that breathes
  const moonlightAlpha = 0.18 + Math.sin(t * Math.PI * 2 * 0.18) * 0.04;

  // ── CINEMATIC OPENING ────────────────────────────────────────────
  // Soft fade-in from black at the start, fade-out at the end
  const masterOpacity = interpolate(
    frame,
    [0, 18, durationInFrames - 18, durationInFrames],
    [0, 1, 1, 0.6],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a0f3a", opacity: masterOpacity }}>
      {/* Layer 1: Deep sky tint base */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, #1a0f3a 0%, #2d1b5c 40%, #4a2d7a 70%, #5b3a8a 100%)",
        }}
      />

      {/* Layer 2: Twinkling stars (parallax-back, very slow horizontal drift) */}
      <AbsoluteFill>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          style={{
            position: "absolute",
            transform: `translateX(${bgPanX * 0.25}px)`, // stars drift slowest
          }}
        >
          {STAR_SEEDS.map((star, i) => {
            const twinkle = 0.4 + 0.6 * Math.abs(Math.sin(t * 1.4 + star.phase));
            return (
              <circle
                key={i}
                cx={(star.x / 100) * width}
                cy={(star.y / 100) * height}
                r={star.size}
                fill="#fffbe5"
                opacity={twinkle}
              />
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* Layer 3: Moon — soft glow, upper right */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            top: 90,
            right: 220,
            width: 140,
            height: 140,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, #fff7d4 0%, #ffeaa0 35%, rgba(255,234,160,0.4) 60%, rgba(255,234,160,0) 80%)",
            filter: "blur(1px)",
            transform: `translateX(${bgPanX * 0.4}px)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 70,
            right: 200,
            width: 360,
            height: 360,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, rgba(255,234,160,0.25) 0%, rgba(255,234,160,0.08) 40%, rgba(255,234,160,0) 70%)",
            transform: `translateX(${bgPanX * 0.4}px)`,
            mixBlendMode: "screen",
          }}
        />
      </AbsoluteFill>

      {/* Layer 4: Background SVG — slow pan, primary depth layer */}
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            inset: 0,
            transform: `translate(${bgPanX}px, ${bgPanY}px) scale(${bgScale})`,
            transformOrigin: "center center",
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
      </AbsoluteFill>

      {/* Layer 5: Moonlight color wash — adds nighttime mood */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 80% 20%, rgba(120,160,255,0.22) 0%, rgba(80,40,140,0.0) 50%)",
          mixBlendMode: "screen",
          opacity: moonlightAlpha,
          pointerEvents: "none",
        }}
      />

      {/* Layer 6: Drifting dust particles in mid-ground */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
        >
          {DUST_SEEDS.map((d, i) => {
            // particles drift left at varying speeds
            const driftX = ((d.x - t * d.speed * 8) % 120 + 120) % 120;
            return (
              <circle
                key={i}
                cx={(driftX / 100) * width}
                cy={(d.y / 100) * height}
                r={d.size}
                fill="#d6c89a"
                opacity={d.opacity}
              />
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* Layer 7: Cowboy on horse — mid-ground, gallops across */}
      {cowboyOnscreen && (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          <div
            style={{
              position: "absolute",
              left: cowboyX,
              top: height * 0.42,
              width: 520,
              height: 520,
              transform: `translateY(${cowboyBob}px) rotate(${cowboyTilt}deg)`,
              filter: "drop-shadow(0 18px 12px rgba(0,0,0,0.55))",
            }}
          >
            <Img
              src={staticFile("wild-west/cowboy.svg")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
              }}
            />
          </div>
        </AbsoluteFill>
      )}

      {/* Layer 8: Hoof dust — small puff under cowboy */}
      {cowboyOnscreen && (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          <svg width={width} height={height}>
            {[0, 1, 2, 3].map((i) => {
              const phase = (t * 4 + i * 0.25) % 1;
              const px = cowboyX + 200 + i * 40 + phase * 60;
              const py = height * 0.42 + 430 + Math.sin(phase * Math.PI) * 6;
              const r = 8 + phase * 18;
              const op = (1 - phase) * 0.35;
              return (
                <circle
                  key={i}
                  cx={px}
                  cy={py}
                  r={r}
                  fill="#c4b48a"
                  opacity={op}
                />
              );
            })}
          </svg>
        </AbsoluteFill>
      )}

      {/* Layer 9: Cowgirl on horse — foreground left, subtle horse-idle */}
      <AbsoluteFill style={{ pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            left: -70 + cowgirlSway,
            bottom: -60,
            width: 760,
            height: 760,
            transform: `translateY(${cowgirlBob}px) rotate(${cowgirlTilt}deg) scale(${cowgirlBreath})`,
            transformOrigin: "bottom center",
            opacity: cowgirlOpacity,
            filter: "drop-shadow(0 22px 16px rgba(0,0,0,0.65))",
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

      {/* Layer 10: Atmospheric vignette — pulls eye to center */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Layer 11: Subtle film grain via repeating noise (faux) */}
      <AbsoluteFill
        style={{
          background:
            "repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,0.012) 0 1px, transparent 1px 3px)",
          mixBlendMode: "overlay",
          opacity: 0.5,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
