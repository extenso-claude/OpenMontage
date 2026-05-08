/**
 * AnimatedMap — DEPRECATED. Use {@link MapAnnotation} instead.
 *
 * Brand review feedback (May 2026): the synthetic 1000×500 viewBox space gave
 * us no real geography, and pins frequently landed in oceans. Replaced by
 * MapAnnotation, which overlays annotations on a real channel-styled map
 * image so positions are tied to actual geography.
 *
 * This file is kept only for historical fixtures that haven't been migrated
 * yet. Do not author new scenes against it. The symbol is no longer
 * re-exported from `components/brand/index.ts`.
 *
 *   - world_route   : dotted line traces a path across continents, pin lands at endpoint
 *   - region_zoom   : camera zooms from world view → target region with optional labels
 *   - pin_drop      : pins drop sequentially at named coordinates
 *   - empire_extent : shaded territory polygon animates outward (rise) or inward (fall)
 *
 * @deprecated Use MapAnnotation. Slated for removal once existing fixtures migrate.
 * @version 0.2.0
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { BrandTheme, resolveTheme } from "./theme";
import { WorldMapBase } from "./WorldMapBase";

export type AnimatedMapVariant =
  | "world_route"
  | "region_zoom"
  | "pin_drop"
  | "empire_extent";

export interface MapPoint {
  /** x in 0–1000 viewBox space. */
  x: number;
  /** y in 0–500 viewBox space. */
  y: number;
  /** Visible label. */
  label?: string;
}

export interface WorldRouteConfig {
  variant: "world_route";
  origin: MapPoint;
  destination: MapPoint;
  /** Extra waypoints between origin and destination. */
  waypoints?: MapPoint[];
  /** Continents to highlight beneath the route. */
  highlightContinents?: number[];
}

export interface RegionZoomConfig {
  variant: "region_zoom";
  /** Center of zoom in viewBox coords. */
  target: MapPoint;
  /** Final zoom factor. 1 = no zoom; 4 = 4x. Default 3. */
  endZoom?: number;
  /** Continents to highlight at full zoom. */
  highlightContinents?: number[];
}

export interface PinDropConfig {
  variant: "pin_drop";
  pins: MapPoint[];
  /** Frames between sequential drops. Default = fps × 1.5 (1.5s). */
  staggerFrames?: number;
}

export interface EmpireExtentConfig {
  variant: "empire_extent";
  /** Polygon path in viewBox coords (e.g., "M 470,110 L ..."). */
  territoryPath: string;
  /** "rise" grows outward from a center; "fall" shrinks inward. */
  direction?: "rise" | "fall";
}

export type AnimatedMapConfig =
  | WorldRouteConfig
  | RegionZoomConfig
  | PinDropConfig
  | EmpireExtentConfig;

export interface AnimatedMapProps {
  config: AnimatedMapConfig;
  /** Total frames the component is on screen (including fades). Default = 6s @ fps. */
  durationFrames?: number;
  theme?: Partial<BrandTheme>;
  /** Title/caption shown above the map. */
  title?: string;
}

// Quadratic-bezier path between two points with curvature
function bezierPath(p1: MapPoint, p2: MapPoint, curvature = 0.25): string {
  const mx = (p1.x + p2.x) / 2;
  const my = (p1.y + p2.y) / 2;
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  // perpendicular offset for curve
  const cx = mx - dy * curvature;
  const cy = my + dx * curvature;
  return `M ${p1.x} ${p1.y} Q ${cx} ${cy} ${p2.x} ${p2.y}`;
}

export const AnimatedMap: React.FC<AnimatedMapProps> = ({
  config,
  durationFrames,
  title,
  theme: themeOverride,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(themeOverride);

  const fadeFrames = theme.fadeFrames ?? 36;
  const total = durationFrames ?? 6 * fps;
  const fadeOutStart = total - fadeFrames;

  const opacity = interpolate(frame, [0, fadeFrames, fadeOutStart, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity,
        padding: 64,
      }}
    >
      {title ? (
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: theme.headingWeight ?? 700,
            fontSize: 32,
            color: theme.accent,
            letterSpacing: "0.05em",
            marginBottom: 24,
            textTransform: "uppercase",
          }}
        >
          {title}
        </div>
      ) : null}
      <MapVariant config={config} theme={theme} frame={frame} fps={fps} total={total} />
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// Variant dispatch
// ─────────────────────────────────────────────────────────────────────────

interface MapVariantProps {
  config: AnimatedMapConfig;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}

const MapVariant: React.FC<MapVariantProps> = ({ config, theme, frame, fps, total }) => {
  switch (config.variant) {
    case "world_route":
      return <WorldRoute config={config} theme={theme} frame={frame} fps={fps} total={total} />;
    case "region_zoom":
      return <RegionZoom config={config} theme={theme} frame={frame} fps={fps} total={total} />;
    case "pin_drop":
      return <PinDrop config={config} theme={theme} frame={frame} fps={fps} total={total} />;
    case "empire_extent":
      return <EmpireExtent config={config} theme={theme} frame={frame} fps={fps} total={total} />;
  }
};

// ─────────────────────────────────────────────────────────────────────────
// world_route
// ─────────────────────────────────────────────────────────────────────────

const WorldRoute: React.FC<{
  config: WorldRouteConfig;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ config, theme, frame, total }) => {
  const reveal = interpolate(frame, [10, total - 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Build a sequence of bezier segments through waypoints
  const points = [config.origin, ...(config.waypoints ?? []), config.destination];
  const segments = [];
  for (let i = 0; i < points.length - 1; i++) {
    segments.push(bezierPath(points[i]!, points[i + 1]!, 0.22));
  }

  // Compute total path length per segment to support reveal
  const fullPath = segments.join(" ");

  return (
    <div style={{ position: "relative" }}>
      <WorldMapBase
        theme={theme}
        highlightIndices={config.highlightContinents}
      />
      <svg
        viewBox="0 0 1000 500"
        width={1100}
        height={550}
        style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
      >
        <path
          d={fullPath}
          fill="none"
          stroke={theme.accent}
          strokeWidth={3}
          strokeDasharray="6 8"
          strokeDashoffset={`${(1 - reveal) * 800}`}
          style={{ filter: `drop-shadow(0 0 8px ${theme.accent}88)` }}
        />
        {/* Origin pin */}
        <Pin point={config.origin} theme={theme} appear={frame > 0} />
        {/* Destination pin appears once route is mostly drawn */}
        {reveal > 0.85 ? (
          <Pin point={config.destination} theme={theme} appear={true} />
        ) : null}
      </svg>
    </div>
  );
};

const Pin: React.FC<{ point: MapPoint; theme: BrandTheme; appear: boolean }> = ({
  point,
  theme,
  appear,
}) => {
  if (!appear) return null;
  return (
    <g>
      <circle cx={point.x} cy={point.y} r={6} fill={theme.accent} />
      <circle
        cx={point.x}
        cy={point.y}
        r={12}
        fill="none"
        stroke={theme.accent}
        strokeOpacity={0.6}
        strokeWidth={1.5}
      />
      {point.label ? (
        <text
          x={point.x + 14}
          y={point.y + 4}
          fontSize={14}
          fontFamily={theme.fontBody}
          fill={theme.text}
          stroke={theme.bg}
          strokeWidth={3}
          paintOrder="stroke"
        >
          {point.label}
        </text>
      ) : null}
    </g>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// region_zoom
// ─────────────────────────────────────────────────────────────────────────

const RegionZoom: React.FC<{
  config: RegionZoomConfig;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ config, theme, frame, total }) => {
  const endZoom = config.endZoom ?? 3;
  const t = interpolate(frame, [0, total], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // ease-out cubic
  const eased = 1 - Math.pow(1 - t, 3);
  const zoom = 1 + (endZoom - 1) * eased;

  // Zoom around target — translate so target stays visually centered
  const tx = (500 - config.target.x) * (eased * (endZoom - 1) / endZoom);
  const ty = (250 - config.target.y) * (eased * (endZoom - 1) / endZoom);

  return (
    <div
      style={{
        position: "relative",
        width: 1100,
        height: 550,
        overflow: "hidden",
        border: `1px solid ${theme.accent}66`,
      }}
    >
      <div
        style={{
          width: 1100,
          height: 550,
          transform: `translate(${tx * 1.1}px, ${ty * 1.1}px) scale(${zoom})`,
          transformOrigin: "center",
          transition: "none",
        }}
      >
        <WorldMapBase
          theme={theme}
          highlightIndices={config.highlightContinents}
        />
      </div>
      {/* target reticle appears at full zoom */}
      {eased > 0.6 ? (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 80,
            height: 80,
            border: `2px solid ${theme.accent}`,
            borderRadius: "50%",
            opacity: (eased - 0.6) / 0.4,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: 6,
              height: 6,
              background: theme.accent,
              transform: "translate(-50%, -50%)",
              borderRadius: "50%",
            }}
          />
        </div>
      ) : null}
      {config.target.label ? (
        <div
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            color: theme.accent,
            fontFamily: theme.fontHeading,
            fontSize: 28,
            background: theme.bg,
            padding: "8px 16px",
            border: `1px solid ${theme.accent}`,
            opacity: Math.max(0, (eased - 0.7) / 0.3),
            letterSpacing: "0.06em",
            textTransform: "uppercase",
          }}
        >
          {config.target.label}
        </div>
      ) : null}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// pin_drop
// ─────────────────────────────────────────────────────────────────────────

const PinDrop: React.FC<{
  config: PinDropConfig;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ config, theme, frame, fps }) => {
  const stagger = config.staggerFrames ?? Math.round(fps * 1.2);

  return (
    <div style={{ position: "relative" }}>
      <WorldMapBase theme={theme} />
      <svg
        viewBox="0 0 1000 500"
        width={1100}
        height={550}
        style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
      >
        {config.pins.map((pin, i) => {
          const startFrame = 12 + i * stagger;
          const localFrame = frame - startFrame;
          if (localFrame < 0) return null;

          // Drop animation — y offset eases from -40 → 0 over 18 frames
          const drop = interpolate(localFrame, [0, 18], [-40, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const grow = interpolate(localFrame, [16, 30], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <g key={i} transform={`translate(0, ${drop})`}>
              <circle
                cx={pin.x}
                cy={pin.y}
                r={6}
                fill={theme.accent}
                opacity={Math.min(1, localFrame / 6)}
              />
              <circle
                cx={pin.x}
                cy={pin.y}
                r={12 + grow * 14}
                fill="none"
                stroke={theme.accent}
                strokeOpacity={Math.max(0, 1 - grow)}
                strokeWidth={1.5}
              />
              {pin.label && grow > 0.4 ? (
                <text
                  x={pin.x + 14}
                  y={pin.y + 4}
                  fontSize={13}
                  fontFamily={theme.fontBody}
                  fill={theme.text}
                  stroke={theme.bg}
                  strokeWidth={3}
                  paintOrder="stroke"
                  opacity={(grow - 0.4) / 0.6}
                >
                  {pin.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// empire_extent
// ─────────────────────────────────────────────────────────────────────────

const EmpireExtent: React.FC<{
  config: EmpireExtentConfig;
  theme: BrandTheme;
  frame: number;
  fps: number;
  total: number;
}> = ({ config, theme, frame, total }) => {
  const direction = config.direction ?? "rise";
  const t = interpolate(frame, [10, total - 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - t, 2.5);
  const scale = direction === "rise" ? eased : 1 - eased;
  const opacity = direction === "rise" ? eased : Math.max(0, 1 - eased * 0.85);

  return (
    <div style={{ position: "relative" }}>
      <WorldMapBase theme={theme} />
      <svg
        viewBox="0 0 1000 500"
        width={1100}
        height={550}
        style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
      >
        <g style={{ transformOrigin: "center", transform: `scale(${scale})` }}>
          <path
            d={config.territoryPath}
            fill={theme.accent}
            fillOpacity={opacity * 0.45}
            stroke={theme.accent}
            strokeOpacity={opacity}
            strokeWidth={2}
          />
        </g>
      </svg>
    </div>
  );
};
