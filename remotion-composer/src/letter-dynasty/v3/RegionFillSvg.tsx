/**
 * RegionFillSvg — load a region-tagged line_art SVG and animate per-region fills.
 *
 * The tagged SVG has white counter-shapes with `fill="var(--reg-NAME, rgb(254,254,254))"`.
 * This component sets CSS variables on the parent div, interpolating each region's
 * fill color from white (rgb(254,254,254)) to its target over the beat progress.
 *
 * Result: line art appears to "fill in" with proper colors between the lines.
 */

import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, interpolate, staticFile } from "remotion";

export const REGIONS = ["sky", "ground", "left-subject", "center-subject", "right-subject"] as const;
export type Region = (typeof REGIONS)[number];
export type RegionPalette = Partial<Record<Region, string>>;

const SVG_CACHE = new Map<string, string>();

function forceFill(xml: string, preserveAspect: string): string {
  return xml.replace(/<svg\b([^>]*)>/i, (_match, attrs: string) => {
    const cleaned = attrs
      .replace(/\s+width\s*=\s*"[^"]*"/gi, "")
      .replace(/\s+height\s*=\s*"[^"]*"/gi, "")
      .replace(/\s+style\s*=\s*"[^"]*"/gi, "")
      .replace(/\s+preserveAspectRatio\s*=\s*"[^"]*"/gi, "");
    return `<svg${cleaned} width="100%" height="100%" preserveAspectRatio="${preserveAspect}" style="display:block;width:100%;height:100%">`;
  });
}

/** Linear interpolate between two hex colors. */
function lerpHex(start: string, end: string, t: number): string {
  const sH = start.replace("#", "");
  const eH = end.replace("#", "");
  const sR = parseInt(sH.slice(0, 2), 16);
  const sG = parseInt(sH.slice(2, 4), 16);
  const sB = parseInt(sH.slice(4, 6), 16);
  const eR = parseInt(eH.slice(0, 2), 16);
  const eG = parseInt(eH.slice(2, 4), 16);
  const eB = parseInt(eH.slice(4, 6), 16);
  const c = Math.max(0, Math.min(1, t));
  const r = Math.round(sR + (eR - sR) * c);
  const g = Math.round(sG + (eG - sG) * c);
  const b = Math.round(sB + (eB - sB) * c);
  return `rgb(${r},${g},${b})`;
}

const NEAR_WHITE = "#fefefe";

export type RegionFillProps = {
  src: string;
  palette: RegionPalette;
  /** 0-1: how much of the fill animation has progressed. */
  fillProgress: number;
  /** Per-region staggered start (0-1 of fillProgress). Defaults to all 0. */
  staggerStart?: Partial<Record<Region, number>>;
  /** How much of the fillProgress range each region uses to transition. */
  staggerWindow?: number;
  preserveAspect?: string;
  style?: React.CSSProperties;
  className?: string;
};

export const RegionFillSvg: React.FC<RegionFillProps> = ({
  src,
  palette,
  fillProgress,
  staggerStart,
  staggerWindow = 0.6,
  preserveAspect = "xMidYMid meet",
  style,
  className,
}) => {
  const [raw, setRaw] = useState<string>("");
  const [handle] = useState(() => delayRender(`RegionFillSvg ${src}`));

  useEffect(() => {
    let cancelled = false;
    const url = staticFile(src);
    (async () => {
      try {
        let xml = SVG_CACHE.get(url);
        if (!xml) {
          const r = await fetch(url);
          xml = await r.text();
          SVG_CACHE.set(url, xml);
        }
        if (cancelled) return;
        setRaw(xml);
        continueRender(handle);
      } catch {
        if (!cancelled) continueRender(handle);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [handle, src]);

  const processed = useMemo(() => {
    if (!raw) return "";
    return forceFill(raw, preserveAspect);
  }, [raw, preserveAspect]);

  // Compute per-region color at this fillProgress
  const cssVars: Record<string, string> = {};
  for (const region of REGIONS) {
    const target = palette[region];
    if (!target) {
      cssVars[`--reg-${region}`] = "rgb(254,254,254)";
      continue;
    }
    const start = staggerStart?.[region] ?? 0;
    const localT = (fillProgress - start) / staggerWindow;
    const tinted = lerpHex(NEAR_WHITE, target, localT);
    cssVars[`--reg-${region}`] = tinted;
  }

  return (
    <AbsoluteFill
      className={className}
      style={{
        ...style,
        ...(cssVars as unknown as React.CSSProperties),
      }}
      dangerouslySetInnerHTML={processed ? { __html: processed } : undefined}
    />
  );
};

// ── Per-beat palettes for the Hook section ───────────────────────────────

export const HOOK_REGION_PALETTES: Record<string, RegionPalette> = {
  // H-01 Belgian dock at dawn
  channelDawn: {
    sky: "#a8c4d4",
    ground: "#a8794a",
    "left-subject": "#5a3a3a",
    "center-subject": "#e8d4ba",
    "right-subject": "#d4ba8a",
  },
  // H-02 country road
  countryRoad: {
    sky: "#cae0ec",
    ground: "#7a8c4a",
    "left-subject": "#3a3a3a",
    "center-subject": "#a8794a",
    "right-subject": "#5a4a3a",
  },
  // H-03 Foreign Office door
  govtBuilding: {
    sky: "#d4c4a8",
    ground: "#5a4a3a",
    "left-subject": "#a8594a",
    "center-subject": "#d4b88a",
    "right-subject": "#5a4a3a",
  },
  // H-04 Prince Regent bedroom — candle warmth
  bedroom: {
    sky: "#3a2a4a",
    ground: "#5a3a2a",
    "left-subject": "#7a4a3a",
    "center-subject": "#e8b56a",
    "right-subject": "#d4a574",
  },
  // H-05 London dawn arrival
  londonDawn: {
    sky: "#a8c4d4",
    ground: "#7a6a5a",
    "left-subject": "#5a4a4a",
    "center-subject": "#a8593a",
    "right-subject": "#5a4a4a",
  },
  // H-06 Stock Exchange interior
  stockExchange: {
    sky: "#d4c4a8",
    ground: "#5a4a3a",
    "left-subject": "#3a3a4a",
    "center-subject": "#1a2840",
    "right-subject": "#7a6a5a",
  },
  // H-08 Thames sunset
  thamesSunset: {
    sky: "#e8a06a",
    ground: "#3a4a5a",
    "left-subject": "#5a4a3a",
    "center-subject": "#7a5a3a",
    "right-subject": "#c9a84c",
  },
  // H-10 Frankfurt night gate
  frankfurtNight: {
    sky: "#3a4a6a",
    ground: "#5a4a3a",
    "left-subject": "#3a2a2a",
    "center-subject": "#5a4a4a",
    "right-subject": "#5a4a4a",
  },
  // H-11 Mayer study candlelight
  mayerStudy: {
    sky: "#3a2a1a",
    ground: "#7a5a3a",
    "left-subject": "#3a2a1a",
    "center-subject": "#d4944a",
    "right-subject": "#3a2a1a",
  },
};

// Per-beat palettes for Chapter 1 — period sepia
export const CHAPTER1_REGION_PALETTES: Record<string, RegionPalette> = {
  judengasse1: {
    sky: "#3a3a4a",
    ground: "#5a4a3a",
    "left-subject": "#3a2a2a",
    "center-subject": "#7a5a3a",
    "right-subject": "#5a4a3a",
  },
  pavement: {
    sky: "#3a3a4a",
    ground: "#7a6a5a",
    "left-subject": "#3a2a2a",
    "center-subject": "#5a4a3a",
    "right-subject": "#7a6a4a",
  },
  judengasse2: {
    sky: "#3a3a4a",
    ground: "#5a4a3a",
    "left-subject": "#3a2a2a",
    "center-subject": "#7a5a3a",
    "right-subject": "#7a6a5a",
  },
  mayerDesk: {
    sky: "#1a1a1a",
    ground: "#5a4a3a",
    "left-subject": "#3a2a1a",
    "center-subject": "#d4944a",
    "right-subject": "#3a2a1a",
  },
  ledger: {
    sky: "#3a2a1a",
    ground: "#5a4a3a",
    "left-subject": "#7a5a3a",
    "center-subject": "#d4944a",
    "right-subject": "#7a5a3a",
  },
};
