/**
 * Letter Dynasty v3 — Hook with proper coloring-book fill-in.
 *
 * Each line_art SVG is region-tagged (sky / ground / left-subject /
 * center-subject / right-subject). Per-beat palettes assign colors to each
 * region. Fill animates from white → target color over a window in the beat,
 * staggered by region for a "watercolor sweep" reveal.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { MM, MMSvgV3, v3lib } from "./MMSvgV3";
import { RegionFillSvg, HOOK_REGION_PALETTES, RegionPalette } from "./RegionFillSvg";
import {
  Beat,
  BeatSpec,
  FilmGrain,
  FPS,
  LightShaftAcross,
  PeriodTitle,
  TEXT_STROKE,
  Vignette,
  microZoom,
  useBeatFrame,
  useBeatProgress,
} from "../beat-helpers";

const HOOK_DURATION_S = 71.08;
export const LETTER_HOOK_V3_DURATION_FRAMES = Math.ceil(HOOK_DURATION_S * FPS);

const BEATS: Record<string, BeatSpec> = {
  H1: { id: "H-01", start: 0.0, end: 9.3 },
  H2: { id: "H-02", start: 10.36, end: 15.82 },
  H3: { id: "H-03", start: 16.94, end: 18.12 },
  H4: { id: "H-04", start: 19.1, end: 21.66 },
  H5: { id: "H-05", start: 22.74, end: 29.12 },
  H6: { id: "H-06", start: 29.12, end: 37.62 },
  H7: { id: "H-07", start: 38.8, end: 42.02 },
  H8: { id: "H-08", start: 42.58, end: 47.98 },
  H9: { id: "H-09", start: 48.7, end: 55.42 },
  H10: { id: "H-10", start: 55.42, end: 62.28 },
  H11: { id: "H-11", start: 63.02, end: 70.58 },
};

/** Scene with line-art reveal (lines fade in first) + region-fill animation. */
const Scene: React.FC<{
  spec: BeatSpec;
  src: string;
  palette: RegionPalette;
  zoom?: number;
  drift?: { x: number; y: number };
  light?: number;
  preserveAspect?: string;
}> = ({ spec, src, palette, zoom = 0.04, drift, light = 0.25, preserveAspect = "xMidYMid meet" }) => {
  const f = useBeatFrame(spec);
  const p = useBeatProgress(spec);
  const scale = microZoom(p, zoom);
  const tx = drift ? drift.x * p : 0;
  const ty = drift ? drift.y * p : 0;
  // Lines first (0 → 0.18), then fill animates (0.18 → 0.65)
  const lineArtOpacity = interpolate(p, [0, 0.18], [0, 1], { extrapolateRight: "clamp" });
  const fillProgress = interpolate(p, [0.18, 0.65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Stagger regions so they fill in successively
  const stagger = {
    sky: 0.0,
    ground: 0.15,
    "left-subject": 0.3,
    "center-subject": 0.45,
    "right-subject": 0.55,
  };
  return (
    <Beat spec={spec}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill
        style={{
          transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
          opacity: lineArtOpacity,
        }}
      >
        <RegionFillSvg
          src={src}
          palette={palette}
          fillProgress={fillProgress}
          staggerStart={stagger}
          staggerWindow={0.5}
          preserveAspect={preserveAspect}
        />
      </AbsoluteFill>
      <Vignette intensity={0.4} />
      <LightShaftAcross frame={f} intensity={light} />
    </Beat>
  );
};

// H-09: Calendar year roll-back (procedural)
const Beat9: React.FC = () => {
  const f = useBeatFrame(BEATS.H9);
  const p = useBeatProgress(BEATS.H9);
  const year = Math.round(1815 - p * 20);
  return (
    <Beat spec={BEATS.H9}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <Vignette intensity={0.4} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 240,
            color: MM.ink,
            letterSpacing: "0.04em",
            ...TEXT_STROKE,
          }}
        >
          {year}
        </div>
        <div
          style={{
            marginTop: 24,
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 28,
            color: MM.goldDim,
            letterSpacing: "0.2em",
          }}
        >
          TWENTY YEARS BACK
        </div>
      </AbsoluteFill>
      <FilmGrain frame={f} opacity={0.06} />
    </Beat>
  );
};

// H-07: Name reveal — "Nathan Mayer Rothschild"
const Beat7: React.FC = () => {
  const f = useBeatFrame(BEATS.H7);
  const p = useBeatProgress(BEATS.H7);
  return (
    <Beat spec={BEATS.H7}>
      <AbsoluteFill style={{ backgroundColor: MM.cream }} />
      <AbsoluteFill style={{ opacity: 0.55 }}>
        <RegionFillSvg
          src={v3lib("scenes/hook/h06-nathan-stock-exchange-tagged.svg")}
          palette={HOOK_REGION_PALETTES.stockExchange}
          fillProgress={1}
          preserveAspect="xMidYMid meet"
        />
      </AbsoluteFill>
      <Vignette intensity={0.5} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <PeriodTitle text="Nathan Mayer Rothschild" progress={p} size={86} color={MM.ink} underlineColor={MM.gold} />
      </AbsoluteFill>
      <LightShaftAcross frame={f} intensity={0.35} />
    </Beat>
  );
};

export const LetterDynastyHookV3: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.cream }}>
      <Audio src={staticFile("letter-dynasty-hook.wav")} volume={1} />
      <Scene spec={BEATS.H1} src={v3lib("scenes/hook/h01-dock-courier-tagged.svg")} palette={HOOK_REGION_PALETTES.channelDawn} drift={{ x: 30, y: 0 }} />
      <Scene spec={BEATS.H2} src={v3lib("scenes/hook/h02-dual-rider-road-tagged.svg")} palette={HOOK_REGION_PALETTES.countryRoad} drift={{ x: -50, y: 0 }} zoom={0.05} />
      <Scene spec={BEATS.H3} src={v3lib("scenes/hook/h03-fo-door-tagged.svg")} palette={HOOK_REGION_PALETTES.govtBuilding} zoom={0.07} />
      <Scene spec={BEATS.H4} src={v3lib("scenes/hook/h04-prince-bedroom-tagged.svg")} palette={HOOK_REGION_PALETTES.bedroom} zoom={0.04} />
      <Scene spec={BEATS.H5} src={v3lib("scenes/hook/h05-couriers-london-dawn-tagged.svg")} palette={HOOK_REGION_PALETTES.londonDawn} drift={{ x: -40, y: 0 }} />
      <Scene spec={BEATS.H6} src={v3lib("scenes/hook/h06-nathan-stock-exchange-tagged.svg")} palette={HOOK_REGION_PALETTES.stockExchange} zoom={0.06} />
      <Beat7 />
      <Scene spec={BEATS.H8} src={v3lib("scenes/hook/h08-thames-sunset-coins-tagged.svg")} palette={HOOK_REGION_PALETTES.thamesSunset} zoom={0.04} />
      <Beat9 />
      <Scene spec={BEATS.H10} src={v3lib("scenes/hook/h10-mayer-frankfurt-gate-sons-leaving-tagged.svg")} palette={HOOK_REGION_PALETTES.frankfurtNight} zoom={0.05} />
      <Scene spec={BEATS.H11} src={v3lib("scenes/hook/h11-mayer-son-desk-candle-tagged.svg")} palette={HOOK_REGION_PALETTES.mayerStudy} zoom={0.04} />
      <FilmGrain frame={frame} opacity={0.04} />
    </AbsoluteFill>
  );
};
