/**
 * MMSvgV3 — line_art / vivid_shapes / bold_stroke aware loader.
 *
 * No recolor by default — the SVG comes from Recraft already in its locked style.
 * Just loads, forces it to fill the container, and renders.
 *
 * Optional: blob underlay for Chapter 1.
 */

import React, { useEffect, useMemo, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";

export const MM = {
  bg: "#080c16",
  cream: "#f5f0e4",
  parchment: "#efe5d0",
  gold: "#c9a84c",
  goldDim: "#8c6e23",
  blue: "#4a6fa5",
  red: "#b41e1e",
  ink: "#0d1a2a",
} as const;

const SVG_CACHE = new Map<string, string>();

/**
 * Force the SVG root to fill its parent container.
 * Recraft outputs SVGs with fixed width/height — strip those, force 100% scaling.
 */
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

/**
 * Strip the canvas-covering white rect — used for line_art assets that need
 * blobs UNDER the linework. Keeps inner counter-shapes intact.
 */
function stripCanvasBg(xml: string): string {
  return xml.replace(
    /<path d="M 0 0 L 2048 0 L 2048 2048 L 0 2048 L 0 0 z" fill="rgb\(25[0-5],25[0-5],25[0-5]\)"[^>]*><\/path>/g,
    ""
  );
}

type Props = {
  src: string;
  style?: React.CSSProperties;
  className?: string;
  preserveAspect?: string;
  stripBg?: boolean;
  blobUnderlay?: BlobConfig;
};

export type BlobConfig = {
  blobs: { cx: number; cy: number; rx: number; ry: number; color: string; opacity?: number; rotation?: number }[];
  blurStdDev?: number;
  blendMode?: string;
};

/**
 * Build the SVG <g> string for a blob underlay using the SVG's viewBox dimensions.
 */
function buildBlobLayer(config: BlobConfig, vw: number, vh: number, idSuffix: string): string {
  const blur = config.blurStdDev ?? 80;
  const blend = config.blendMode ?? "multiply";
  const blobs = config.blobs
    .map((b) => {
      const cx = b.cx * vw;
      const cy = b.cy * vh;
      const rx = b.rx * vw;
      const ry = b.ry * vh;
      const op = b.opacity ?? 0.55;
      const rot = b.rotation ?? 0;
      return `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${b.color}" opacity="${op}" filter="url(#blob-blur-${idSuffix})" transform="rotate(${rot} ${cx} ${cy})"/>`;
    })
    .join("");
  return `<g style="mix-blend-mode:${blend}"><defs><filter id="blob-blur-${idSuffix}" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="${blur}"/></filter></defs>${blobs}</g>`;
}

export const MMSvgV3: React.FC<Props> = ({
  src,
  style,
  className,
  preserveAspect = "xMidYMid meet",
  stripBg = false,
  blobUnderlay,
}) => {
  const [raw, setRaw] = useState<string>("");
  const [handle] = useState(() => delayRender(`MMSvgV3 ${src}`));

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
    let xml = raw;
    if (stripBg || blobUnderlay) {
      xml = stripCanvasBg(xml);
    }
    if (blobUnderlay) {
      // Insert blob layer right after the <svg> opening tag (renders behind)
      const m = /<svg\b[^>]*>/i.exec(xml);
      if (m) {
        const vbMatch = /viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"/.exec(m[0]);
        const vw = vbMatch ? parseFloat(vbMatch[1]) : 2048;
        const vh = vbMatch ? parseFloat(vbMatch[2]) : 2048;
        const blobs = buildBlobLayer(blobUnderlay, vw, vh, src.replace(/[^a-z0-9]/gi, ""));
        xml = xml.slice(0, m.index + m[0].length) + blobs + xml.slice(m.index + m[0].length);
      }
    }
    xml = forceFill(xml, preserveAspect);
    return xml;
  }, [raw, stripBg, blobUnderlay, preserveAspect, src]);

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
      dangerouslySetInnerHTML={processed ? { __html: processed } : undefined}
    />
  );
};

export const v3lib = (filename: string) => `svg-library/v3/${filename}`;
