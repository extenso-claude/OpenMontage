import { Composition, CalculateMetadataFunction } from "remotion";
import { Explainer, ExplainerProps } from "./Explainer";
import {
  CinematicRenderer,
  calculateCinematicMetadata,
} from "./CinematicRenderer";
import { signalFromTomorrowWithMusicFixture } from "./cinematic/fixtures";
import { TalkingHead, TalkingHeadProps } from "./TalkingHead";
import {
  TitledVideo,
  calculateTitledVideoMetadata,
} from "./TitledVideo";
import { EndTag, EndTagProps } from "./components/EndTag";
import { HeroTitle } from "./components/HeroTitle";
import { ProductReveal, ProductRevealProps } from "./components/ProductReveal";
import { CaptionOverlay, WordCaption } from "./components/CaptionOverlay";
import { CollageBurst, CollageBurstProps } from "./CollageBurst";
import { LyricOverlay, LyricOverlayProps } from "./LyricOverlay";
import { BrandDemo, BRAND_DEMO_DURATION_FRAMES } from "./BrandDemo";
import { BrandDemo2, BRAND_DEMO_2_DURATION_FRAMES } from "./BrandDemo2";
import { BrandDemo3, BRAND_DEMO_3_DURATION_FRAMES } from "./BrandDemo3";
import {
  MidnightMagnatesStyleReel,
  MIDNIGHT_MAGNATES_REEL_DURATION_FRAMES,
} from "./MidnightMagnatesStyleReel";
import {
  FiveArrowsEpisode,
  FIVE_ARROWS_EPISODE_DURATION_FRAMES,
} from "./FiveArrowsEpisode";
import { LetterDynastyHook, LETTER_HOOK_DURATION_FRAMES } from "./LetterDynastyHook";
import { LetterDynastyColdOpen, LETTER_COLD_OPEN_DURATION_FRAMES } from "./LetterDynastyColdOpen";
import { LetterDynastyChapter1, LETTER_CHAPTER1_DURATION_FRAMES } from "./LetterDynastyChapter1";
import { LetterDynastyChapter2, LETTER_CHAPTER2_DURATION_FRAMES } from "./LetterDynastyChapter2";
import {
  LetterDynastyHookV2,
  LETTER_HOOK_V2_DURATION_FRAMES,
} from "./letter-dynasty/HookV2";
import {
  LetterDynastyColdOpenV2,
  LETTER_COLD_OPEN_V2_DURATION_FRAMES,
} from "./letter-dynasty/ColdOpenV2";
import {
  LetterDynastyChapter1V2,
  LETTER_CHAPTER1_V2_DURATION_FRAMES,
} from "./letter-dynasty/Chapter1V2";
import {
  LetterDynastyChapter2V2,
  LETTER_CHAPTER2_V2_DURATION_FRAMES,
} from "./letter-dynasty/Chapter2V2";
import {
  LetterDynastyFullV2,
  LETTER_DYNASTY_FULL_V2_DURATION_FRAMES,
} from "./letter-dynasty/FullEpisodeV2";
import {
  LetterDynastyHookV3,
  LETTER_HOOK_V3_DURATION_FRAMES,
} from "./letter-dynasty/v3/HookV3";
import {
  LetterDynastyColdOpenV3,
  LETTER_COLD_OPEN_V3_DURATION_FRAMES,
} from "./letter-dynasty/v3/ColdOpenV3";
import {
  LetterDynastyChapter1V3,
  LETTER_CHAPTER1_V3_DURATION_FRAMES,
} from "./letter-dynasty/v3/Chapter1V3";
import {
  LetterDynastyChapter2V3,
  LETTER_CHAPTER2_V3_DURATION_FRAMES,
} from "./letter-dynasty/v3/Chapter2V3";
import {
  LetterDynastyFullV3,
  LETTER_DYNASTY_FULL_V3_DURATION_FRAMES,
} from "./letter-dynasty/v3/FullEpisodeV3";
import {
  WildWestParallax,
  WILD_WEST_PARALLAX_DURATION_FRAMES,
} from "./WildWestParallax";
import {
  WildWestRidingTogether,
  WILD_WEST_RIDING_TOGETHER_DURATION_FRAMES,
} from "./WildWestRidingTogether";

// ---------------------------------------------------------------------------
// Theme System — prevents every video from looking like dark fintech
// ---------------------------------------------------------------------------

export interface ThemeConfig {
  primaryColor: string;
  accentColor: string;
  backgroundColor: string;
  surfaceColor: string;
  textColor: string;
  mutedTextColor: string;
  headingFont: string;
  bodyFont: string;
  monoFont: string;
  chartColors: string[];
  springConfig: { damping: number; stiffness: number; mass: number };
  transitionDuration: number;
  captionHighlightColor: string;
  captionBackgroundColor: string;
}

export const THEMES: Record<string, ThemeConfig> = {
  "clean-professional": {
    primaryColor: "#2563EB",
    accentColor: "#F59E0B",
    backgroundColor: "#FFFFFF",
    surfaceColor: "#F9FAFB",
    textColor: "#1F2937",
    mutedTextColor: "#6B7280",
    headingFont: "Inter",
    bodyFont: "Inter",
    monoFont: "JetBrains Mono",
    chartColors: ["#2563EB", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#06B6D4"],
    springConfig: { damping: 20, stiffness: 120, mass: 1 },
    transitionDuration: 0.4,
    captionHighlightColor: "#2563EB",
    captionBackgroundColor: "rgba(255, 255, 255, 0.85)",
  },
  "flat-motion-graphics": {
    primaryColor: "#7C3AED",
    accentColor: "#EC4899",
    backgroundColor: "#0F172A",
    surfaceColor: "#1E293B",
    textColor: "#F8FAFC",
    mutedTextColor: "#94A3B8",
    headingFont: "Space Grotesk",
    bodyFont: "Space Grotesk",
    monoFont: "Fira Code",
    chartColors: ["#7C3AED", "#EC4899", "#06B6D4", "#F59E0B", "#10B981", "#EF4444"],
    springConfig: { damping: 12, stiffness: 80, mass: 1 },
    transitionDuration: 0.3,
    captionHighlightColor: "#22D3EE",
    captionBackgroundColor: "rgba(15, 23, 42, 0.75)",
  },
  "minimalist-diagram": {
    primaryColor: "#1A1A2E",
    accentColor: "#E94560",
    backgroundColor: "#FAFAFA",
    surfaceColor: "#FFFFFF",
    textColor: "#1A1A2E",
    mutedTextColor: "#6B7280",
    headingFont: "IBM Plex Sans",
    bodyFont: "IBM Plex Sans",
    monoFont: "IBM Plex Mono",
    chartColors: ["#E94560", "#1A1A2E", "#0F3460", "#9CA3AF"],
    springConfig: { damping: 25, stiffness: 150, mass: 1 },
    transitionDuration: 0.5,
    captionHighlightColor: "#E94560",
    captionBackgroundColor: "rgba(250, 250, 250, 0.9)",
  },
  "anime-ghibli": {
    primaryColor: "#2D5016",
    accentColor: "#FFB347",
    backgroundColor: "#0A0A1A",
    surfaceColor: "#1A2332",
    textColor: "#F0E6D3",
    mutedTextColor: "#A8957E",
    headingFont: "Noto Serif JP",
    bodyFont: "Noto Sans",
    monoFont: "Fira Code",
    chartColors: ["#FFB347", "#2D5016", "#FF6B9D", "#A8E6CF", "#6B4C8A", "#E8927C"],
    springConfig: { damping: 18, stiffness: 60, mass: 1 },
    transitionDuration: 1.0,
    captionHighlightColor: "#FFB347",
    captionBackgroundColor: "rgba(10, 10, 26, 0.8)",
  },
};

// Default theme when none is specified — uses the existing dark style for backwards compatibility
export const DEFAULT_THEME = THEMES["flat-motion-graphics"];

export function resolveTheme(props: Record<string, unknown>): ThemeConfig {
  const themeName = (props.theme as string) || (props.playbook as string);
  if (themeName && THEMES[themeName]) {
    return THEMES[themeName];
  }
  // Allow custom theme passed as full object
  if (props.themeConfig && typeof props.themeConfig === "object") {
    return { ...DEFAULT_THEME, ...(props.themeConfig as Partial<ThemeConfig>) };
  }
  return DEFAULT_THEME;
}

const calculateMetadata: CalculateMetadataFunction<ExplainerProps> = async ({
  props,
}) => {
  const cuts = props.cuts || [];
  if (cuts.length === 0) {
    return { durationInFrames: 30 * 60 };
  }
  const lastEnd = Math.max(...cuts.map((c) => c.out_seconds || 0));
  // Add 1 second padding for final fade
  return { durationInFrames: Math.ceil((lastEnd + 1) * 30) };
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Explainer"
        component={Explainer}
        durationInFrames={30 * 60}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          cuts: [],
          overlays: [],
          captions: [],
          audio: {},
        }}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="CinematicRenderer"
        component={CinematicRenderer}
        durationInFrames={30 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          scenes: [],
          titleFontSize: 78,
          titleWidth: 1320,
          signalLineCount: 18,
        }}
        calculateMetadata={calculateCinematicMetadata}
      />
      <Composition
        id="SignalFromTomorrowWithMusic"
        component={CinematicRenderer}
        durationInFrames={30 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={signalFromTomorrowWithMusicFixture}
        calculateMetadata={calculateCinematicMetadata}
      />
      <Composition
        id="TalkingHead"
        component={TalkingHead}
        durationInFrames={30 * 300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoSrc: "",
          captions: [],
          overlays: [],
          wordsPerPage: 4,
          fontSize: 52,
          highlightColor: "#22D3EE",
        }}
      />
      <Composition
        id="TitledVideo"
        component={TitledVideo}
        durationInFrames={30 * 60}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          videoSrc: "",
          tagline: "home is a verb.",
          taglineInSeconds: 53.5,
          taglineOutSeconds: undefined,
          topPx: 150,
          fontSize: 148,
          accentColor: "#F5C470",
        }}
        calculateMetadata={calculateTitledVideoMetadata}
      />
      <Composition
        id="HeroTitle"
        component={HeroTitle}
        durationInFrames={30 * 17}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "THE CALIBRATORS",
          subtitle: "The People Who Define Reality",
        }}
      />
      <Composition
        id="ProductReveal"
        component={ProductReveal}
        durationInFrames={30 * 8}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          productImage: "airnothing/product.png",
          productName: "AirNothing Pro Max Ultra",
          price: "Starting at $999",
          tagline: "Nothing included.",
          closer: "Less is nothing.",
          accentColor: "#00D4FF",
        } as ProductRevealProps}
      />
      <Composition
        id="ProductRevealVertical"
        component={ProductReveal}
        durationInFrames={30 * 8}
        fps={30}
        width={720}
        height={1280}
        defaultProps={{
          productImage: "airnothing/product.png",
          productName: "AirNothing Pro Max Ultra",
          price: "Starting at $999",
          tagline: "Nothing included.",
          closer: "Less is nothing.",
          accentColor: "#00D4FF",
        } as ProductRevealProps}
      />
      <Composition
        id="CaptionOverlayOnly"
        component={CaptionOverlay}
        durationInFrames={30 * 300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          words: [] as WordCaption[],
          wordsPerPage: 3,
          fontSize: 58,
          highlightColor: "#FACC15",
          backgroundColor: "rgba(15, 23, 42, 0.75)",
        }}
      />
      <Composition
        id="CollageBurst"
        component={CollageBurst}
        durationInFrames={30 * 30}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          backgroundSrc: "",
          backgroundInSeconds: 0,
          curtainStartSeconds: 1.5,
          curtainEndSeconds: 3.0,
          clips: [],
        } as CollageBurstProps}
      />
      <Composition
        id="LyricOverlay"
        component={LyricOverlay}
        durationInFrames={30 * 28}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoSrc: "",
          lyrics: [],
          bottomY: 0.88,
        } as LyricOverlayProps}
      />
      <Composition
        id="EndTag"
        component={EndTag}
        // 5.5s at 30fps = 165 frames. Render CLI can override via --props.
        durationInFrames={165}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          text: "THE CITY KEEPS ITS OWN VIGIL.",
          palette: "cool_offwhite_on_black",
          fadeInSeconds: 0.6,
          holdSeconds: 4.3,
          fadeOutSeconds: 0.6,
        } as EndTagProps}
      />
      <Composition
        id="EndTagOverlay"
        component={EndTag}
        // 8.19s at 30fps = 246 frames. Render CLI can override via --props.
        // Intended to be composited on top of body footage, not concat'd.
        durationInFrames={246}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          text: "EARN THE LIGHT.",
          palette: "cool_offwhite_on_black",
          fadeInSeconds: 1.0,
          holdSeconds: 5.69,
          fadeOutSeconds: 1.5,
          overlay: true,
        } as EndTagProps}
      />
      <Composition
        id="BrandDemo"
        component={BrandDemo}
        durationInFrames={BRAND_DEMO_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
        defaultProps={{
          channel: "grandpa_huxley" as const,
        }}
      />
      <Composition
        id="BrandDemo2"
        component={BrandDemo2}
        durationInFrames={BRAND_DEMO_2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
        defaultProps={{
          channel: "grandpa_huxley" as const,
        }}
      />
      <Composition
        id="BrandDemo3"
        component={BrandDemo3}
        durationInFrames={BRAND_DEMO_3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
        defaultProps={{
          channel: "grandpa_huxley" as const,
        }}
      />
      <Composition
        id="MidnightMagnatesStyleReel"
        component={MidnightMagnatesStyleReel}
        durationInFrames={MIDNIGHT_MAGNATES_REEL_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="FiveArrowsEpisode"
        component={FiveArrowsEpisode}
        durationInFrames={FIVE_ARROWS_EPISODE_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyHook"
        component={LetterDynastyHook}
        durationInFrames={LETTER_HOOK_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyColdOpen"
        component={LetterDynastyColdOpen}
        durationInFrames={LETTER_COLD_OPEN_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter1"
        component={LetterDynastyChapter1}
        durationInFrames={LETTER_CHAPTER1_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter2"
        component={LetterDynastyChapter2}
        durationInFrames={LETTER_CHAPTER2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyHookV2"
        component={LetterDynastyHookV2}
        durationInFrames={LETTER_HOOK_V2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyColdOpenV2"
        component={LetterDynastyColdOpenV2}
        durationInFrames={LETTER_COLD_OPEN_V2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter1V2"
        component={LetterDynastyChapter1V2}
        durationInFrames={LETTER_CHAPTER1_V2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter2V2"
        component={LetterDynastyChapter2V2}
        durationInFrames={LETTER_CHAPTER2_V2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyFullV2"
        component={LetterDynastyFullV2}
        durationInFrames={LETTER_DYNASTY_FULL_V2_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyHookV3"
        component={LetterDynastyHookV3}
        durationInFrames={LETTER_HOOK_V3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyColdOpenV3"
        component={LetterDynastyColdOpenV3}
        durationInFrames={LETTER_COLD_OPEN_V3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter1V3"
        component={LetterDynastyChapter1V3}
        durationInFrames={LETTER_CHAPTER1_V3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyChapter2V3"
        component={LetterDynastyChapter2V3}
        durationInFrames={LETTER_CHAPTER2_V3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="LetterDynastyFullV3"
        component={LetterDynastyFullV3}
        durationInFrames={LETTER_DYNASTY_FULL_V3_DURATION_FRAMES}
        fps={24}
        width={1920}
        height={1080}
      />
      <Composition
        id="WildWestParallax"
        component={WildWestParallax}
        durationInFrames={WILD_WEST_PARALLAX_DURATION_FRAMES}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="WildWestRidingTogether"
        component={WildWestRidingTogether}
        durationInFrames={WILD_WEST_RIDING_TOGETHER_DURATION_FRAMES}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
