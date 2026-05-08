/**
 * FiveArrowsEpisode — Midnight Magnates Five Arrows test composition.
 *
 * Full episode mapped to 6 voice-over tracks (concatenated as master.wav)
 * with 49 scenes + 10 overlays driven by the scene_plan.json artifact at
 * projects/midnight-magnates-five-arrows-test/artifacts/scene_plan.json.
 *
 * Render config: 1920x1080 @ 24fps, total ~486s (11,663 frames + 1s fade).
 *
 * Components exercised (one or more times each):
 *   - HeroTitle (inline, channel-styled), ChapterCard, CharacterCard
 *   - Stamp, DocumentReveal, AssetFrame, TypewriterText
 *   - QuoteCard, ClockReveal, CalendarReveal, NetworkMap, MapAnnotation
 *   - StatCard (built-in), ComparisonCard, BarChart, LineChart
 *   - LowerThird, SectionTitle (overlay), ProviderChip (overlay)
 *   - CTABanner
 *   - **FiveArrowsReveal** — NEW component for this episode
 *
 * Channel-locked tokens come from themes/midnight_magnates.json.
 */
import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  Series,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";
import {
  ChapterCard,
  CharacterCard,
  Stamp,
  DocumentReveal,
  AssetFrame,
  TypewriterText,
  QuoteCard,
  ClockReveal,
  CalendarReveal,
  NetworkMap,
  MapAnnotation,
  ComparisonCard,
  BarChart,
  LineChart,
  LowerThird,
  CTABanner,
  FiveArrowsReveal,
  StatCard,
  SectionTitle,
  ProviderChip,
  resolveTheme,
} from "./components";
import mmTheme from "./components/brand/themes/midnight_magnates.json";

const FPS = 24;
const W = 1920;
const H = 1080;
const TOTAL_DURATION_S = 485.96;
export const FIVE_ARROWS_EPISODE_DURATION_FRAMES = Math.ceil(TOTAL_DURATION_S * FPS) + 24; // +1s pad

const sec = (s: number) => Math.round(s * FPS);

// 8-offset stroke + soft shadow for any inline cream text
const TEXT_STROKE =
  "2px 0 0 #000, -2px 0 0 #000, 0 2px 0 #000, 0 -2px 0 #000, " +
  "1.4px 1.4px 0 #000, -1.4px 1.4px 0 #000, 1.4px -1.4px 0 #000, -1.4px -1.4px 0 #000, " +
  "0 4px 14px rgba(0,0,0,0.55)";

// ---------------------------------------------------------------------------
// EpisodeHeroTitle — inline title card matching the MidnightMagnatesStyleReel
// pattern (the existing global HeroTitle is hardcoded for a different
// channel's typography). Reusable for hook open + closing card.
// ---------------------------------------------------------------------------
const EpisodeHeroTitle: React.FC<{ title: string; subtitle?: string }> = ({
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const theme = resolveTheme(mmTheme as any);
  const fadeIn = 36;
  const fadeOut = 36;
  const titleSpread = 30;

  const fade = interpolate(
    frame,
    [0, fadeIn, durationInFrames - fadeOut, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const scale = interpolate(frame, [0, fadeIn], [0.97, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const ruleStart = fadeIn + titleSpread + 12;
  const ruleEnd = ruleStart + 30;
  const ruleProgress = interpolate(frame, [ruleStart, ruleEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const subStart = ruleEnd + 8;
  const subOpacity = interpolate(frame, [subStart, subStart + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        opacity: fade,
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontFamily: theme.fontHeading,
          fontWeight: 700,
          fontSize: 96,
          color: theme.text,
          letterSpacing: "0.10em",
          textShadow: TEXT_STROKE,
          display: "flex",
        }}
      >
        {title.split("").map((char, i) => {
          const charStart = fadeIn + (i / Math.max(1, title.length)) * titleSpread;
          const o = interpolate(frame, [charStart, charStart + 8], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          return (
            <span key={i} style={{ opacity: o, whiteSpace: "pre" }}>
              {char}
            </span>
          );
        })}
      </div>
      <div
        style={{
          width: 720,
          height: 2,
          background: theme.accent,
          marginTop: 36,
          transform: `scaleX(${ruleProgress})`,
          transformOrigin: "center",
          boxShadow: `0 0 18px ${theme.accent}66`,
        }}
      />
      {subtitle ? (
        <div
          style={{
            fontFamily: theme.fontBody,
            fontStyle: "italic",
            fontSize: 36,
            color: theme.text,
            marginTop: 36,
            opacity: subOpacity,
            letterSpacing: "0.04em",
            textShadow: TEXT_STROKE,
            maxWidth: 1100,
            textAlign: "center",
            lineHeight: 1.4,
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Helper — wrap a child scene in a thin fade so consecutive cuts don't snap.
// ---------------------------------------------------------------------------
const SceneFade: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const fade = 18;
  const o = interpolate(
    frame,
    [0, fade, durationInFrames - fade, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

// ---------------------------------------------------------------------------
// Image scene with subtle Ken-Burns motion + brand background plate.
// ---------------------------------------------------------------------------
const ImageScene: React.FC<{
  src: string;
  kenBurns?: "zoom_in_slow" | "pan_left" | "pan_right" | "zoom_in" | "parallax_drift" | "parallax" | "slow_zoom" | "slow_zoom_in" | "hold_then_drift" | "pan_forward" | "zoom_in_slow_2";
}> = ({ src, kenBurns = "zoom_in_slow" }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  let scale = 1.05 + t * 0.05;
  let tx = 0;
  let ty = 0;

  switch (kenBurns) {
    case "pan_left":
      tx = interpolate(t, [0, 1], [40, -40]);
      break;
    case "pan_right":
      tx = interpolate(t, [0, 1], [-40, 40]);
      break;
    case "zoom_in":
      scale = 1.02 + t * 0.10;
      break;
    case "zoom_in_slow":
      scale = 1.04 + t * 0.06;
      break;
    case "slow_zoom":
    case "slow_zoom_in":
      scale = 1.04 + t * 0.05;
      break;
    case "parallax":
    case "parallax_drift":
      scale = 1.06 + t * 0.04;
      tx = interpolate(t, [0, 1], [-20, 20]);
      ty = interpolate(t, [0, 1], [10, -10]);
      break;
    case "hold_then_drift":
      tx = interpolate(t, [0, 0.5, 1], [0, 0, 30]);
      break;
    case "pan_forward":
      scale = 1.05 + t * 0.08;
      ty = interpolate(t, [0, 1], [10, -10]);
      break;
  }

  const theme = resolveTheme(mmTheme as any);
  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
          transformOrigin: "center",
        }}
      >
        <Img
          src={src}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
      {/* Subtle vignette to integrate with brand bg */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.45) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// AI clip scene — wraps OffthreadVideo with brand background fallback.
// ---------------------------------------------------------------------------
const AIClipScene: React.FC<{ src: string }> = ({ src }) => {
  const theme = resolveTheme(mmTheme as any);
  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <OffthreadVideo
        src={src}
        muted
        playbackRate={1}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.35) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// CenterTextCard — channel-styled large text moment (replaces upstream TextCard
// which uses Inter and is non-channel).
// ---------------------------------------------------------------------------
const CenterTextCard: React.FC<{ text: string; attribution?: string; size?: number }> = ({
  text,
  attribution,
  size = 56,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const theme = resolveTheme(mmTheme as any);
  const fadeIn = 36;
  const fadeOut = 36;
  const fade = interpolate(
    frame,
    [0, fadeIn, durationInFrames - fadeOut, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return (
    <AbsoluteFill
      style={{
        background: theme.bg,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        opacity: fade,
      }}
    >
      <div
        style={{
          fontFamily: theme.fontHeading,
          fontStyle: "italic",
          fontSize: size,
          color: theme.text,
          textAlign: "center",
          maxWidth: 1300,
          lineHeight: 1.4,
          letterSpacing: "0.01em",
          textShadow: TEXT_STROKE,
        }}
      >
        {text}
      </div>
      {attribution ? (
        <div
          style={{
            fontFamily: theme.fontHeading,
            fontWeight: 700,
            fontSize: 22,
            color: theme.muted ?? "#6a6a7a",
            marginTop: 32,
            letterSpacing: "0.18em",
          }}
        >
          {attribution}
        </div>
      ) : null}
      <div
        style={{
          width: 240,
          height: 1.5,
          background: theme.accent,
          marginTop: 24,
          opacity: 0.7,
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// SCENE TABLE — declarative description of 49 scenes with frame durations.
// Order matters: scenes render via <Series> in this order.
// ---------------------------------------------------------------------------
type SceneSpec = {
  id: string;
  durationFrames: number;
  render: () => React.ReactElement;
};

const themeForBrand = (props: any = {}) => mmTheme as any;

const sceneList: SceneSpec[] = [
  // HOOK ──────────────────────────────────────────────────────────────────
  {
    id: "h01_title",
    durationFrames: sec(6.5),
    render: () => (
      <EpisodeHeroTitle
        title="THE FIVE ARROWS"
        subtitle="How a single sealed letter built a dynasty"
      />
    ),
  },
  {
    id: "h02_letter_clip",
    durationFrames: sec(7.5),
    render: () => <AIClipScene src={staticFile("five-arrows/ai_v_letter_kling.mp4")} />,
  },
  {
    id: "h03_frankfurt",
    durationFrames: sec(8.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_frankfurt_alley.png")}
        kenBurns="zoom_in_slow"
      />
    ),
  },
  {
    id: "h04_london_xchg",
    durationFrames: sec(8.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_london_xchg_dawn.png")}
        kenBurns="pan_left"
      />
    ),
  },
  {
    id: "h05_trading_pillar",
    durationFrames: sec(9.5),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_trading_floor_wide.png")}
        kenBurns="zoom_in"
      />
    ),
  },
  {
    id: "h06_nathan_card",
    durationFrames: sec(7.5),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <ImageScene
          src={staticFile("five-arrows/img_trading_floor_wide.png")}
          kenBurns="hold_then_drift"
        />
        <CharacterCard
          name="Nathan Mayer Rothschild"
          role="London Banker"
          dates="1777 – 1836"
          position="top-right"
          portraitSrc={staticFile("five-arrows/img_nathan_portrait.png")}
          theme={mmTheme as any}
          durationFrames={sec(7.5)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "h07_fortune_clip",
    durationFrames: sec(9.0),
    render: () => <AIClipScene src={staticFile("five-arrows/ai_v_fortune_veo.mp4")} />,
  },
  {
    id: "h08_five_arrows_hero",
    durationFrames: sec(9.5),
    render: () => (
      <FiveArrowsReveal
        cities={["Frankfurt", "London", "Paris", "Vienna", "Naples"]}
        originLabel="Frankfurt"
        highlightOrigin
        durationFrames={sec(9.5)}
        theme={mmTheme as any}
      />
    ),
  },
  {
    id: "h09_information",
    durationFrames: sec(5.58),
    render: () => (
      <CenterTextCard
        text="Information is the only currency that does not lose its value."
        attribution="MAYER AMSCHEL ROTHSCHILD, ATTRIBUTED"
      />
    ),
  },

  // COLD OPEN ─────────────────────────────────────────────────────────────
  {
    id: "c01_floor_re",
    durationFrames: sec(7.92),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_trading_floor_wide.png")}
        kenBurns="hold_then_drift"
      />
    ),
  },
  {
    id: "c02_nathan_pillar",
    durationFrames: sec(10.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_nathan_at_pillar.png")}
        kenBurns="slow_zoom"
      />
    ),
  },
  {
    id: "c03_sell_doc",
    durationFrames: sec(9.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <DocumentReveal
          variant="signature"
          documentTitle="SELL · CONSOLS"
          metadata="Trading floor · 19 June 1815"
          bodyText={"By order of N. Rothschild\nSt Swithin's Lane · London"}
          signatureText="N. Rothschild"
          theme={mmTheme as any}
          durationFrames={sec(9.0)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "c04_bond_chart",
    durationFrames: sec(10.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <div
          style={{
            position: "absolute",
            top: 60,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: (mmTheme as any).fontHeading,
            fontWeight: 700,
            fontSize: 36,
            color: (mmTheme as any).text,
            letterSpacing: "0.05em",
            textShadow: TEXT_STROKE,
            zIndex: 2,
          }}
        >
          LONDON BOND MARKET · 19 JUNE 1815
        </div>
        <AbsoluteFill style={{ paddingTop: 150, paddingLeft: 80, paddingRight: 80, paddingBottom: 60 }}>
          <BarChart
            data={[
              { label: "08:00", value: 100 },
              { label: "10:00", value: 92 },
              { label: "12:00", value: 71 },
              { label: "14:00", value: 48 },
              { label: "16:00", value: 38 },
            ]}
            showValues
            showGrid
            animationStyle="grow-up"
            colors={["#c9a84c", "#8c6e23", "#4a6fa5", "#b41e1e", "#3a3a4a"]}
            backgroundColor={(mmTheme as any).bg}
            textColor={(mmTheme as any).text}
            gridColor="#3a3a4a"
            fontFamily="Georgia"
          />
        </AbsoluteFill>
      </AbsoluteFill>
    ),
  },
  {
    id: "c05_brokers_panic",
    durationFrames: sec(9.0),
    render: () => <AIClipScene src={staticFile("five-arrows/ai_v_brokers_seedance.mp4")} />,
  },
  {
    id: "c06_quiet_buy",
    durationFrames: sec(9.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_quiet_buyers.png")}
        kenBurns="parallax_drift"
      />
    ),
  },
  {
    id: "c07_dawn_close",
    durationFrames: sec(10.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <StatCard
          stat="ALL POSITIONS · CLOSED"
          subtitle="By dawn, 20 June 1815"
          accentColor={(mmTheme as any).accent}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "c08_messenger",
    durationFrames: sec(10.0),
    render: () => <AIClipScene src={staticFile("five-arrows/ai_v_messenger_minimax.mp4")} />,
  },
  {
    id: "c09_finance_born",
    durationFrames: sec(10.0),
    render: () => (
      <CenterTextCard
        text="The modern financial world has just been born — in the silence between two pieces of information."
        size={48}
      />
    ),
  },
  {
    id: "c10_classified_stamp",
    durationFrames: sec(12.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <ImageScene
          src={staticFile("five-arrows/img_paper_letter.png")}
          kenBurns="zoom_in_slow"
        />
        <Stamp
          text="SEALED"
          rotationDeg={-7}
          impactAtSeconds={4.0}
          theme={mmTheme as any}
          durationFrames={sec(12.0)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "c11_cta_follow",
    durationFrames: sec(6.55),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <ImageScene
          src={staticFile("five-arrows/img_paper_letter.png")}
          kenBurns="hold_then_drift"
        />
        <CTABanner
          preset="spotify_follow"
          customText="If these stories speak to you, tap follow to join our circle of dreamers."
          holdSeconds={4.5}
          theme={mmTheme as any}
          durationFrames={sec(6.55)}
        />
      </AbsoluteFill>
    ),
  },

  // CHAPTER 1 ─────────────────────────────────────────────────────────────
  {
    id: "ch1_card",
    durationFrames: sec(5.95),
    render: () => (
      <ChapterCard
        chapterNumber={1}
        title="The Five Arrows"
        subtitle="Frankfurt · 1764 – 1812"
        overrides={{
          backgroundImageSrc: staticFile("five-arrows/img_frankfurt_alley_blur.png"),
          backgroundOverlayOpacity: 0.7,
        }}
        theme={mmTheme as any}
        durationFrames={sec(5.95)}
      />
    ),
  },
  {
    id: "ch1_alley",
    durationFrames: sec(12.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_judengasse.png")}
        kenBurns="zoom_in_slow"
      />
    ),
  },
  {
    id: "ch1_mayer_card",
    durationFrames: sec(6.5),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <ImageScene
          src={staticFile("five-arrows/img_judengasse.png")}
          kenBurns="hold_then_drift"
        />
        <CharacterCard
          name="Mayer Amschel Rothschild"
          role="Coin Dealer · Patriarch"
          dates="1744 – 1812"
          position="top-left"
          portraitSrc={staticFile("five-arrows/img_mayer_portrait.png")}
          theme={mmTheme as any}
          durationFrames={sec(6.5)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "ch1_general_map",
    durationFrames: sec(14.5),
    render: () => (
      <FiveArrowsReveal
        cities={["Frankfurt", "London", "Paris", "Vienna", "Naples"]}
        originLabel="Frankfurt"
        highlightOrigin
        durationFrames={sec(14.5)}
        theme={mmTheme as any}
      />
    ),
  },
  {
    id: "ch1_listen",
    durationFrames: sec(12.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_letters_crossing.png")}
        kenBurns="parallax"
      />
    ),
  },
  {
    id: "ch1_network",
    durationFrames: sec(14.5),
    render: () => (
      <NetworkMap
        title="THE FIVE-ROTHSCHILD NETWORK"
        nodes={[
          { id: "frankfurt", label: "Frankfurt", x: 500, y: 300, isCenter: true, role: "Origin" },
          { id: "london", label: "London", x: 200, y: 200, role: "Nathan" },
          { id: "paris", label: "Paris", x: 250, y: 380, role: "James" },
          { id: "vienna", label: "Vienna", x: 800, y: 280, role: "Salomon" },
          { id: "naples", label: "Naples", x: 720, y: 480, role: "Carl" },
        ]}
        edges={[
          { fromId: "frankfurt", toId: "london", type: "ally" },
          { fromId: "frankfurt", toId: "paris", type: "ally" },
          { fromId: "frankfurt", toId: "vienna", type: "ally" },
          { fromId: "frankfurt", toId: "naples", type: "ally" },
          { fromId: "london", toId: "paris", type: "transaction" },
          { fromId: "vienna", toId: "naples", type: "transaction" },
        ]}
        durationFrames={sec(14.5)}
        theme={mmTheme as any}
      />
    ),
  },
  {
    id: "ch1_1812",
    durationFrames: sec(7.0),
    render: () => (
      <CalendarReveal
        month="September"
        year={1812}
        targetDay={19}
        firstDayOfWeek={2}
        daysInMonth={30}
        caption="Mayer Amschel dies"
        theme={mmTheme as any}
        durationFrames={sec(7.0)}
      />
    ),
  },
  {
    id: "ch1_one_mind",
    durationFrames: sec(8.4),
    render: () => (
      <CenterTextCard
        text="Five capitals. One mind. One family ledger no government on the continent could read."
        size={50}
      />
    ),
  },

  // CHAPTER 2 ─────────────────────────────────────────────────────────────
  {
    id: "ch2_card",
    durationFrames: sec(5.6),
    render: () => (
      <ChapterCard
        chapterNumber={2}
        title="The Couriers"
        subtitle="Brussels → London"
        overrides={{
          backgroundImageSrc: staticFile("five-arrows/img_riders_relay.png"),
          backgroundOverlayOpacity: 0.7,
        }}
        theme={mmTheme as any}
        durationFrames={sec(5.6)}
      />
    ),
  },
  {
    id: "ch2_compare",
    durationFrames: sec(12.0),
    render: () => (
      <ComparisonCard
        leftLabel="Crown Postal Service"
        leftValue="4 days"
        rightLabel="Rothschild Network"
        rightValue="32 hours"
        title="Brussels → London"
      />
    ),
  },
  {
    id: "ch2_route_map",
    durationFrames: sec(17.0),
    render: () => (
      <MapAnnotation
        mapSrc={staticFile("five-arrows/img_europe_map_lowpoly.png")}
        annotations={[
          { type: "pin", position: { x: 0.55, y: 0.42 }, label: "Brussels", revealAtSeconds: 0.0 },
          {
            type: "route_arc",
            waypoints: [
              { x: 0.55, y: 0.42 },
              { x: 0.52, y: 0.45 },
              { x: 0.50, y: 0.40 },
            ],
            sprite: "🐎",
            revealAtSeconds: 1.5,
          },
          { type: "pin", position: { x: 0.50, y: 0.40 }, label: "Ostend", revealAtSeconds: 5.5 },
          {
            type: "route_arc",
            waypoints: [
              { x: 0.50, y: 0.40 },
              { x: 0.45, y: 0.42 },
              { x: 0.40, y: 0.45 },
            ],
            sprite: "⚓",
            revealAtSeconds: 6.0,
          },
          { type: "pin", position: { x: 0.40, y: 0.45 }, label: "London", revealAtSeconds: 10.5 },
        ]}
        durationFrames={sec(17.0)}
        theme={mmTheme as any}
      />
    ),
  },
  {
    id: "ch2_letter_seal",
    durationFrames: sec(10.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <DocumentReveal
          variant="signature"
          documentTitle="To: N. ROTHSCHILD"
          metadata="St Swithin's Lane · London"
          bodyText={"Most urgent\nBy private courier"}
          signatureText="J. Rothschild"
          theme={mmTheme as any}
          durationFrames={sec(10.0)}
        />
        <Stamp
          text="SEALED"
          rotationDeg={-9}
          impactAtSeconds={5.5}
          position={{ x: 0.78, y: 0.58 }}
          scale={0.5}
          theme={mmTheme as any}
          durationFrames={sec(10.0)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "ch2_paris_anchor",
    durationFrames: sec(12.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_letter_paris_pickup.png")}
        kenBurns="zoom_in"
      />
    ),
  },
  {
    id: "ch2_riders_relay",
    durationFrames: sec(10.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_riders_relay.png")}
        kenBurns="pan_right"
      />
    ),
  },
  {
    id: "ch2_roworth_lt",
    durationFrames: sec(12.11),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_roworth_north.png")}
        kenBurns="zoom_in_slow"
      />
    ),
  },

  // CHAPTER 3 ─────────────────────────────────────────────────────────────
  {
    id: "ch3_card",
    durationFrames: sec(5.89),
    render: () => (
      <ChapterCard
        chapterNumber={3}
        title="The Field at Waterloo"
        subtitle="Belgium · 18 June 1815"
        overrides={{
          backgroundImageSrc: staticFile("five-arrows/img_waterloo_aftermath.png"),
          backgroundOverlayOpacity: 0.7,
        }}
        theme={mmTheme as any}
        durationFrames={sec(5.89)}
      />
    ),
  },
  {
    id: "ch3_clock",
    durationFrames: sec(8.0),
    render: () => (
      <ClockReveal
        targetTime="20:00"
        dateLabel="18 June 1815"
        caption="The hour Wellington's victory was sealed"
        theme={mmTheme as any}
        durationFrames={sec(8.0)}
      />
    ),
  },
  {
    id: "ch3_battle_aft",
    durationFrames: sec(14.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_waterloo_aftermath.png")}
        kenBurns="slow_zoom"
      />
    ),
  },
  {
    id: "ch3_napoleon_ended",
    durationFrames: sec(10.0),
    render: () => (
      <CenterTextCard
        text="Twenty-three years of continental war — over."
        size={64}
      />
    ),
  },
  {
    id: "ch3_channel_dark",
    durationFrames: sec(12.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_channel_dark.png")}
        kenBurns="parallax"
      />
    ),
  },
  {
    id: "ch3_letter_in_coat",
    durationFrames: sec(9.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <AssetFrame
          variant="document"
          src={staticFile("five-arrows/img_letter_close.png")}
          captionText="Folded · Sealed · Tucked"
          aspectRatio="16/9"
          theme={mmTheme as any}
          durationFrames={sec(9.0)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "ch3_ostend_dock",
    durationFrames: sec(11.14),
    render: () => (
      <MapAnnotation
        mapSrc={staticFile("five-arrows/img_europe_map_lowpoly.png")}
        cameraStart={{ focalX: 0.5, focalY: 0.4, zoom: 1.0 }}
        cameraEnd={{ focalX: 0.5, focalY: 0.4, zoom: 2.4 }}
        annotations={[
          {
            type: "pulse",
            position: { x: 0.50, y: 0.40 },
            label: "Ostend",
            revealAtSeconds: 0.0,
          },
          {
            type: "region_label",
            position: { x: 0.46, y: 0.55 },
            text: "Packet boat waiting · sails ready",
            revealAtSeconds: 1.5,
          },
        ]}
        durationFrames={sec(11.14)}
        theme={mmTheme as any}
      />
    ),
  },

  // CHAPTER 4 ─────────────────────────────────────────────────────────────
  {
    id: "ch4_card",
    durationFrames: sec(5.86),
    render: () => (
      <ChapterCard
        chapterNumber={4}
        title="The Quiet Trade"
        subtitle="London · Dawn · 20 June 1815"
        overrides={{
          backgroundImageSrc: staticFile("five-arrows/img_nathan_dawn.png"),
          backgroundOverlayOpacity: 0.7,
        }}
        theme={mmTheme as any}
        durationFrames={sec(5.86)}
      />
    ),
  },
  {
    id: "ch4_dawn_window",
    durationFrames: sec(12.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_nathan_dawn.png")}
        kenBurns="slow_zoom_in"
      />
    ),
  },
  {
    id: "ch4_typewriter_silence",
    durationFrames: sec(10.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <ImageScene
          src={staticFile("five-arrows/img_nathan_dawn.png")}
          kenBurns="hold_then_drift"
        />
        <AbsoluteFill
          style={{
            background: "rgba(8,12,22,0.30)",
          }}
        />
        <TypewriterText
          text="He says nothing. He writes nothing. He doesn't tell his wife."
          charsPerSecond={18}
          theme={mmTheme as any}
          durationFrames={sec(10.0)}
        />
      </AbsoluteFill>
    ),
  },
  {
    id: "ch4_to_exchange",
    durationFrames: sec(10.0),
    render: () => (
      <ImageScene
        src={staticFile("five-arrows/img_walking_to_xchg.png")}
        kenBurns="pan_forward"
      />
    ),
  },
  {
    id: "ch4_chart_collapse_buy",
    durationFrames: sec(16.0),
    render: () => (
      <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
        <div
          style={{
            position: "absolute",
            top: 60,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: (mmTheme as any).fontHeading,
            fontWeight: 700,
            fontSize: 36,
            color: (mmTheme as any).text,
            letterSpacing: "0.05em",
            textShadow: TEXT_STROKE,
            zIndex: 2,
          }}
        >
          THE TRADE · 20 JUNE 1815
        </div>
        <AbsoluteFill style={{ paddingTop: 150, paddingLeft: 80, paddingRight: 80, paddingBottom: 60 }}>
          <LineChart
            series={[
              {
                label: "Bond Price",
                data: [
                  { x: 0, y: 100 },
                  { x: 1, y: 86 },
                  { x: 2, y: 64 },
                  { x: 3, y: 41 },
                  { x: 4, y: 38 },
                  { x: 5, y: 56 },
                  { x: 6, y: 78 },
                  { x: 7, y: 95 },
                ],
              },
            ]}
            xLabel="Hour of trading"
            yLabel="Index"
            showMarkers
            showGrid
            animationStyle="draw"
            colors={["#c9a84c"]}
            backgroundColor={(mmTheme as any).bg}
            textColor={(mmTheme as any).text}
            gridColor="#3a3a4a"
            fontFamily="Georgia"
          />
        </AbsoluteFill>
      </AbsoluteFill>
    ),
  },
  {
    id: "ch4_calder_interp",
    durationFrames: sec(14.0),
    render: () => (
      <QuoteCard
        variant="centered_no_portrait"
        quote="I think this was the moment the modern financial system quietly began. You might disagree."
        attribution="— CALDER"
        theme={mmTheme as any}
        durationFrames={sec(14.0)}
      />
    ),
  },
  {
    id: "ch4_close",
    durationFrames: sec(13.96),
    render: () => (
      <EpisodeHeroTitle
        title="THE QUIET TRADE"
        subtitle="The Five Arrows · Episode 1"
      />
    ),
  },
];

// ---------------------------------------------------------------------------
// OVERLAYS — render on top of the scene track at absolute frame ranges.
// ---------------------------------------------------------------------------
type OverlaySpec = {
  id: string;
  fromFrame: number;
  durationFrames: number;
  render: () => React.ReactElement;
};

const overlayList: OverlaySpec[] = [
  {
    id: "ov_h02_chip",
    fromFrame: sec(6.5),
    durationFrames: sec(7.5),
    render: () => (
      <ProviderChip
        providers={["Kling 2.5 (v3/standard)"]}
        label="AI VIDEO"
        position="top-right"
      />
    ),
  },
  {
    id: "ov_h_year",
    fromFrame: sec(22.5),
    durationFrames: sec(5.0),
    render: () => (
      <LowerThird
        variant="news_ticker"
        name="LONDON · 19 JUNE 1815"
        theme={mmTheme as any}
        durationFrames={sec(5.0)}
      />
    ),
  },
  {
    id: "ov_h07_chip",
    fromFrame: sec(47.0),
    durationFrames: sec(9.0),
    render: () => (
      <ProviderChip
        providers={["Veo 3.1 Fast (Google)"]}
        label="AI VIDEO"
        position="top-right"
      />
    ),
  },
  {
    id: "ov_c_section",
    fromFrame: sec(71.5),
    durationFrames: sec(5.0),
    render: () => (
      <SectionTitle title="COLD OPEN · 1815" position="top-left" accentColor={(mmTheme as any).accent} />
    ),
  },
  {
    id: "ov_c05_chip",
    fromFrame: sec(108.0),
    durationFrames: sec(9.0),
    render: () => (
      <ProviderChip
        providers={["Seedance 1.0 Fast"]}
        label="AI VIDEO"
        position="top-right"
      />
    ),
  },
  {
    id: "ov_c08_chip",
    fromFrame: sec(136.0),
    durationFrames: sec(10.0),
    render: () => (
      <ProviderChip
        providers={["MiniMax Hailuo 02"]}
        label="AI VIDEO"
        position="top-right"
      />
    ),
  },
  {
    id: "ov_ch2_section",
    fromFrame: sec(256.0),
    durationFrames: sec(5.0),
    render: () => <SectionTitle title="CHAPTER 2" position="top-left" accentColor={(mmTheme as any).accent} />,
  },
  {
    id: "ov_ch2_lt_roworth",
    fromFrame: sec(322.5),
    durationFrames: sec(5.0),
    render: () => (
      <LowerThird
        variant="simple_left"
        name="ROWORTH"
        role="Rothschild courier · Waterloo dispatch"
        theme={mmTheme as any}
        durationFrames={sec(5.0)}
      />
    ),
  },
  {
    id: "ov_ch3_section",
    fromFrame: sec(335.0),
    durationFrames: sec(5.0),
    render: () => (
      <SectionTitle title="CHAPTER 3 · WATERLOO" position="top-left" accentColor={(mmTheme as any).accent} />
    ),
  },
  {
    id: "ov_ch4_section",
    fromFrame: sec(405.0),
    durationFrames: sec(5.0),
    render: () => (
      <SectionTitle title="CHAPTER 4 · LONDON, DAWN" position="top-left" accentColor={(mmTheme as any).accent} />
    ),
  },
];

// ---------------------------------------------------------------------------
// MAIN composition
// ---------------------------------------------------------------------------
export const FiveArrowsEpisode: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: (mmTheme as any).bg }}>
      {/* Master VO track */}
      <Audio src={staticFile("five-arrows/master.wav")} />

      {/* Background scene track — sequential 49 scenes via Series */}
      <Series>
        {sceneList.map((sc) => (
          <Series.Sequence
            key={sc.id}
            durationInFrames={sc.durationFrames}
            name={sc.id}
          >
            <SceneFade>{sc.render()}</SceneFade>
          </Series.Sequence>
        ))}
      </Series>

      {/* Overlay layer — absolute-frame Sequence per overlay so they composite
          on top of whatever scene is playing at that frame */}
      {overlayList.map((ov) => (
        <Sequence
          key={ov.id}
          from={ov.fromFrame}
          durationInFrames={ov.durationFrames}
          name={ov.id}
        >
          {ov.render()}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
