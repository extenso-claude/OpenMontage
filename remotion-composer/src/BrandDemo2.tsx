/**
 * BrandDemo2 — sample reel for the second batch of brand components.
 *
 * Shows: ChapterCard (channel + era override), LowerThird (3 variants),
 * QuoteCard (2 variants), ClockReveal, CalendarReveal, ParallaxStill,
 * DocumentReveal (highlight + redact), SocialMediaPopup (tweet + text),
 * CalloutArrow over a wide shot, NetworkMap, BrandedChart.
 *
 * Render via:
 *   npx remotion render src/index.tsx BrandDemo2 out.mov \\
 *     --props='{"channel":"midnight_magnates"}' \\
 *     --codec=prores --pro-res-profile=hq
 */
import { AbsoluteFill, Img, Series, staticFile } from "remotion";
import {
  TypewriterText,
  ChapterCard,
  ERA_PRESETS,
  LowerThird,
  QuoteCard,
  ClockReveal,
  CalendarReveal,
  ParallaxStill,
  DocumentReveal,
  SocialMediaPopup,
  CalloutArrow,
  NetworkMap,
  BrandedChart,
  resolveTheme,
  BrandTheme,
} from "./components";
import huxleyTheme from "./components/brand/themes/grandpa_huxley.json";
import mmTheme from "./components/brand/themes/midnight_magnates.json";

export interface BrandDemo2Props {
  channel: "grandpa_huxley" | "midnight_magnates";
}

const THEMES: Record<BrandDemo2Props["channel"], Partial<BrandTheme>> = {
  grandpa_huxley: huxleyTheme as Partial<BrandTheme>,
  midnight_magnates: mmTheme as Partial<BrandTheme>,
};

const FPS = 24;
const sec = (s: number) => Math.round(s * FPS);

// Scene durations in seconds
const SCENE_DURATIONS = [
  5, // 1. Title
  4, // 2. ChapterCard (channel theme)
  4, // 3. ChapterCard (wild west override)
  4, // 4. LowerThird simple_left
  4, // 5. LowerThird boxed
  4, // 6. LowerThird news_ticker
  6, // 7. QuoteCard centered
  6, // 8. QuoteCard portrait_left
  5, // 9. ClockReveal
  5, // 10. CalendarReveal
  6, // 11. ParallaxStill
  6, // 12. DocumentReveal highlight
  7, // 13. DocumentReveal redact
  6, // 14. SocialMediaPopup tweet
  7, // 15. SocialMediaPopup text_message
  6, // 16. CalloutArrow over wide shot
  8, // 17. NetworkMap
  6, // 18. BrandedChart bar
  4, // 19. End
];

const TOTAL_SECONDS = SCENE_DURATIONS.reduce((a, b) => a + b, 0);
export const BRAND_DEMO_2_DURATION_FRAMES = sec(TOTAL_SECONDS);

export const BrandDemo2: React.FC<BrandDemo2Props> = ({ channel }) => {
  const theme = resolveTheme(THEMES[channel]);
  const isMM = channel === "midnight_magnates";

  // Channel-specific demo content
  const channelTitle = isMM ? "MIDNIGHT MAGNATES" : "GRANDPA HUXLEY";

  const chapterTitle = isMM ? "Five Sons, Five Capitals" : "The Marketplace at Athens";
  const chapterSubtitle = isMM
    ? "How a single family wired Europe's information"
    : "Where philosophy was an argument, not a textbook";

  const wildWestTitle = isMM
    ? "The Marshal They Forgot"
    : "Wisdom From The Frontier";
  const wildWestSubtitle = isMM
    ? "Bass Reeves, when the law had to ride alone"
    : "Lessons from those who lived without comforts";

  const lowerThirdName = isMM ? "Mayer Amschel Rothschild" : "Marcus Aurelius";
  const lowerThirdRole = isMM
    ? "Founder of the Rothschild banking dynasty"
    : "Stoic philosopher and Roman emperor";
  const lowerThirdCategory = isMM ? "BANKING DYNASTY" : "STOIC PHILOSOPHY";

  const quote = isMM
    ? "I care not what puppet is placed upon the throne of England... the man who controls Britain's money supply controls the British Empire."
    : "You have power over your mind — not outside events. Realize this, and you will find strength.";
  const attribution = isMM ? "Nathan Mayer Rothschild" : "Marcus Aurelius, Meditations";

  const photo1 = isMM ? staticFile("brand_demo/mm/vault.jpg") : staticFile("brand_demo/huxley/candle.jpg");
  const photo2 = isMM ? staticFile("brand_demo/mm/chess.jpg") : staticFile("brand_demo/huxley/book.jpg");

  // Document body
  const docBody = isMM
    ? `Memorandum dated 18 June 1815.\n\nThe outcome at Waterloo is no longer in doubt. Our courier reached London at dawn, twenty hours ahead of the official dispatches. Nathan acted at the Exchange before the news became public.\n\nThe profits from this morning are sufficient to settle every account in the Hapsburg dossier. Recommend we close all open positions before the official report reaches the Treasury.`
    : `On the practice of attention.\n\nThe mind, untrained, runs ahead of the body and arrives nowhere. The first lesson of the philosopher is to bring the mind back. Not once, but every hour. Not by force, but by gentle return.\n\nWhat the world calls patience is only the long habit of returning. Begin again. The work of a lifetime is the work of a moment, performed many times.`;

  const docPhrasesHighlight = isMM
    ? ["twenty hours ahead", "before the news became public"]
    : ["bring the mind back", "every hour", "long habit of returning"];

  const docPhrasesRedact = isMM
    ? ["the Hapsburg dossier", "the Treasury"]
    : ["the long habit of returning", "the work of a moment"];

  // Tweet content
  const tweetAuthor = isMM ? "John P. Morgan" : "Lao Tzu Quotes";
  const tweetHandle = isMM ? "@jpmorgan_official" : "@daodejing";
  const tweetBody = isMM
    ? "Gold is money. Everything else is credit."
    : "When you are content to be simply yourself and don't compare or compete, everybody will respect you.";
  const tweetTime = isMM ? "Dec 14, 1912 · The New York Banker" : "Verse 8 · Tao Te Ching";

  // Text message bubbles
  const textMessages = isMM
    ? [
        { side: "left" as const, text: "Saw the wire from Frankfurt", revealAtSeconds: 0.5 },
        { side: "right" as const, text: "We move tonight, before London reads it", revealAtSeconds: 2.0 },
        { side: "left" as const, text: "Discrete. Through the side ledger.", revealAtSeconds: 3.5 },
        { side: "right" as const, text: "Always.", revealAtSeconds: 4.8 },
      ]
    : [
        { side: "left" as const, text: "Couldn't sleep again", revealAtSeconds: 0.5 },
        { side: "right" as const, text: "Tell me what's running through your head", revealAtSeconds: 2.0 },
        { side: "left" as const, text: "Everything I should have said years ago", revealAtSeconds: 3.5 },
        { side: "right" as const, text: "Then write it down. We'll read it together at sunrise.", revealAtSeconds: 4.8 },
      ];

  // Network map
  const networkNodes = isMM
    ? [
        { id: "mayer", label: "Mayer Amschel", role: "Founder · Frankfurt", x: 500, y: 300, isCenter: true },
        { id: "amschel", label: "Amschel", role: "Frankfurt", x: 250, y: 130 },
        { id: "salomon", label: "Salomon", role: "Vienna", x: 750, y: 130 },
        { id: "nathan", label: "Nathan", role: "London", x: 150, y: 360 },
        { id: "carl", label: "Carl", role: "Naples", x: 500, y: 510 },
        { id: "james", label: "James", role: "Paris", x: 850, y: 360 },
      ]
    : [
        { id: "socrates", label: "Socrates", role: "470 – 399 BC", x: 500, y: 300, isCenter: true },
        { id: "plato", label: "Plato", role: "Founded the Academy", x: 250, y: 150 },
        { id: "aristotle", label: "Aristotle", role: "Founded the Lyceum", x: 750, y: 150 },
        { id: "xenophon", label: "Xenophon", role: "Soldier–philosopher", x: 250, y: 460 },
        { id: "zeno", label: "Zeno of Citium", role: "Founded Stoicism", x: 750, y: 460 },
      ];

  const networkEdges = isMM
    ? [
        { fromId: "mayer", toId: "amschel", type: "transaction" as const, label: "1798" },
        { fromId: "mayer", toId: "salomon", type: "transaction" as const, label: "1820" },
        { fromId: "mayer", toId: "nathan", type: "transaction" as const, label: "1798" },
        { fromId: "mayer", toId: "carl", type: "transaction" as const, label: "1821" },
        { fromId: "mayer", toId: "james", type: "transaction" as const, label: "1812" },
      ]
    : [
        { fromId: "socrates", toId: "plato", type: "mentor" as const, label: "c. 408 BC" },
        { fromId: "socrates", toId: "xenophon", type: "mentor" as const, label: "c. 405 BC" },
        { fromId: "plato", toId: "aristotle", type: "mentor" as const, label: "c. 367 BC" },
        { fromId: "plato", toId: "zeno", type: "mentor" as const, label: "indirect" },
      ];

  // Chart data
  const chartData = isMM
    ? [
        { label: "London", value: 9.4 },
        { label: "Paris", value: 7.2 },
        { label: "Frankfurt", value: 5.6 },
        { label: "Vienna", value: 4.1 },
        { label: "Naples", value: 2.3 },
      ]
    : [
        { label: "Stoicism", value: 535 },
        { label: "Platonism", value: 412 },
        { label: "Epicurean", value: 388 },
        { label: "Cynic", value: 290 },
        { label: "Skeptic", value: 245 },
      ];

  const chartTitle = isMM
    ? "Rothschild Branch Capital · 1850 (£M, est.)"
    : "Years of Active Tradition · Hellenistic Schools";

  return (
    <AbsoluteFill style={{ background: theme.bg }}>
      <Series>
        {/* 1. Title */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[0])}>
          <TypewriterText
            text={`${channelTitle}\nbrand components · batch 2`}
            charsPerSecond={14}
            fontSize={64}
            theme={theme}
            durationFrames={sec(SCENE_DURATIONS[0])}
          />
        </Series.Sequence>

        {/* 2. ChapterCard — channel theme */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[1])}>
          <ChapterCard
            chapterNumber={3}
            title={chapterTitle}
            subtitle={chapterSubtitle}
            durationFrames={sec(SCENE_DURATIONS[1])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 3. ChapterCard — wild west override */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[2])}>
          <ChapterCard
            chapterNumber={4}
            title={wildWestTitle}
            subtitle={wildWestSubtitle}
            overrides={ERA_PRESETS.wild_west}
            durationFrames={sec(SCENE_DURATIONS[2])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 4. LowerThird simple_left — over a photo */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[3])}>
          <AbsoluteFill style={{ background: theme.bg }}>
            <Img src={photo1} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.6)" }} />
            <CornerLabel theme={theme} text="LowerThird · simple_left" />
            <LowerThird
              variant="simple_left"
              name={lowerThirdName}
              role={lowerThirdRole}
              durationFrames={sec(SCENE_DURATIONS[3])}
              theme={theme}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* 5. LowerThird boxed */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[4])}>
          <AbsoluteFill style={{ background: theme.bg }}>
            <Img src={photo2} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.55)" }} />
            <CornerLabel theme={theme} text="LowerThird · boxed" />
            <LowerThird
              variant="boxed"
              name={lowerThirdName}
              role={lowerThirdRole}
              category={lowerThirdCategory}
              durationFrames={sec(SCENE_DURATIONS[4])}
              theme={theme}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* 6. LowerThird news_ticker */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[5])}>
          <AbsoluteFill style={{ background: theme.bg }}>
            <Img src={photo1} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.6)" }} />
            <CornerLabel theme={theme} text="LowerThird · news_ticker" />
            <LowerThird
              variant="news_ticker"
              name={lowerThirdName}
              role={lowerThirdRole}
              category={lowerThirdCategory}
              durationFrames={sec(SCENE_DURATIONS[5])}
              theme={theme}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* 7. QuoteCard centered_no_portrait */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[6])}>
          <QuoteCard
            variant="centered_no_portrait"
            quote={quote}
            attribution={attribution}
            durationFrames={sec(SCENE_DURATIONS[6])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 8. QuoteCard portrait_left */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[7])}>
          <QuoteCard
            variant="portrait_left"
            quote={quote}
            attribution={attribution}
            portraitSrc={photo2}
            durationFrames={sec(SCENE_DURATIONS[7])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 9. ClockReveal */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[8])}>
          <ClockReveal
            targetTime={isMM ? "06:42" : "23:58"}
            dateLabel={isMM ? "1815 · June 18 · Brussels" : "Just before midnight"}
            caption={isMM ? "The hour the courier rode" : "The quiet hour"}
            durationFrames={sec(SCENE_DURATIONS[8])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 10. CalendarReveal */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[9])}>
          <CalendarReveal
            month={isMM ? "October" : "April"}
            year={isMM ? "1929" : "121"}
            targetDay={isMM ? 28 : 26}
            firstDayOfWeek={isMM ? 2 : 0}
            daysInMonth={isMM ? 31 : 30}
            supportingDays={isMM ? [24, 25, 29] : []}
            caption={isMM ? "Black Tuesday" : "On the day Marcus Aurelius was born"}
            durationFrames={sec(SCENE_DURATIONS[9])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 11. ParallaxStill */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[10])}>
          <ParallaxStill
            backgroundSrc={photo1}
            motion="right"
            caption={isMM ? "What the vault held could buy a state" : "A single candle, a quiet hour"}
            durationFrames={sec(SCENE_DURATIONS[10])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 12. DocumentReveal highlight */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[11])}>
          <DocumentReveal
            variant="highlight"
            documentTitle={isMM ? "Internal Memorandum" : "On Attention — Notebook IV"}
            metadata={isMM ? "Frankfurt · 18 June 1815 · File 7421-A" : "Aurelius · Personal Notebooks"}
            bodyText={docBody}
            phrases={docPhrasesHighlight}
            durationFrames={sec(SCENE_DURATIONS[11])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 13. DocumentReveal redact */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[12])}>
          <DocumentReveal
            variant="redact"
            documentTitle={isMM ? "DECLASSIFIED — INCIDENT REPORT" : "On Attention — Notebook IV"}
            metadata={isMM ? "1815 · For partner eyes only" : "(redaction shown for demo only)"}
            bodyText={docBody}
            phrases={docPhrasesRedact}
            durationFrames={sec(SCENE_DURATIONS[12])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 14. SocialMediaPopup tweet */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[13])}>
          <SocialMediaPopup
            variant="tweet"
            authorName={tweetAuthor}
            authorHandle={tweetHandle}
            avatarSrc={photo2}
            body={tweetBody}
            timestamp={tweetTime}
            stats={isMM ? { replies: 2400, retweets: 18000, likes: 92000 } : { replies: 540, retweets: 4100, likes: 22000 }}
            durationFrames={sec(SCENE_DURATIONS[13])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 15. SocialMediaPopup text_message */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[14])}>
          <SocialMediaPopup
            variant="text_message"
            contactName={isMM ? "James (Paris)" : "An old friend"}
            bubbles={textMessages}
            durationFrames={sec(SCENE_DURATIONS[14])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 16. CalloutArrow over a wide shot */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[15])}>
          <AbsoluteFill style={{ background: theme.bg }}>
            <Img src={photo1} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.7)" }} />
            <CornerLabel theme={theme} text="CalloutArrow · multi-callout on wide shot" />
            <CalloutArrow
              target={{ x: 0.62, y: 0.45 }}
              label={{ x: 0.82, y: 0.18 }}
              title={isMM ? "The signal lamp" : "The candle"}
              description={isMM ? "Lit only when the courier was overdue" : "A cue for evening practice"}
              glyph="◉"
              revealAtSeconds={0.4}
              durationFrames={sec(SCENE_DURATIONS[15])}
              theme={theme}
            />
            <CalloutArrow
              target={{ x: 0.32, y: 0.62 }}
              label={{ x: 0.18, y: 0.82 }}
              title={isMM ? "Side ledger" : "Open volume"}
              description={isMM ? "Off the books, always" : "The work of returning"}
              glyph="◇"
              revealAtSeconds={1.8}
              durationFrames={sec(SCENE_DURATIONS[15])}
              theme={theme}
            />
          </AbsoluteFill>
        </Series.Sequence>

        {/* 17. NetworkMap */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[16])}>
          <NetworkMap
            nodes={networkNodes}
            edges={networkEdges}
            title={isMM ? "Five Capitals · The Network" : "The Lineage From Athens"}
            durationFrames={sec(SCENE_DURATIONS[16])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 18. BrandedChart bar */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[17])}>
          <BrandedChart
            kind="bar"
            data={chartData}
            title={chartTitle}
            durationFrames={sec(SCENE_DURATIONS[17])}
            theme={theme}
          />
        </Series.Sequence>

        {/* 19. End */}
        <Series.Sequence durationInFrames={sec(SCENE_DURATIONS[18])}>
          <TypewriterText
            text={`end of batch 2`}
            charsPerSecond={10}
            fontSize={48}
            theme={theme}
            durationFrames={sec(SCENE_DURATIONS[18])}
          />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};

const CornerLabel: React.FC<{ theme: BrandTheme; text: string }> = ({ theme, text }) => (
  <div
    style={{
      position: "absolute",
      top: 36,
      left: 36,
      fontFamily: theme.fontHeading,
      fontSize: 16,
      color: theme.muted,
      letterSpacing: "0.18em",
      textTransform: "uppercase",
      background: `${theme.bg}AA`,
      padding: "6px 12px",
      border: `1px solid ${theme.muted}`,
      pointerEvents: "none",
    }}
  >
    {text}
  </div>
);
