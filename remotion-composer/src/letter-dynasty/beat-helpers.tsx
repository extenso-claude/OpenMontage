/**
 * Letter Dynasty — shared beat / motion / overlay helpers.
 */

import React, { CSSProperties } from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
} from "remotion";
import { MM } from "./MMSvg";

export const FPS = 24;
export const ease = Easing.inOut(Easing.cubic);
export const easeOut = Easing.out(Easing.cubic);
export const easeIn = Easing.in(Easing.cubic);

export type BeatSpec = {
  id: string;
  start: number; //  in seconds (relative to scene start)
  end: number;
  narration?: string;
};

const TEXT_STROKE: CSSProperties = {
  textShadow:
    "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000," +
    "1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000," +
    "0 4px 14px rgba(0,0,0,0.55)",
};

export { TEXT_STROKE };

/**
 * Fade beat in and out with the cross-fade dissolve duration.
 */
export const Beat: React.FC<{
  spec: BeatSpec;
  dissolve?: number;
  children: React.ReactNode;
  style?: CSSProperties;
}> = ({ spec, dissolve = 0.6, children, style }) => {
  const frame = useCurrentFrame();
  const sF = spec.start * FPS;
  const eF = spec.end * FPS;
  const dF = dissolve * FPS;
  const fadeIn = interpolate(
    frame,
    [sF - dF / 2, sF + dF / 2],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }
  );
  const fadeOut = interpolate(
    frame,
    [eF - dF / 2, eF + dF / 2],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }
  );
  const opacity = Math.min(fadeIn, fadeOut);
  if (frame < sF - dF || frame > eF + dF) return null;
  return (
    <AbsoluteFill style={{ opacity, ...style }}>{children}</AbsoluteFill>
  );
};

/**
 * Beat-local progress 0->1 across its duration.
 */
export const useBeatProgress = (spec: BeatSpec): number => {
  const frame = useCurrentFrame();
  const sF = spec.start * FPS;
  const eF = spec.end * FPS;
  return Math.max(0, Math.min(1, (frame - sF) / Math.max(1, eF - sF)));
};

/**
 * Frames since the beat started.
 */
export const useBeatFrame = (spec: BeatSpec): number => {
  const frame = useCurrentFrame();
  return frame - spec.start * FPS;
};

/**
 * Subtle "breath" — slow scale oscillation 1.0..1.02 over `period` seconds.
 */
export function breathScale(frame: number, period = 6): number {
  return 1 + 0.012 * Math.sin((2 * Math.PI * frame) / (FPS * period));
}

/**
 * Drift transform — slow horizontal pan + tiny vertical sway.
 * Returns a CSS transform string.
 */
export function driftTransform(
  frame: number,
  speed = 6,
  amount = 12,
  startFrame = 0
): string {
  const f = frame - startFrame;
  const x = (f * amount) / (FPS * speed);
  const y = 4 * Math.sin((2 * Math.PI * f) / (FPS * speed * 1.5));
  return `translate(${x}px, ${y}px)`;
}

/**
 * Micro-zoom — slow zoom-in over the beat.
 */
export function microZoom(progress: number, magnitude = 0.06): number {
  return 1 + progress * magnitude;
}

/**
 * Parallax-translate by depth: 0 (still) to 1.5 (faster than camera).
 */
export function parallax(frame: number, speedPxPerSec: number): number {
  return (frame * speedPxPerSec) / FPS;
}

/**
 * Render a single shaft of light across the frame, MM-locked.
 */
export const LightShaftAcross: React.FC<{
  frame: number;
  start?: number;
  end?: number;
  intensity?: number;
}> = ({ frame, start = 0, end, intensity = 0.5 }) => {
  // Single soft shaft from upper-left, intensifying then fading
  const intensityCurve = end
    ? interpolate(frame, [start * FPS, ((end + start) / 2) * FPS, end * FPS], [0, intensity, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : intensity;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `linear-gradient(135deg, rgba(74,111,165,${intensityCurve}) 0%, rgba(74,111,165,${
          intensityCurve * 0.4
        }) 25%, transparent 60%)`,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    />
  );
};

/**
 * Period text card — Georgia bold, cream + gold underline + draw-on stroke.
 */
export const PeriodTitle: React.FC<{
  text: string;
  progress: number; //  0->1, controls draw-on
  color?: string;
  underlineColor?: string;
  size?: number;
  style?: CSSProperties;
}> = ({
  text,
  progress,
  color = MM.cream,
  underlineColor = MM.gold,
  size = 88,
  style,
}) => {
  // Progress 0..0.6 = type appears char-by-char, 0.6..1.0 = underline draws
  const charsShown = Math.floor(progress * 1.7 * text.length);
  const underlineWidth = Math.max(
    0,
    Math.min(1, (progress - 0.55) / 0.45)
  );
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        ...style,
      }}
    >
      <div
        style={{
          fontFamily: "Georgia, 'Times New Roman', serif",
          fontWeight: 700,
          fontSize: size,
          letterSpacing: "0.02em",
          color,
          ...TEXT_STROKE,
        }}
      >
        {text.slice(0, Math.min(text.length, Math.max(0, charsShown)))}
        <span style={{ opacity: 0.001 }}>
          {text.slice(Math.max(0, charsShown))}
        </span>
      </div>
      <div
        style={{
          marginTop: 14,
          height: 3,
          width: `${underlineWidth * 70}%`,
          background: underlineColor,
          boxShadow: `0 0 12px ${underlineColor}66`,
          transition: "none",
        }}
      />
    </div>
  );
};

/**
 * Vignette overlay — channel signature mood.
 */
export const Vignette: React.FC<{ intensity?: number }> = ({ intensity = 0.65 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse at center, transparent 38%, rgba(0,0,0,${intensity}) 100%)`,
      pointerEvents: "none",
    }}
  />
);

/**
 * Film grain — animated low-opacity noise.
 */
export const FilmGrain: React.FC<{ frame: number; opacity?: number }> = ({
  frame,
  opacity = 0.045,
}) => {
  const seed = (frame * 13) % 11;
  return (
    <AbsoluteFill
      style={{
        opacity,
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 250 250' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='250' height='250' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E\")",
        transform: `translate(${seed}px, ${(seed * 7) % 9}px)`,
        pointerEvents: "none",
      }}
    />
  );
};

/**
 * Plate background — the channel-signature deep navy with subtle texture.
 */
export const Plate: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ backgroundColor: MM.bg }}>{children}</AbsoluteFill>
);

/**
 * Particle dust — for atmospheric beats.
 */
export const DustParticles: React.FC<{
  frame: number;
  count?: number;
  intensity?: number;
}> = ({ frame, count = 30, intensity = 0.4 }) => (
  <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
    {Array.from({ length: count }).map((_, i) => {
      const seed = i * 137;
      const x = (((seed * 31) % 1920) + ((frame * (10 + (i % 5))) % 200)) % 1920;
      const y = (((seed * 47) % 1080) + ((frame * (3 + (i % 4))) % 100)) % 1080;
      const r = ((seed * 7) % 6) + 1;
      const o = ((seed * 13) % 60) / 100 + 0.1;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: r,
            height: r,
            borderRadius: "50%",
            background: MM.cream,
            opacity: o * intensity,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

/**
 * Wrapper that applies a transform via a function of the current frame.
 */
export const Transformed: React.FC<{
  transform: string;
  children: React.ReactNode;
  style?: CSSProperties;
}> = ({ transform, children, style }) => (
  <AbsoluteFill style={{ transform, ...style }}>{children}</AbsoluteFill>
);
