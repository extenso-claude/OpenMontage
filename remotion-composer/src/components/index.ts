export { TextCard } from "./TextCard";
export { StatCard } from "./StatCard";
export { ProgressBar } from "./ProgressBar";
export { CalloutBox } from "./CalloutBox";
export { ComparisonCard } from "./ComparisonCard";
export { BarChart, LineChart, PieChart, KPIGrid } from "./charts";
export { CaptionOverlay } from "./CaptionOverlay";
export { SectionTitle } from "./SectionTitle";
export { StatReveal } from "./StatReveal";
export { HeroTitle } from "./HeroTitle";
export { ParticleOverlay } from "./ParticleOverlay";
export { AnimeScene } from "./AnimeScene";
export { TerminalScene } from "./TerminalScene";
export { ScreenshotScene } from "./ScreenshotScene";
export { ProviderChip } from "./ProviderChip";
export type { ParticleType } from "./ParticleOverlay";
export type { CameraMotion, AnimeSceneProps } from "./AnimeScene";
export type { TerminalStep } from "./TerminalScene";
export type { ScreenshotStep, Region, Point } from "./ScreenshotScene";

// ─── Brand library (channel-themed reusables) ───
// See remotion-composer/src/components/brand/README.md
export { CharacterCard } from "./brand/CharacterCard";
export { TypewriterText } from "./brand/TypewriterText";
export { CTABanner } from "./brand/CTABanner";
export { AssetFrame } from "./brand/AssetFrame";
/** @deprecated Use MapAnnotation. AnimatedMap renders against synthetic geography only. */
export { AnimatedMap } from "./brand/AnimatedMap";
export { MapAnnotation, dedupePins } from "./brand/MapAnnotation";
export { Timeline } from "./brand/Timeline";
export { ChapterCard, ERA_PRESETS } from "./brand/ChapterCard";
export { LowerThird } from "./brand/LowerThird";
export { QuoteCard } from "./brand/QuoteCard";
export { ClockReveal } from "./brand/ClockReveal";
export { CalendarReveal } from "./brand/CalendarReveal";
export { ParallaxStill } from "./brand/ParallaxStill";
export { DocumentReveal } from "./brand/DocumentReveal";
export { Stamp } from "./brand/Stamp";
export { SocialMediaPopup } from "./brand/SocialMediaPopup";
export { CalloutArrow } from "./brand/CalloutArrow";
export { NetworkMap } from "./brand/NetworkMap";
export { BrandedChart } from "./brand/BrandedChart";
export { FiveArrowsReveal } from "./brand/FiveArrowsReveal";
export { resolveTheme, NETWORK_BASE_THEME } from "./brand/theme";
export type { BrandTheme } from "./brand/theme";
export type { CharacterCardProps, CharacterCardPosition } from "./brand/CharacterCard";
export type { TypewriterTextProps } from "./brand/TypewriterText";
export type { CTABannerProps, CTAPreset } from "./brand/CTABanner";
export type { AssetFrameProps, AssetFrameVariant } from "./brand/AssetFrame";
export type { ChapterCardProps, ChapterOverrides } from "./brand/ChapterCard";
export type { LowerThirdProps, LowerThirdVariant } from "./brand/LowerThird";
export type { QuoteCardProps, QuoteCardVariant } from "./brand/QuoteCard";
export type { ClockRevealProps } from "./brand/ClockReveal";
export type { CalendarRevealProps } from "./brand/CalendarReveal";
export type { ParallaxStillProps } from "./brand/ParallaxStill";
export type { DocumentRevealProps, DocumentRevealVariant, DocRegion } from "./brand/DocumentReveal";
export type { StampProps, StampPreset } from "./brand/Stamp";
export type { SocialMediaPopupProps, SocialMediaVariant, MessageBubble } from "./brand/SocialMediaPopup";
export type { CalloutArrowProps } from "./brand/CalloutArrow";
export type { NetworkMapProps, NetworkNode, NetworkEdge } from "./brand/NetworkMap";
export type { BrandedChartProps } from "./brand/BrandedChart";
export type { FiveArrowsRevealProps } from "./brand/FiveArrowsReveal";
export type {
  AnimatedMapProps,
  AnimatedMapVariant,
  AnimatedMapConfig,
  WorldRouteConfig,
  RegionZoomConfig,
  PinDropConfig,
  EmpireExtentConfig,
  MapPoint as DeprecatedMapPoint,
} from "./brand/AnimatedMap";
export type {
  MapAnnotationProps,
  Annotation as MapAnnotation_Annotation,
  PinAnnotation,
  CircleAnnotation,
  RouteArcAnnotation,
  RegionLabelAnnotation,
  ColorOverlayAnnotation,
  PulseAnnotation,
  CameraState,
  MapPoint,
} from "./brand/MapAnnotation";
export type {
  TimelineProps,
  TimelineEvent,
  TimelineVariant,
  TimelineLifeline,
  BranchOption,
} from "./brand/Timeline";
