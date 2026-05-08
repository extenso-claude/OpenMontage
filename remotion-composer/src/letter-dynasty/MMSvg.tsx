/**
 * Midnight Magnates SVG loader + recolor.
 *
 * Recraft generates pure black-and-white engraving SVGs. This component loads
 * one, swaps black/white for MM palette colors, and renders it inline.
 *
 * Black-and-white in -> Midnight Magnates colors out. One source asset, many
 * possible color treatments per scene context.
 */

import React, { useEffect, useMemo, useState } from "react";
import {
  continueRender,
  delayRender,
  staticFile,
} from "remotion";

export const MM = {
  bg: "#080c16",
  cream: "#f5f0e4",
  gold: "#c9a84c",
  goldDim: "#8c6e23",
  blue: "#4a6fa5",
  red: "#b41e1e",
  ink: "#0d1a2a",
  stormGray: "#3a3a4a",
  blueDeep: "#1a2840",
} as const;

export type RecolorMode =
  | "navy-cream" //  default — black->bg, white->cream
  | "cream-on-navy" //  same as navy-cream, semantic alias
  | "gold-on-navy" //  black->bg, white->gold
  | "blue-on-navy" //  black->bg, white->cool blue
  | "navy-gold" //  black->bg, white->gold (alias)
  | "ink-cream" //  black->ink, white->cream (slightly lighter bg)
  | "silhouette" //  black stays, white->bg (silhouette only on plate)
  | "ghost" //  black->cream@40, white->cream (faint)
  | "shadow"; //  black->cream@70, white->bg (low contrast)

function resolveTints(mode: RecolorMode): { black: string; white: string } {
  switch (mode) {
    case "navy-cream":
    case "cream-on-navy":
      return { black: MM.bg, white: MM.cream };
    case "gold-on-navy":
    case "navy-gold":
      return { black: MM.bg, white: MM.gold };
    case "blue-on-navy":
      return { black: MM.bg, white: MM.blue };
    case "ink-cream":
      return { black: MM.ink, white: MM.cream };
    case "silhouette":
      return { black: MM.cream, white: MM.bg };
    case "ghost":
      return { black: "rgba(245,240,228,0.32)", white: MM.cream };
    case "shadow":
      return { black: "rgba(245,240,228,0.70)", white: MM.bg };
    default:
      return { black: MM.bg, white: MM.cream };
  }
}

const SVG_CACHE = new Map<string, string>();

function recolorXml(xml: string, black: string, white: string): string {
  // Recraft outputs rgb(0,0,0) and rgb(255,255,255) — also catch hex variants
  let out = xml
    .replace(/rgb\(\s*0\s*,\s*0\s*,\s*0\s*\)/g, black)
    .replace(/rgb\(\s*255\s*,\s*255\s*,\s*255\s*\)/g, white)
    .replace(/#000000\b/gi, black)
    .replace(/#ffffff\b/gi, white)
    .replace(/="#000"/gi, `="${black}"`)
    .replace(/="#fff"/gi, `="${white}"`);
  // Force SVG root to fill its container — strip baked width/height attrs.
  out = out.replace(/<svg\b([^>]*)>/i, (_match, attrs: string) => {
    const cleaned = attrs
      .replace(/\s+width\s*=\s*"[^"]*"/gi, "")
      .replace(/\s+height\s*=\s*"[^"]*"/gi, "")
      .replace(/\s+style\s*=\s*"[^"]*"/gi, "");
    return `<svg${cleaned} width="100%" height="100%" style="display:block;width:100%;height:100%">`;
  });
  return out;
}

export const svgLib = (filename: string): string => `svg-library/${filename}`;

type Props = {
  src: string;
  mode?: RecolorMode;
  style?: React.CSSProperties;
  className?: string;
  preserveAspectRatio?: string;
};

export const MMSvg: React.FC<Props> = ({
  src,
  mode = "navy-cream",
  style,
  className,
  preserveAspectRatio = "xMidYMid meet",
}) => {
  const [raw, setRaw] = useState<string>("");
  const [handle] = useState(() => delayRender(`MMSvg ${src}`));

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
        // Apply preserveAspectRatio override
        xml = xml.replace(
          /preserveAspectRatio="[^"]*"/,
          `preserveAspectRatio="${preserveAspectRatio}"`
        );
        setRaw(xml);
        continueRender(handle);
      } catch (e) {
        if (!cancelled) {
          continueRender(handle);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [handle, src, preserveAspectRatio]);

  const tinted = useMemo(() => {
    if (!raw) return "";
    const { black, white } = resolveTints(mode);
    return recolorXml(raw, black, white);
  }, [raw, mode]);

  return (
    <div
      className={className}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        ...style,
      }}
      dangerouslySetInnerHTML={tinted ? { __html: tinted } : undefined}
    />
  );
};

/**
 * Light shaft overlay — single shaft from upper-left, soft falloff.
 * Use over assets to add the playbook-mandated single shaft.
 */
export const LightShaft: React.FC<{
  intensity?: number;
  color?: string;
  origin?: "upper-left" | "upper-right" | "above";
}> = ({ intensity = 0.4, color = MM.blue, origin = "upper-left" }) => {
  const transform =
    origin === "upper-left"
      ? "rotate(25deg) translate(-30%, -10%)"
      : origin === "upper-right"
      ? "rotate(-25deg) translate(30%, -10%)"
      : "translate(0, -10%)";
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `linear-gradient(180deg, ${color}00 0%, ${color}${Math.round(
          intensity * 70
        )
          .toString(16)
          .padStart(2, "0")} 30%, ${color}00 70%)`,
        mixBlendMode: "screen",
        transform,
        transformOrigin: "top left",
        pointerEvents: "none",
      }}
    />
  );
};

/**
 * Vignette dimmer — softens edges, helps focus, channel-signature mood.
 */
export const Vignette: React.FC<{ intensity?: number }> = ({ intensity = 0.7 }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      background: `radial-gradient(ellipse at center, transparent 35%, rgba(0,0,0,${intensity}) 100%)`,
      pointerEvents: "none",
    }}
  />
);

/**
 * Film grain — animated subtle noise. Sleep-network signature.
 */
export const Grain: React.FC<{ frame: number; opacity?: number }> = ({
  frame,
  opacity = 0.04,
}) => {
  const seed = (frame * 13) % 7;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E\")",
        transform: `translate(${seed}px, ${(seed * 7) % 5}px)`,
        pointerEvents: "none",
      }}
    />
  );
};
