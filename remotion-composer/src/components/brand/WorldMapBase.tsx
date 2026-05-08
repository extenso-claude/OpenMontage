/**
 * WorldMapBase — stylized continent silhouettes for the AnimatedMap variants.
 *
 * Hand-traced approximate continent shapes in a 1000×500 viewBox.
 * Coordinates throughout the map system are in this normalized space:
 * x ∈ [0, 1000], y ∈ [0, 500]. Lat/lng resolution is a TODO for future
 * variants — for the demo, the simplified system is intentional (sleep-doc
 * aesthetic favors stylized over photoreal).
 *
 * @internal — used only by AnimatedMap variants.
 */
import { BrandTheme } from "./theme";

interface WorldMapBaseProps {
  theme: BrandTheme;
  /** Highlight specific landmasses by index (subtle accent overlay). */
  highlightIndices?: number[];
  /** Width in pixels. Default 1100. */
  width?: number;
}

// Approximate continent silhouettes — intentionally stylized, not geographically precise.
// Path commands in viewBox coordinates (1000 wide × 500 tall).
const CONTINENTS: Array<{ name: string; d: string }> = [
  // North America
  {
    name: "north_america",
    d: "M 130,90 L 200,75 L 260,80 L 290,110 L 285,140 L 270,165 L 235,185 L 220,210 L 200,235 L 175,225 L 155,195 L 145,160 L 130,130 Z",
  },
  // South America
  {
    name: "south_america",
    d: "M 280,255 L 305,240 L 320,260 L 325,300 L 315,345 L 295,380 L 280,395 L 270,375 L 270,335 L 275,295 Z",
  },
  // Europe
  {
    name: "europe",
    d: "M 470,110 L 510,100 L 545,105 L 555,125 L 545,145 L 530,160 L 505,165 L 485,160 L 470,140 Z",
  },
  // Africa
  {
    name: "africa",
    d: "M 490,180 L 530,180 L 555,200 L 565,235 L 560,275 L 545,315 L 525,340 L 510,335 L 495,310 L 485,275 L 480,235 L 485,205 Z",
  },
  // Middle East / Western Asia
  {
    name: "middle_east",
    d: "M 560,150 L 605,150 L 615,175 L 605,195 L 580,200 L 565,180 Z",
  },
  // Asia (main mass)
  {
    name: "asia",
    d: "M 580,90 L 700,80 L 790,90 L 830,115 L 825,150 L 800,170 L 760,180 L 720,180 L 680,175 L 640,160 L 615,140 L 590,120 Z",
  },
  // Southeast Asia / Indonesia (cluster)
  {
    name: "se_asia",
    d: "M 770,210 L 800,205 L 815,225 L 800,240 L 775,235 Z",
  },
  // Australia
  {
    name: "australia",
    d: "M 800,300 L 855,295 L 880,310 L 875,340 L 845,355 L 815,350 L 798,330 Z",
  },
  // Greenland
  {
    name: "greenland",
    d: "M 380,55 L 420,50 L 430,75 L 415,90 L 390,85 Z",
  },
  // British Isles (suggestion)
  {
    name: "british_isles",
    d: "M 455,115 L 470,110 L 472,135 L 460,140 Z",
  },
];

export const WorldMapBase: React.FC<WorldMapBaseProps> = ({
  theme,
  highlightIndices = [],
  width = 1100,
}) => {
  const aspect = 500 / 1000;
  const height = width * aspect;
  const baseColor = theme.muted ?? "#3a3a4a";

  return (
    <svg
      viewBox="0 0 1000 500"
      width={width}
      height={height}
      style={{ display: "block" }}
    >
      {/* subtle grid for context */}
      <defs>
        <linearGradient id="map-bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={theme.bg} />
          <stop offset="100%" stopColor={baseColor} stopOpacity="0.15" />
        </linearGradient>
      </defs>
      <rect width="1000" height="500" fill="url(#map-bg-grad)" />
      {/* faint latitude/longitude lines */}
      {[125, 250, 375].map((y) => (
        <line
          key={`lat-${y}`}
          x1={0}
          x2={1000}
          y1={y}
          y2={y}
          stroke={baseColor}
          strokeOpacity={0.12}
          strokeDasharray="2 6"
        />
      ))}
      {[200, 400, 600, 800].map((x) => (
        <line
          key={`lon-${x}`}
          y1={0}
          y2={500}
          x1={x}
          x2={x}
          stroke={baseColor}
          strokeOpacity={0.12}
          strokeDasharray="2 6"
        />
      ))}

      {/* continents */}
      {CONTINENTS.map((c, i) => {
        const highlighted = highlightIndices.includes(i);
        return (
          <path
            key={c.name}
            d={c.d}
            fill={highlighted ? theme.accent : baseColor}
            fillOpacity={highlighted ? 0.55 : 0.4}
            stroke={highlighted ? theme.accent : baseColor}
            strokeWidth={highlighted ? 1.5 : 0.7}
            strokeOpacity={highlighted ? 0.9 : 0.6}
          />
        );
      })}
    </svg>
  );
};

export const CONTINENT_NAMES = CONTINENTS.map((c) => c.name);
