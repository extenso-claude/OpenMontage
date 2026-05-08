/**
 * BrandDemo3 — map animation showcase using real channel-styled map images.
 *
 * Uses Imagen-Ultra-generated maps (vintage parchment for Huxley, noir navy for MM)
 * and demonstrates 7 animation patterns over each: static reveal, route_arc journey
 * with sprite, zoom-in to a city with scribble circle, zoom-out, pin drops, color
 * overlay (cultural/economic reach), and region labels.
 *
 * Coordinates over the maps are eyeballed from the generated images and may need
 * fine-tuning per channel — the asset director should treat these positions as
 * a starting point and adjust per scene.
 */
import { AbsoluteFill, Series, staticFile } from "remotion";
import {
  TypewriterText,
  MapAnnotation,
  MapAnnotation_Annotation,
  CameraState,
  MapPoint,
  resolveTheme,
  BrandTheme,
} from "./components";
import huxleyTheme from "./components/brand/themes/grandpa_huxley.json";
import mmTheme from "./components/brand/themes/midnight_magnates.json";

export interface BrandDemo3Props {
  channel: "grandpa_huxley" | "midnight_magnates";
}

const THEMES: Record<BrandDemo3Props["channel"], Partial<BrandTheme>> = {
  grandpa_huxley: huxleyTheme as Partial<BrandTheme>,
  midnight_magnates: mmTheme as Partial<BrandTheme>,
};

const FPS = 24;
const sec = (s: number) => Math.round(s * FPS);

const SCENE_DURATIONS_S = [
  4,  // 1. Title
  5,  // 2. Map static reveal
  8,  // 3. route_arc
  7,  // 4. zoom in + scribble circle
  6,  // 5. zoom out (back to full)
  7,  // 6. pin drops
  7,  // 7. color overlay
  6,  // 8. region labels
  4,  // 9. End
];

const TOTAL_S = SCENE_DURATIONS_S.reduce((a, b) => a + b, 0);
export const BRAND_DEMO_3_DURATION_FRAMES = sec(TOTAL_S);

export const BrandDemo3: React.FC<BrandDemo3Props> = ({ channel }) => {
  const theme = resolveTheme(THEMES[channel]);
  const isMM = channel === "midnight_magnates";

  const mapSrc = isMM
    ? staticFile("brand_demo/maps/mm_europe.png")
    : staticFile("brand_demo/maps/huxley_mediterranean.png");

  const channelTitle = isMM ? "MIDNIGHT MAGNATES" : "GRANDPA HUXLEY";

  // City coordinates (re-eyeballed after QA frame review against regenerated maps)
  const cities: Record<string, MapPoint> = isMM
    ? {
        // Europe map — corrected against regenerated mm_europe.png
        london: { x: 0.15, y: 0.42, label: "London" },
        paris: { x: 0.30, y: 0.58, label: "Paris" },
        frankfurt: { x: 0.45, y: 0.52, label: "Frankfurt" },
        vienna: { x: 0.55, y: 0.62, label: "Vienna" },
        naples: { x: 0.46, y: 0.82, label: "Naples" },
        madrid: { x: 0.22, y: 0.85, label: "Madrid" },
        berlin: { x: 0.50, y: 0.46, label: "Berlin" },
      }
    : {
        // Mediterranean map — corrected against huxley_mediterranean.png
        rome: { x: 0.45, y: 0.40, label: "Rome" },
        athens: { x: 0.62, y: 0.51, label: "Athens" },
        alexandria: { x: 0.79, y: 0.65, label: "Alexandria" },
        antioch: { x: 0.84, y: 0.42, label: "Antioch" },
        carthage: { x: 0.42, y: 0.55, label: "Carthage" },
        constantinople: { x: 0.66, y: 0.32, label: "Constantinople" },
      };

  // ── Scene 3: route_arc ──
  const routeAnnotations: MapAnnotation_Annotation[] = isMM
    ? [
        {
          type: "route_arc",
          waypoints: [
            cities.frankfurt!,
            cities.london!,
            cities.paris!,
            cities.vienna!,
            cities.naples!,
          ],
          sprite: "✈",
          curvature: 0.10,
          revealAtSeconds: 0.4,
        },
      ]
    : [
        {
          type: "route_arc",
          waypoints: [
            cities.athens!,
            cities.alexandria!,
            cities.antioch!,
            cities.constantinople!,
            cities.rome!,
          ],
          sprite: "⚓",
          curvature: 0.12,
          revealAtSeconds: 0.4,
        },
      ];

  // ── Scene 4: zoom in to a target city, with scribble circle ──
  const zoomTarget: MapPoint = isMM ? cities.london! : cities.athens!;
  const zoomInStart: CameraState = { focalX: 0.5, focalY: 0.5, zoom: 1 };
  const zoomInEnd: CameraState = { focalX: zoomTarget.x, focalY: zoomTarget.y, zoom: 2.6 };
  const zoomInAnnotations: MapAnnotation_Annotation[] = [
    {
      type: "circle",
      center: zoomTarget,
      radius: 0.04,
      scribble: true,
      label: zoomTarget.label,
      revealAtSeconds: 3.2,
    },
    {
      type: "pulse",
      position: zoomTarget,
      revealAtSeconds: 5.0,
    },
  ];

  // ── Scene 5: zoom out (reverse) ──
  const zoomOutStart: CameraState = { focalX: zoomTarget.x, focalY: zoomTarget.y, zoom: 2.6 };
  const zoomOutEnd: CameraState = { focalX: 0.5, focalY: 0.5, zoom: 1 };

  // ── Scene 6: pin drops ──
  const pinAnnotations: MapAnnotation_Annotation[] = isMM
    ? [
        { type: "pin", position: cities.frankfurt!, revealAtSeconds: 0.4 },
        { type: "pin", position: cities.london!, revealAtSeconds: 1.4 },
        { type: "pin", position: cities.paris!, revealAtSeconds: 2.4 },
        { type: "pin", position: cities.vienna!, revealAtSeconds: 3.4 },
        { type: "pin", position: cities.naples!, revealAtSeconds: 4.4 },
      ]
    : [
        { type: "pin", position: cities.athens!, revealAtSeconds: 0.4 },
        { type: "pin", position: cities.rome!, revealAtSeconds: 1.4 },
        { type: "pin", position: cities.alexandria!, revealAtSeconds: 2.4 },
        { type: "pin", position: cities.antioch!, revealAtSeconds: 3.4 },
        { type: "pin", position: cities.carthage!, revealAtSeconds: 4.4 },
      ];

  // ── Scene 7: color overlay (territory / cultural reach) ──
  const colorOverlayAnnotations: MapAnnotation_Annotation[] = isMM
    ? [
        // British sphere — Britain + Ireland + edges. Drawn around the actual British Isles.
        {
          type: "color_overlay",
          polygonPath:
            "M 0.05,0.20 L 0.22,0.18 L 0.23,0.40 L 0.20,0.55 L 0.10,0.55 L 0.04,0.40 Z",
          direction: "rise",
          revealAtSeconds: 0.5,
        },
        {
          type: "region_label",
          position: { x: 0.13, y: 0.34 },
          text: "British Sphere",
          fontSize: 32,
          revealAtSeconds: 2.2,
        },
      ]
    : [
        // Hellenistic cultural sphere — Greek peninsula + Anatolia + Levant + Egypt
        {
          type: "color_overlay",
          polygonPath:
            "M 0.55,0.30 L 0.92,0.20 L 0.94,0.45 L 0.90,0.65 L 0.78,0.78 L 0.62,0.68 L 0.55,0.55 Z",
          direction: "rise",
          revealAtSeconds: 0.5,
        },
        {
          type: "region_label",
          position: { x: 0.78, y: 0.50 },
          text: "Hellenistic Sphere",
          fontSize: 32,
          revealAtSeconds: 2.2,
        },
      ];

  // ── Scene 8: region labels (multiple) ──
  const regionLabelAnnotations: MapAnnotation_Annotation[] = isMM
    ? [
        { type: "region_label", position: { x: 0.14, y: 0.42 }, text: "BRITISH ISLES", fontSize: 34, revealAtSeconds: 0.4 },
        { type: "region_label", position: { x: 0.30, y: 0.72 }, text: "FRANCE", fontSize: 40, revealAtSeconds: 1.4 },
        { type: "region_label", position: { x: 0.46, y: 0.55 }, text: "GERMAN STATES", fontSize: 34, revealAtSeconds: 2.4 },
        { type: "region_label", position: { x: 0.46, y: 0.78 }, text: "ITALY", fontSize: 40, revealAtSeconds: 3.4 },
        { type: "region_label", position: { x: 0.22, y: 0.88 }, text: "IBERIA", fontSize: 38, revealAtSeconds: 4.4 },
      ]
    : [
        { type: "region_label", position: { x: 0.45, y: 0.45 }, text: "ITALIA", fontSize: 40, revealAtSeconds: 0.4 },
        { type: "region_label", position: { x: 0.62, y: 0.45 }, text: "GRAECIA", fontSize: 38, revealAtSeconds: 1.4 },
        { type: "region_label", position: { x: 0.82, y: 0.30 }, text: "ANATOLIA", fontSize: 38, revealAtSeconds: 2.4 },
        { type: "region_label", position: { x: 0.79, y: 0.74 }, text: "AEGYPTUS", fontSize: 38, revealAtSeconds: 3.4 },
        { type: "region_label", position: { x: 0.10, y: 0.42 }, text: "HISPANIA", fontSize: 38, revealAtSeconds: 4.4 },
      ];

  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <Series>
        {/* 1. Title */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[0])}>
          <TypewriterText
            text={`${channelTitle}\nmap animations`}
            charsPerSecond={14}
            fontSize={64}
            theme={theme}
            durationFrames={sec(SCENE_DURATIONS_S[0])}
          />
        </Series.Sequence>

        {/* 2. Map static reveal */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[1])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "Europe · Mid-19th Century" : "The Mediterranean World"}
            durationFrames={sec(SCENE_DURATIONS_S[1])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 3. route_arc journey */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[2])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "The Network · Five Capitals" : "The Spread of Stoicism"}
            annotations={routeAnnotations}
            durationFrames={sec(SCENE_DURATIONS_S[2])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 4. zoom in to a city + scribble circle */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[3])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "Zoom · London" : "Zoom · Athens"}
            cameraStart={zoomInStart}
            cameraEnd={zoomInEnd}
            annotations={zoomInAnnotations}
            durationFrames={sec(SCENE_DURATIONS_S[3])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 5. zoom out */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[4])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={"…and back to the wider view"}
            cameraStart={zoomOutStart}
            cameraEnd={zoomOutEnd}
            durationFrames={sec(SCENE_DURATIONS_S[4])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 6. pin drops */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[5])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "Five Capitals · Pin Drops" : "Centers of Learning"}
            annotations={pinAnnotations}
            durationFrames={sec(SCENE_DURATIONS_S[5])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 7. color overlay (cultural/political reach) */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[6])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "Sphere of Influence" : "Hellenistic Reach"}
            annotations={colorOverlayAnnotations}
            durationFrames={sec(SCENE_DURATIONS_S[6])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 8. region labels */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[7])}>
          <MapAnnotation
            mapSrc={mapSrc}
            title={isMM ? "Region Labels" : "Provinces of the Old World"}
            annotations={regionLabelAnnotations}
            durationFrames={sec(SCENE_DURATIONS_S[7])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 9. End */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS_S[8])}>
          <TypewriterText
            text={`MapAnnotation · v0.1`}
            charsPerSecond={12}
            fontSize={48}
            theme={theme}
            durationFrames={sec(SCENE_DURATIONS_S[8])}
          />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
