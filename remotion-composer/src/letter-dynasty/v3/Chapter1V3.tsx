/**
 * Letter Dynasty v3 — Chapter 1 with region-fill coloring-book animation.
 *
 * Period-sepia palette: each beat fills line art's region shapes with
 * burnt-umber / olive / dim-gold / warm-rust based on spatial position.
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
import { RegionFillSvg, CHAPTER1_REGION_PALETTES, RegionPalette } from "./RegionFillSvg";
import {
  Beat,
  BeatSpec,
  FilmGrain,
  FPS,
  Vignette,
  microZoom,
  useBeatFrame,
  useBeatProgress,
} from "../beat-helpers";

const CHAPTER1_DURATION_S = 80.85;
export const LETTER_CHAPTER1_V3_DURATION_FRAMES = Math.ceil(CHAPTER1_DURATION_S * FPS);

const BEATS: Record<string, BeatSpec> = {
  C1: { id: "C1-01", start: 0.0, end: 8.92 },
  C2: { id: "C1-02", start: 8.92, end: 15.48 },
  C3: { id: "C1-03", start: 16.24, end: 22.96 },
  C4: { id: "C1-04", start: 23.76, end: 29.28 },
  C5: { id: "C1-05", start: 30.0, end: 37.56 },
  C6: { id: "C1-06", start: 39.36, end: 45.96 },
  C7: { id: "C1-07", start: 45.96, end: 52.82 },
  C8: { id: "C1-08", start: 52.82, end: 61.32 },
  C9: { id: "C1-09", start: 61.32, end: 68.78 },
  C10: { id: "C1-10", start: 69.6, end: 77.56 },
  C11: { id: "C1-11", start: 77.56, end: 80.42 },
};

const Scene: React.FC<{
  spec: BeatSpec;
  src: string;
  palette: RegionPalette;
  zoom?: number;
  drift?: { x: number; y: number };
}> = ({ spec, src, palette, zoom = 0.04, drift }) => {
  const p = useBeatProgress(spec);
  const scale = microZoom(p, zoom);
  const tx = drift ? drift.x * p : 0;
  const ty = drift ? drift.y * p : 0;
  const lineArtOpacity = interpolate(p, [0, 0.18], [0, 1], { extrapolateRight: "clamp" });
  const fillProgress = interpolate(p, [0.18, 0.65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stagger = {
    sky: 0.0,
    ground: 0.15,
    "left-subject": 0.3,
    "center-subject": 0.45,
    "right-subject": 0.55,
  };
  return (
    <Beat spec={spec}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <AbsoluteFill style={{ transform: `translate(${tx}px, ${ty}px) scale(${scale})`, opacity: lineArtOpacity }}>
        <RegionFillSvg src={src} palette={palette} fillProgress={fillProgress} staggerStart={stagger} staggerWindow={0.5} preserveAspect="xMidYMid meet" />
      </AbsoluteFill>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

const EUROPE_CITIES: Record<string, { x: number; y: number }> = {
  FRANKFURT: { x: 0.55, y: 0.42 },
  LONDON: { x: 0.40, y: 0.32 },
  PARIS: { x: 0.46, y: 0.46 },
  VIENNA: { x: 0.62, y: 0.50 },
  NAPLES: { x: 0.58, y: 0.62 },
};

const MapWithPins: React.FC<{ pins: Array<{ name: string; lit: boolean }> }> = ({ pins }) => (
  <>
    <AbsoluteFill style={{ opacity: 0.85 }}>
      <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
    </AbsoluteFill>
    {pins.map((pin) => {
      const c = EUROPE_CITIES[pin.name];
      if (!c) return null;
      return (
        <React.Fragment key={pin.name}>
          <div
            style={{
              position: "absolute",
              left: `${c.x * 100}%`,
              top: `${c.y * 100}%`,
              width: 18,
              height: 18,
              borderRadius: "50%",
              background: MM.gold,
              opacity: pin.lit ? 1 : 0.25,
              boxShadow: pin.lit ? `0 0 28px ${MM.gold}` : "none",
              transform: "translate(-50%, -50%)",
            }}
          />
          <div
            style={{
              position: "absolute",
              left: `${c.x * 100}%`,
              top: `calc(${c.y * 100}% - 36px)`,
              transform: "translateX(-50%)",
              fontFamily: "Georgia, serif",
              fontWeight: 700,
              fontSize: 22,
              color: MM.gold,
              opacity: pin.lit ? 1 : 0,
              letterSpacing: "0.15em",
              textShadow: "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000",
              whiteSpace: "nowrap",
            }}
          >
            {pin.name}
          </div>
        </React.Fragment>
      );
    })}
  </>
);

const Beat4: React.FC = () => {
  const p = useBeatProgress(BEATS.C4);
  const pins = [
    { name: "FRANKFURT", lit: p > 0.85 },
    { name: "LONDON", lit: false },
    { name: "PARIS", lit: false },
    { name: "VIENNA", lit: false },
    { name: "NAPLES", lit: false },
  ];
  return (
    <Beat spec={BEATS.C4}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <MapWithPins pins={pins} />
      <Vignette intensity={0.4} />
    </Beat>
  );
};

const Beat5: React.FC = () => {
  const p = useBeatProgress(BEATS.C5);
  const pins = [
    { name: "FRANKFURT", lit: true },
    { name: "LONDON", lit: p > 0.05 },
    { name: "PARIS", lit: p > 0.27 },
    { name: "VIENNA", lit: p > 0.55 },
    { name: "NAPLES", lit: p > 0.78 },
  ];
  return (
    <Beat spec={BEATS.C5}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <MapWithPins pins={pins} />
      <Vignette intensity={0.4} />
    </Beat>
  );
};

const Beat6: React.FC = () => {
  const p = useBeatProgress(BEATS.C6);
  const cities = ["LONDON", "PARIS", "VIENNA", "NAPLES"];
  const frankfurt = EUROPE_CITIES.FRANKFURT;
  return (
    <Beat spec={BEATS.C6}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <AbsoluteFill style={{ opacity: 0.6 }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
      </AbsoluteFill>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        {cities.map((name, i) => {
          const c = EUROPE_CITIES[name];
          const startP = i * 0.08;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.5));
          const x1 = frankfurt.x * 1920;
          const y1 = frankfurt.y * 1080;
          const x2 = c.x * 1920;
          const y2 = c.y * 1080;
          const cx = x1 + (x2 - x1) * localP;
          const cy = y1 + (y2 - y1) * localP;
          return (
            <line key={name} x1={x1} y1={y1} x2={cx} y2={cy} stroke={MM.gold} strokeWidth={3} opacity={0.9} style={{ filter: `drop-shadow(0 0 10px ${MM.gold})` }} />
          );
        })}
        {Object.values(EUROPE_CITIES).map((c, i) => (
          <circle key={i} cx={c.x * 1920} cy={c.y * 1080} r={8} fill={MM.gold} style={{ filter: `drop-shadow(0 0 12px ${MM.gold})` }} />
        ))}
      </svg>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

const Beat7: React.FC = () => {
  const p = useBeatProgress(BEATS.C7);
  const all = Object.values(EUROPE_CITIES);
  const pairs: [number, number][] = [];
  for (let a = 0; a < all.length; a++) for (let b = a + 1; b < all.length; b++) pairs.push([a, b]);
  return (
    <Beat spec={BEATS.C7}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <AbsoluteFill style={{ opacity: 0.6 }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
      </AbsoluteFill>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        {pairs.map(([a, b], idx) => {
          const startP = idx * 0.06;
          const localP = Math.max(0, Math.min(1, (p - startP) / 0.4));
          const x1 = all[a].x * 1920;
          const y1 = all[a].y * 1080;
          const x2 = all[b].x * 1920;
          const y2 = all[b].y * 1080;
          const cx = x1 + (x2 - x1) * localP;
          const cy = y1 + (y2 - y1) * localP;
          return <line key={idx} x1={x1} y1={y1} x2={cx} y2={cy} stroke={MM.gold} strokeWidth={2.5} opacity={0.7} style={{ filter: `drop-shadow(0 0 4px ${MM.gold})` }} />;
        })}
        {all.map((c, i) => (
          <circle key={i} cx={c.x * 1920} cy={c.y * 1080} r={7} fill={MM.gold} />
        ))}
      </svg>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

const Beat8: React.FC = () => {
  const f = useBeatFrame(BEATS.C8);
  const p = useBeatProgress(BEATS.C8);
  const pulse = 0.7 + 0.3 * Math.sin((f * 2 * Math.PI) / (FPS * 2.5));
  const all = Object.values(EUROPE_CITIES);
  const pairs: [number, number][] = [];
  for (let a = 0; a < all.length; a++) for (let b = a + 1; b < all.length; b++) pairs.push([a, b]);
  return (
    <Beat spec={BEATS.C8}>
      <AbsoluteFill style={{ backgroundColor: MM.parchment }} />
      <AbsoluteFill style={{ opacity: 0.6 }}>
        <MMSvgV3 src={v3lib("scenes/chapter2/c2-europe-map-base.svg")} />
      </AbsoluteFill>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        {pairs.map(([a, b], idx) => (
          <line key={idx} x1={all[a].x * 1920} y1={all[a].y * 1080} x2={all[b].x * 1920} y2={all[b].y * 1080} stroke={MM.gold} strokeWidth={2} opacity={0.55 * pulse} />
        ))}
        {all.map((c, i) => (
          <circle key={i} cx={c.x * 1920} cy={c.y * 1080} r={8 + 2 * pulse} fill={MM.gold} opacity={pulse} />
        ))}
      </svg>
      <Vignette intensity={0.4} />
    </Beat>
  );
};

export const LetterDynastyChapter1V3: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: MM.parchment }}>
      <Audio src={staticFile("letter-dynasty-chapter1.mp3")} volume={1} />
      <Scene spec={BEATS.C1} src={v3lib("scenes/chapter1/c1-mayer-at-gate-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.judengasse1} />
      <Scene spec={BEATS.C2} src={v3lib("scenes/chapter1/c1-pavement-divide-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.pavement} />
      <Scene spec={BEATS.C3} src={v3lib("scenes/chapter1/c1-mayer-at-gate-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.judengasse2} />
      <Beat4 />
      <Beat5 />
      <Beat6 />
      <Beat7 />
      <Beat8 />
      <Scene spec={BEATS.C9} src={v3lib("scenes/chapter1/c1-mayer-final-desk-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.mayerDesk} />
      <Scene spec={BEATS.C10} src={v3lib("scenes/chapter1/c1-mayer-final-desk-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.mayerDesk} />
      <Scene spec={BEATS.C11} src={v3lib("lib/ledger-isolated-line-tagged.svg")} palette={CHAPTER1_REGION_PALETTES.ledger} zoom={0.07} />
      <FilmGrain frame={frame} opacity={0.05} />
    </AbsoluteFill>
  );
};
