/**
 * MapAnnotation — overlay animated annotations on a real map image.
 *
 * Replaces the deprecated AnimatedMap. Geographic truth comes from the source
 * image (channel-styled, AI-generated or sourced from Wikimedia). All annotations
 * (pins, circles, route arcs, sprites, region labels, color overlays, pulses) are
 * positioned in normalized 0–1 space over that image, so coordinates always map
 * to real geography.
 *
 * Supports a camera transform over the scene duration (zoom in/out, pan) by
 * interpolating from `cameraStart` to `cameraEnd`. Both default to "no zoom"
 * (focal at 0.5,0.5, zoom 1), in which case the map fills the screen statically.
 *
 * @version 0.1.0
 */
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BrandTheme, resolveTheme } from "./theme";

// ─── Annotation types ─────────────────────────────────────────────────

interface AnnotationBase {
  /** When (seconds from scene start) the annotation begins animating in. */
  revealAtSeconds?: number;
  /** How long the annotation is visible in total (default = until end of scene). */
  durationSeconds?: number;
}

export interface MapPoint {
  /** x in 0–1 normalized map space (0 = left edge, 1 = right edge). */
  x: number;
  /** y in 0–1 normalized map space (0 = top edge, 1 = bottom edge). */
  y: number;
  /** Optional label rendered next to a pin / pulse. */
  label?: string;
}

export interface PinAnnotation extends AnnotationBase {
  type: "pin";
  position: MapPoint;
}

export interface CircleAnnotation extends AnnotationBase {
  type: "circle";
  center: MapPoint;
  /** Radius in 0–1 map-space units (e.g., 0.05 = 5% of map width). */
  radius: number;
  /** Hand-drawn scribble style (loose, multi-pass) vs clean single circle. */
  scribble?: boolean;
  label?: string;
}

export interface RouteArcAnnotation extends AnnotationBase {
  type: "route_arc";
  /** Sequence of waypoints. Path is drawn through them in order. */
  waypoints: MapPoint[];
  /** Optional sprite glyph that travels along the path (e.g., "✈", "⚓", "🐎"). */
  sprite?: string;
  /** Curvature 0..1 of bezier between segments. Default 0.22. */
  curvature?: number;
}

export interface RegionLabelAnnotation extends AnnotationBase {
  type: "region_label";
  position: MapPoint;
  text: string;
  /** Font size in pixels (in screen space, not map space). Default 24. */
  fontSize?: number;
}

export interface ColorOverlayAnnotation extends AnnotationBase {
  type: "color_overlay";
  /**
   * SVG path data with coordinates in 0–1 map space, scaled to map at render.
   * Example for a polygon: "M 0.40,0.30 L 0.60,0.30 L 0.55,0.55 L 0.42,0.55 Z"
   */
  polygonPath: string;
  /** Override fill color. Defaults to theme.accent. */
  color?: string;
  /** Direction of animation: rise = grow outward from center, fall = shrink inward. */
  direction?: "rise" | "fall";
}

export interface PulseAnnotation extends AnnotationBase {
  type: "pulse";
  position: MapPoint;
  /** Override pulse color. Defaults to theme.accent. */
  color?: string;
}

export type Annotation =
  | PinAnnotation
  | CircleAnnotation
  | RouteArcAnnotation
  | RegionLabelAnnotation
  | ColorOverlayAnnotation
  | PulseAnnotation;

// ─── Camera ────────────────────────────────────────────────────────────

export interface CameraState {
  /** Focal point in 0–1 map space. (0.5, 0.5) = center. */
  focalX: number;
  focalY: number;
  /** Zoom multiplier. 1 = fit, 2 = 2x zoom. */
  zoom: number;
}

const DEFAULT_CAMERA: CameraState = { focalX: 0.5, focalY: 0.5, zoom: 1 };

// ─── Component ─────────────────────────────────────────────────────────

export interface MapAnnotationProps {
  /** Public URL or staticFile() path to the map image. */
  mapSrc: string;
  /** Annotations to overlay (in 0–1 map space). */
  annotations?: Annotation[];
  /** Optional title/caption shown above or below the map. */
  title?: string;
  /** Camera at the start of the scene. */
  cameraStart?: CameraState;
  /** Camera at the end of the scene. Interpolates from start. */
  cameraEnd?: CameraState;
  /** Total duration of the scene in frames. Default = 7s @ fps. */
  durationFrames?: number;
  /** Optional brightness filter applied to the underlying map (0–1). Default 0.92. */
  mapBrightness?: number;
  /**
   * Strip near-duplicate pin/region/pulse annotations before rendering.
   * Two annotations within `dedupeMinDistance` of each other (in normalized
   * 0–1 space) and sharing the same label are collapsed to the first.
   * Default true. Disable for intentional same-label overlays.
   */
  autoDedupe?: boolean;
  /** Min distance for autoDedupe in normalized 0–1 space. Default 0.02 (2% of map width). */
  dedupeMinDistance?: number;
  theme?: Partial<BrandTheme>;
}

/**
 * Remove near-duplicate point annotations (pin, region_label, pulse) that
 * share the same label within `minDistance` of each other. Useful when the
 * asset director has redundant entries — e.g. two "London" pins at slightly
 * different lat/lon. Returns a new array; original is untouched.
 */
export function dedupePins(
  annotations: Annotation[],
  minDistance = 0.02,
): Annotation[] {
  const kept: Annotation[] = [];
  const seen: { label: string; x: number; y: number }[] = [];

  const readPoint = (a: Annotation): { label?: string; x: number; y: number } | null => {
    if (a.type === "pin") return { label: a.position.label, x: a.position.x, y: a.position.y };
    if (a.type === "pulse") return { label: a.position.label, x: a.position.x, y: a.position.y };
    if (a.type === "region_label") return { label: a.text, x: a.position.x, y: a.position.y };
    return null;
  };

  for (const a of annotations) {
    const pt = readPoint(a);
    if (!pt || !pt.label) {
      kept.push(a);
      continue;
    }
    const dup = seen.find(
      (s) =>
        s.label.toLowerCase() === pt.label!.toLowerCase() &&
        Math.hypot(s.x - pt.x, s.y - pt.y) < minDistance,
    );
    if (dup) continue;
    seen.push({ label: pt.label, x: pt.x, y: pt.y });
    kept.push(a);
  }
  return kept;
}

export const MapAnnotation: React.FC<MapAnnotationProps> = ({
  mapSrc,
  annotations = [],
  title,
  cameraStart = DEFAULT_CAMERA,
  cameraEnd = DEFAULT_CAMERA,
  durationFrames,
  mapBrightness = 0.92,
  autoDedupe = true,
  dedupeMinDistance = 0.02,
  theme: themeOverride,
}) => {
  const renderAnnotations = autoDedupe
    ? dedupePins(annotations, dedupeMinDistance)
    : annotations;
  const frame = useCurrentFrame();
  const { fps, width: vw, height: vh } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 7 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Camera interpolation — ease-out cubic
  const t = interpolate(frame, [0, total], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - t, 3);

  const cam = {
    focalX: cameraStart.focalX + (cameraEnd.focalX - cameraStart.focalX) * eased,
    focalY: cameraStart.focalY + (cameraEnd.focalY - cameraStart.focalY) * eased,
    zoom: cameraStart.zoom + (cameraEnd.zoom - cameraStart.zoom) * eased,
  };

  // Compute transform that places focalX,focalY at viewport center.
  // Map element is sized to vw × vh, scaled by cam.zoom from its top-left origin.
  // We translate so the focal point sits at viewport center.
  const tx = vw / 2 - cam.focalX * vw * cam.zoom;
  const ty = vh / 2 - cam.focalY * vh * cam.zoom;

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity,
        overflow: "hidden",
      }}
    >
      {/* Camera-transformed wrapper: contains the map AND all annotations together. */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: vw,
          height: vh,
          transform: `translate(${tx}px, ${ty}px) scale(${cam.zoom})`,
          transformOrigin: "0 0",
        }}
      >
        <Img
          src={mapSrc}
          style={{
            width: vw,
            height: vh,
            objectFit: "cover",
            filter: `brightness(${mapBrightness})`,
            display: "block",
          }}
        />

        {/* Annotation SVG overlay, sized to match the map. */}
        <svg
          viewBox={`0 0 ${vw} ${vh}`}
          width={vw}
          height={vh}
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            pointerEvents: "none",
          }}
        >
          {renderAnnotations.map((a, i) => {
            const reveal = (a.revealAtSeconds ?? 0) * fps;
            return (
              <AnnotationRenderer
                key={i}
                annotation={a}
                theme={theme}
                vw={vw}
                vh={vh}
                frame={frame}
                fps={fps}
                revealFrame={reveal}
              />
            );
          })}
        </svg>
      </div>

      {/* Title (in screen space, NOT camera-transformed) */}
      {title ? (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: theme.fontHeading,
            fontSize: 42,
            fontWeight: 700,
            color: theme.accent,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            background: `linear-gradient(180deg, ${theme.bg}EE 0%, ${theme.bg}AA 60%, transparent 100%)`,
            padding: "44px 80px 60px",
            pointerEvents: "none",
            textShadow: `0 2px 12px ${theme.bg}`,
          }}
        >
          {title}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// ─── Annotation renderers ──────────────────────────────────────────────

const AnnotationRenderer: React.FC<{
  annotation: Annotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ annotation, theme, vw, vh, frame, fps, revealFrame }) => {
  switch (annotation.type) {
    case "pin":
      return (
        <PinAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
    case "circle":
      return (
        <CircleAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
    case "route_arc":
      return (
        <RouteArcAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
    case "region_label":
      return (
        <RegionLabelAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
    case "color_overlay":
      return (
        <ColorOverlayAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
    case "pulse":
      return (
        <PulseAnno
          a={annotation}
          theme={theme}
          vw={vw}
          vh={vh}
          frame={frame}
          fps={fps}
          revealFrame={revealFrame}
        />
      );
  }
};

// pin
const PinAnno: React.FC<{
  a: PinAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const drop = interpolate(local, [0, 14], [-30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(local, [0, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const ring = interpolate(local, [12, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x = a.position.x * vw;
  const y = a.position.y * vh;

  return (
    <g transform={`translate(0, ${drop})`}>
      <circle cx={x} cy={y} r={11 * scale} fill={theme.accent} />
      <circle cx={x} cy={y} r={11 * scale + 2} fill="none" stroke={theme.bg} strokeWidth={2} />
      <circle
        cx={x}
        cy={y}
        r={20 + ring * 24}
        fill="none"
        stroke={theme.accent}
        strokeOpacity={Math.max(0, 1 - ring)}
        strokeWidth={3}
      />
      {a.position.label && scale > 0.6 ? (
        <text
          x={x + 28}
          y={y + 10}
          fontSize={32}
          fontFamily={theme.fontHeading}
          fontWeight={800}
          fill={theme.text}
          stroke={theme.bg}
          strokeWidth={7}
          paintOrder="stroke"
          opacity={(scale - 0.6) / 0.4}
          letterSpacing="0.02em"
        >
          {a.position.label}
        </text>
      ) : null}
    </g>
  );
};

// circle
const CircleAnno: React.FC<{
  a: CircleAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, fps, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const draw = interpolate(local, [0, fps * 0.7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cx = a.center.x * vw;
  const cy = a.center.y * vh;
  const r = a.radius * Math.min(vw, vh);

  if (a.scribble) {
    // Hand-drawn scribble — 3 overlapping circles at slight offsets and rotations
    const passes = [0, 1, 2];
    return (
      <g>
        {passes.map((i) => {
          const passDraw = Math.max(0, Math.min(1, (draw - i * 0.1) / 0.9));
          if (passDraw <= 0) return null;
          const offsetX = [0, -3, 2.5][i]!;
          const offsetY = [0, 2, -2.5][i]!;
          const rotation = [0, -3, 5][i]!;
          const radiusVar = r * [1, 0.97, 1.03][i]!;
          const circumference = 2 * Math.PI * radiusVar;
          return (
            <circle
              key={i}
              cx={cx + offsetX}
              cy={cy + offsetY}
              r={radiusVar}
              fill="none"
              stroke={theme.accent}
              strokeWidth={3.5}
              strokeDasharray={`${circumference}`}
              strokeDashoffset={(1 - passDraw) * circumference}
              strokeLinecap="round"
              transform={`rotate(${rotation} ${cx} ${cy})`}
              style={{ filter: `drop-shadow(0 0 10px ${theme.accent}88)` }}
            />
          );
        })}
        {a.label && draw > 0.7 ? (
          <text
            x={cx}
            y={cy - r - 22}
            fontSize={32}
            fontFamily={theme.fontHeading}
            fill={theme.accent}
            stroke={theme.bg}
            strokeWidth={7}
            paintOrder="stroke"
            textAnchor="middle"
            opacity={(draw - 0.7) / 0.3}
            fontWeight={700}
            letterSpacing="0.05em"
          >
            {a.label}
          </text>
        ) : null}
      </g>
    );
  }

  // Clean single circle — animates via stroke-dashoffset
  const circumference = 2 * Math.PI * r;
  return (
    <g>
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={theme.accent}
        strokeWidth={4.5}
        strokeDasharray={`${circumference}`}
        strokeDashoffset={(1 - draw) * circumference}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ filter: `drop-shadow(0 0 12px ${theme.accent}AA)` }}
      />
      {a.label && draw > 0.7 ? (
        <text
          x={cx}
          y={cy - r - 22}
          fontSize={32}
          fontFamily={theme.fontHeading}
          fill={theme.accent}
          stroke={theme.bg}
          strokeWidth={7}
          paintOrder="stroke"
          textAnchor="middle"
          opacity={(draw - 0.7) / 0.3}
          fontWeight={700}
          letterSpacing="0.05em"
        >
          {a.label}
        </text>
      ) : null}
    </g>
  );
};

// route_arc
const RouteArcAnno: React.FC<{
  a: RouteArcAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, fps, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const draw = interpolate(local, [0, fps * 1.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const curvature = a.curvature ?? 0.22;

  // Convert waypoints to absolute coords
  const pts = a.waypoints.map((w) => ({ x: w.x * vw, y: w.y * vh, label: w.label }));
  if (pts.length < 2) return null;

  // Build path as concatenated quadratic beziers
  let pathD = `M ${pts[0]!.x} ${pts[0]!.y}`;
  const segments: { from: typeof pts[0]; to: typeof pts[0]; cx: number; cy: number }[] = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p1 = pts[i]!;
    const p2 = pts[i + 1]!;
    const mx = (p1.x + p2.x) / 2;
    const my = (p1.y + p2.y) / 2;
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const cx = mx - dy * curvature;
    const cy = my + dx * curvature;
    pathD += ` Q ${cx} ${cy} ${p2.x} ${p2.y}`;
    segments.push({ from: p1, to: p2, cx, cy });
  }

  // Estimate path length for stroke-dashoffset
  // Approximate with chord length + curvature factor
  let estLength = 0;
  for (const seg of segments) {
    const chord = Math.hypot(seg.to.x - seg.from.x, seg.to.y - seg.from.y);
    estLength += chord * 1.1;
  }

  // Sprite position along path — pick which segment at this draw progress
  const spritePos = (() => {
    if (!a.sprite || draw === 0) return null;
    const totalLen = segments.reduce((s, seg) => s + Math.hypot(seg.to.x - seg.from.x, seg.to.y - seg.from.y), 0);
    let traversed = totalLen * draw;
    for (const seg of segments) {
      const len = Math.hypot(seg.to.x - seg.from.x, seg.to.y - seg.from.y);
      if (traversed <= len) {
        const t = traversed / len;
        // Quadratic bezier point
        const px = (1 - t) * (1 - t) * seg.from.x + 2 * (1 - t) * t * seg.cx + t * t * seg.to.x;
        const py = (1 - t) * (1 - t) * seg.from.y + 2 * (1 - t) * t * seg.cy + t * t * seg.to.y;
        // Tangent for rotation
        const tx = 2 * (1 - t) * (seg.cx - seg.from.x) + 2 * t * (seg.to.x - seg.cx);
        const ty = 2 * (1 - t) * (seg.cy - seg.from.y) + 2 * t * (seg.to.y - seg.cy);
        const angle = (Math.atan2(ty, tx) * 180) / Math.PI;
        return { x: px, y: py, angle };
      }
      traversed -= len;
    }
    const last = segments[segments.length - 1]!.to;
    return { x: last.x, y: last.y, angle: 0 };
  })();

  return (
    <g>
      <path
        d={pathD}
        fill="none"
        stroke={theme.accent}
        strokeWidth={5}
        strokeDasharray="10 10"
        strokeDashoffset={(1 - draw) * estLength}
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 10px ${theme.accent}99)` }}
      />
      {/* Origin pin */}
      <circle cx={pts[0]!.x} cy={pts[0]!.y} r={11} fill={theme.accent} />
      <circle cx={pts[0]!.x} cy={pts[0]!.y} r={13} fill="none" stroke={theme.bg} strokeWidth={2} />
      {pts[0]!.label ? (
        <text
          x={pts[0]!.x + 26}
          y={pts[0]!.y - 16}
          fontSize={32}
          fontFamily={theme.fontHeading}
          fontWeight={800}
          fill={theme.text}
          stroke={theme.bg}
          strokeWidth={7}
          paintOrder="stroke"
          letterSpacing="0.02em"
        >
          {pts[0]!.label}
        </text>
      ) : null}
      {/* Endpoint pin (revealed when route completes) */}
      {draw >= 0.95 ? (
        <>
          <circle cx={pts[pts.length - 1]!.x} cy={pts[pts.length - 1]!.y} r={11} fill={theme.accent} />
          <circle cx={pts[pts.length - 1]!.x} cy={pts[pts.length - 1]!.y} r={13} fill="none" stroke={theme.bg} strokeWidth={2} />
          {pts[pts.length - 1]!.label ? (
            <text
              x={pts[pts.length - 1]!.x + 26}
              y={pts[pts.length - 1]!.y - 16}
              fontSize={32}
              fontFamily={theme.fontHeading}
              fontWeight={800}
              fill={theme.text}
              stroke={theme.bg}
              strokeWidth={7}
              paintOrder="stroke"
              letterSpacing="0.02em"
            >
              {pts[pts.length - 1]!.label}
            </text>
          ) : null}
        </>
      ) : null}
      {/* Intermediate waypoints */}
      {pts.slice(1, -1).map((p, i) => {
        const visible = draw > (i + 1) / pts.length;
        return (
          <g key={i} opacity={visible ? 1 : 0}>
            <circle cx={p.x} cy={p.y} r={8} fill={theme.accent} />
            <circle cx={p.x} cy={p.y} r={9.5} fill="none" stroke={theme.bg} strokeWidth={1.5} />
            {p.label && visible ? (
              <text
                x={p.x + 22}
                y={p.y - 12}
                fontSize={26}
                fontFamily={theme.fontHeading}
                fontWeight={800}
                fill={theme.text}
                stroke={theme.bg}
                strokeWidth={6}
                paintOrder="stroke"
              >
                {p.label}
              </text>
            ) : null}
          </g>
        );
      })}
      {/* Sprite — bigger + glow */}
      {spritePos && a.sprite ? (
        <g transform={`rotate(${spritePos.angle} ${spritePos.x} ${spritePos.y})`}>
          <circle cx={spritePos.x} cy={spritePos.y} r={26} fill={theme.bg} fillOpacity={0.85} />
          <text
            x={spritePos.x}
            y={spritePos.y + 16}
            fontSize={44}
            textAnchor="middle"
            fill={theme.accent}
            stroke={theme.bg}
            strokeWidth={3}
            paintOrder="stroke"
            style={{ filter: `drop-shadow(0 0 8px ${theme.accent}AA)` }}
          >
            {a.sprite}
          </text>
        </g>
      ) : null}
    </g>
  );
};

// region_label
const RegionLabelAnno: React.FC<{
  a: RegionLabelAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, fps, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const fade = interpolate(local, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x = a.position.x * vw;
  const y = a.position.y * vh;
  const fontSize = a.fontSize ?? 44;

  return (
    <g opacity={fade}>
      <text
        x={x}
        y={y}
        fontSize={fontSize}
        fontFamily={theme.fontHeading}
        fill={theme.accent}
        stroke={theme.bg}
        strokeWidth={8}
        paintOrder="stroke"
        textAnchor="middle"
        fontWeight={700}
        letterSpacing="0.10em"
        style={{ textTransform: "uppercase" }}
      >
        {a.text}
      </text>
    </g>
  );
};

// color_overlay
const ColorOverlayAnno: React.FC<{
  a: ColorOverlayAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, fps, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const direction = a.direction ?? "rise";
  const t = interpolate(local, [0, fps * 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - t, 2);
  const scale = direction === "rise" ? eased : 1 - eased;
  const fillOpacity = (direction === "rise" ? eased : Math.max(0, 1 - eased * 0.85)) * 0.65;

  // Convert path coordinates from 0–1 space → pixel space.
  // Replace each pair of numbers in the path; we expect simple M/L/Z/Q syntax.
  const scaledPath = a.polygonPath.replace(
    /([MLQTC])\s*([\d.]+)[\s,]+([\d.]+)/gi,
    (_match, cmd, xStr, yStr) => {
      const x = parseFloat(xStr) * vw;
      const y = parseFloat(yStr) * vh;
      return `${cmd} ${x.toFixed(2)} ${y.toFixed(2)}`;
    }
  );

  const color = a.color ?? theme.accent;
  return (
    <g style={{ transformOrigin: "center", transform: `scale(${scale})` }}>
      <path
        d={scaledPath}
        fill={color}
        fillOpacity={fillOpacity}
        stroke={color}
        strokeOpacity={Math.min(1, fillOpacity * 1.5)}
        strokeWidth={3.5}
      />
    </g>
  );
};

// pulse
const PulseAnno: React.FC<{
  a: PulseAnnotation;
  theme: BrandTheme;
  vw: number;
  vh: number;
  frame: number;
  fps: number;
  revealFrame: number;
}> = ({ a, theme, vw, vh, frame, fps, revealFrame }) => {
  const local = frame - revealFrame;
  if (local < 0) return null;
  const x = a.position.x * vw;
  const y = a.position.y * vh;
  const color = a.color ?? theme.accent;
  // Continuous pulse — period ~1.5s
  const cycle = (local / fps) % 1.5;
  const pulse = cycle / 1.5;
  return (
    <g>
      <circle cx={x} cy={y} r={11} fill={color} />
      <circle cx={x} cy={y} r={13} fill="none" stroke={theme.bg} strokeWidth={2} />
      <circle
        cx={x}
        cy={y}
        r={13 + pulse * 32}
        fill="none"
        stroke={color}
        strokeOpacity={Math.max(0, 1 - pulse)}
        strokeWidth={3.5}
      />
      {a.position.label ? (
        <text
          x={x + 28}
          y={y + 10}
          fontSize={32}
          fontFamily={theme.fontHeading}
          fontWeight={800}
          fill={theme.text}
          stroke={theme.bg}
          strokeWidth={7}
          paintOrder="stroke"
        >
          {a.position.label}
        </text>
      ) : null}
    </g>
  );
};
