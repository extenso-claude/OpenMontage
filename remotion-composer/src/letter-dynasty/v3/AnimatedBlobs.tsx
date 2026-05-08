/**
 * AnimatedBlobs — DOM-positioned animated color blobs.
 *
 * Used two ways:
 *   1. Hook: place ABOVE line_art SVG with mix-blend-mode "multiply" → tints
 *      the SVG's white fills with color over time (coloring-book effect).
 *   2. Chapter 1: place BELOW line_art SVG (with stripped white BG) →
 *      blobs show through the transparent areas as watercolor underlay.
 *
 * Each blob has an `appearAt` (0-1 of beat progress) and animates from 0 to
 * its final opacity over `fadeDuration`.
 */

import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

export type AnimBlob = {
  cx: number; //  0-1 of frame width
  cy: number;
  rx: number;
  ry: number;
  color: string;
  rotation?: number;
  appearAt?: number; //  0-1 of beat progress, default 0
  fadeDuration?: number; //  0-1 of beat progress, default 0.4
  finalOpacity?: number; //  default 0.5
};

type Props = {
  blobs: AnimBlob[];
  progress: number; //  beat progress 0-1
  blendMode?: React.CSSProperties["mixBlendMode"];
  blurPx?: number;
};

export const AnimatedBlobs: React.FC<Props> = ({
  blobs,
  progress,
  blendMode = "multiply",
  blurPx = 80,
}) => (
  <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: blendMode }}>
    {blobs.map((blob, i) => {
      const appearAt = blob.appearAt ?? 0;
      const fadeDuration = blob.fadeDuration ?? 0.4;
      const finalOpacity = blob.finalOpacity ?? 0.5;
      const localP = Math.max(0, (progress - appearAt) / fadeDuration);
      const opacity = Math.min(1, localP) * finalOpacity;

      const cxPct = blob.cx * 100;
      const cyPct = blob.cy * 100;
      const wPct = blob.rx * 200;
      const hPct = blob.ry * 200;

      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${cxPct - wPct / 2}%`,
            top: `${cyPct - hPct / 2}%`,
            width: `${wPct}%`,
            height: `${hPct}%`,
            borderRadius: "50%",
            background: blob.color,
            opacity,
            filter: `blur(${blurPx}px)`,
            transform: blob.rotation ? `rotate(${blob.rotation}deg)` : undefined,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

// ── Curated palettes per scene type ───────────────────────────────────────

export const HOOK_PALETTES = {
  // Cool dawn — sky, water, distant land
  channelDawn: [
    { cx: 0.3, cy: 0.25, rx: 0.32, ry: 0.18, color: "#a8c4d4", appearAt: 0.1, fadeDuration: 0.4, finalOpacity: 0.50 }, // sky
    { cx: 0.7, cy: 0.30, rx: 0.30, ry: 0.20, color: "#e8c08c", appearAt: 0.2, fadeDuration: 0.4, finalOpacity: 0.45 }, // horizon warm
    { cx: 0.5, cy: 0.78, rx: 0.45, ry: 0.20, color: "#5a7a8c", appearAt: 0.3, fadeDuration: 0.4, finalOpacity: 0.55 }, // water
    { cx: 0.20, cy: 0.65, rx: 0.18, ry: 0.20, color: "#8a4a3a", appearAt: 0.4, fadeDuration: 0.4, finalOpacity: 0.40 }, // courier coat
  ],
  // Country road — green grass, blue sky, brown earth
  countryRoad: [
    { cx: 0.5, cy: 0.18, rx: 0.50, ry: 0.20, color: "#a8c4d4", appearAt: 0.05, fadeDuration: 0.4, finalOpacity: 0.55 }, // sky
    { cx: 0.5, cy: 0.78, rx: 0.55, ry: 0.20, color: "#7a8c4a", appearAt: 0.15, fadeDuration: 0.4, finalOpacity: 0.50 }, // grass
    { cx: 0.5, cy: 0.55, rx: 0.30, ry: 0.10, color: "#a8794a", appearAt: 0.25, fadeDuration: 0.4, finalOpacity: 0.50 }, // road
    { cx: 0.30, cy: 0.50, rx: 0.10, ry: 0.18, color: "#b41e1e", appearAt: 0.35, fadeDuration: 0.4, finalOpacity: 0.45 }, // crown coat (red)
  ],
  // Government building — amber stone, blue sky
  govtBuilding: [
    { cx: 0.5, cy: 0.30, rx: 0.45, ry: 0.30, color: "#d4b88a", appearAt: 0.1, fadeDuration: 0.4, finalOpacity: 0.50 }, // building
    { cx: 0.5, cy: 0.10, rx: 0.50, ry: 0.10, color: "#a8c4d4", appearAt: 0.05, fadeDuration: 0.4, finalOpacity: 0.45 }, // sky
    { cx: 0.50, cy: 0.65, rx: 0.20, ry: 0.18, color: "#4a3a2a", appearAt: 0.30, fadeDuration: 0.4, finalOpacity: 0.50 }, // messenger cloak
  ],
  // Bedroom — warm candlelight
  bedroom: [
    { cx: 0.40, cy: 0.50, rx: 0.40, ry: 0.40, color: "#e8b56a", appearAt: 0.10, fadeDuration: 0.4, finalOpacity: 0.45 }, // candle warm
    { cx: 0.70, cy: 0.55, rx: 0.30, ry: 0.40, color: "#5a4a8c", appearAt: 0.25, fadeDuration: 0.4, finalOpacity: 0.40 }, // bed shadow
    { cx: 0.20, cy: 0.65, rx: 0.20, ry: 0.30, color: "#6a3a2a", appearAt: 0.35, fadeDuration: 0.4, finalOpacity: 0.40 }, // courier
  ],
  // London dawn — grey blue sky, cool light
  londonDawn: [
    { cx: 0.5, cy: 0.20, rx: 0.55, ry: 0.20, color: "#a8c4d4", appearAt: 0.05, fadeDuration: 0.4, finalOpacity: 0.55 },
    { cx: 0.5, cy: 0.65, rx: 0.55, ry: 0.20, color: "#8a8a7a", appearAt: 0.20, fadeDuration: 0.4, finalOpacity: 0.45 }, // street grey
    { cx: 0.65, cy: 0.55, rx: 0.20, ry: 0.20, color: "#b41e1e", appearAt: 0.30, fadeDuration: 0.4, finalOpacity: 0.45 }, // courier coat
  ],
  // Stock Exchange interior — cool stone with warm light shaft
  stockExchange: [
    { cx: 0.5, cy: 0.30, rx: 0.45, ry: 0.30, color: "#d4c4a8", appearAt: 0.10, fadeDuration: 0.4, finalOpacity: 0.45 }, // stone walls
    { cx: 0.5, cy: 0.50, rx: 0.18, ry: 0.40, color: "#e8c08c", appearAt: 0.30, fadeDuration: 0.4, finalOpacity: 0.50 }, // light shaft
    { cx: 0.50, cy: 0.65, rx: 0.12, ry: 0.30, color: "#1a2840", appearAt: 0.40, fadeDuration: 0.4, finalOpacity: 0.55 }, // Nathan dark coat
  ],
  // Thames at sunset — gold sun, river, gold coins
  thamesSunset: [
    { cx: 0.30, cy: 0.30, rx: 0.20, ry: 0.20, color: "#e8a06a", appearAt: 0.10, fadeDuration: 0.4, finalOpacity: 0.65 }, // sun
    { cx: 0.5, cy: 0.65, rx: 0.55, ry: 0.20, color: "#5a7a8c", appearAt: 0.20, fadeDuration: 0.4, finalOpacity: 0.50 }, // river
    { cx: 0.70, cy: 0.70, rx: 0.18, ry: 0.20, color: "#c9a84c", appearAt: 0.40, fadeDuration: 0.4, finalOpacity: 0.65 }, // gold coins
  ],
  // Frankfurt night — moonlit dusk
  frankfurtNight: [
    { cx: 0.5, cy: 0.18, rx: 0.55, ry: 0.18, color: "#3a4a6a", appearAt: 0.05, fadeDuration: 0.4, finalOpacity: 0.55 }, // night sky
    { cx: 0.5, cy: 0.55, rx: 0.40, ry: 0.30, color: "#5a4a3a", appearAt: 0.20, fadeDuration: 0.4, finalOpacity: 0.50 }, // buildings
    { cx: 0.50, cy: 0.75, rx: 0.20, ry: 0.10, color: "#8a6a4a", appearAt: 0.30, fadeDuration: 0.4, finalOpacity: 0.45 }, // ground
  ],
  // Mayer study — warm candlelit interior
  mayerStudy: [
    { cx: 0.50, cy: 0.50, rx: 0.40, ry: 0.40, color: "#d4944a", appearAt: 0.15, fadeDuration: 0.4, finalOpacity: 0.55 }, // candle warm
    { cx: 0.30, cy: 0.65, rx: 0.20, ry: 0.30, color: "#3a2a1a", appearAt: 0.30, fadeDuration: 0.4, finalOpacity: 0.50 }, // figures dark
    { cx: 0.70, cy: 0.65, rx: 0.20, ry: 0.30, color: "#3a2a1a", appearAt: 0.40, fadeDuration: 0.4, finalOpacity: 0.50 },
  ],
} as const;

// ── Period-sepia palettes for Chapter 1 ───────────────────────────────────

const SEPIA = {
  burntUmber: "#8b5a2b",
  olive: "#7a8c4a",
  dimGold: "#c9a84c",
  warmRust: "#a8593a",
  paleSand: "#d4a574",
  forestShadow: "#3a4a3a",
};

export const CHAPTER1_BLOBS = (seed: number): AnimBlob[] => {
  const palettes = [
    [SEPIA.burntUmber, SEPIA.olive, SEPIA.dimGold],
    [SEPIA.warmRust, SEPIA.paleSand, SEPIA.dimGold],
    [SEPIA.olive, SEPIA.forestShadow, SEPIA.burntUmber],
    [SEPIA.paleSand, SEPIA.dimGold, SEPIA.warmRust],
  ];
  const p = palettes[seed % palettes.length];
  return [
    { cx: 0.25, cy: 0.30, rx: 0.30, ry: 0.25, color: p[0], rotation: -12, appearAt: 0.05, fadeDuration: 0.4, finalOpacity: 0.50 },
    { cx: 0.78, cy: 0.50, rx: 0.28, ry: 0.32, color: p[1], rotation: 18, appearAt: 0.20, fadeDuration: 0.4, finalOpacity: 0.45 },
    { cx: 0.50, cy: 0.78, rx: 0.32, ry: 0.20, color: p[2], rotation: -5, appearAt: 0.35, fadeDuration: 0.4, finalOpacity: 0.55 },
    { cx: 0.20, cy: 0.75, rx: 0.22, ry: 0.18, color: p[1], rotation: 25, appearAt: 0.50, fadeDuration: 0.4, finalOpacity: 0.40 },
  ];
};
