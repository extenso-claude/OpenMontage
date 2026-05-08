/**
 * Letter Dynasty v3 — full episode wrapper.
 * Hook → 2.5s pause → Cold Open → 4s "Chapter 1" title card → Chapter 1 → 4s "Chapter 2" title card → Chapter 2 → 6s end-card hold.
 */

import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { MM } from "./MMSvgV3";
import { TEXT_STROKE, FPS } from "../beat-helpers";
import { LetterDynastyHookV3, LETTER_HOOK_V3_DURATION_FRAMES } from "./HookV3";
import { LetterDynastyColdOpenV3, LETTER_COLD_OPEN_V3_DURATION_FRAMES } from "./ColdOpenV3";
import { LetterDynastyChapter1V3, LETTER_CHAPTER1_V3_DURATION_FRAMES } from "./Chapter1V3";
import { LetterDynastyChapter2V3, LETTER_CHAPTER2_V3_DURATION_FRAMES } from "./Chapter2V3";

const PAUSE_HOOK_TO_CO = Math.round(2.5 * FPS);
const PAUSE_CHAPTER_CARD = Math.round(4.0 * FPS);
const PAUSE_END_HOLD = Math.round(6.0 * FPS);

const HOOK_END = LETTER_HOOK_V3_DURATION_FRAMES;
const CO_START = HOOK_END + PAUSE_HOOK_TO_CO;
const CO_END = CO_START + LETTER_COLD_OPEN_V3_DURATION_FRAMES;
const C1_TITLE_START = CO_END;
const C1_START = C1_TITLE_START + PAUSE_CHAPTER_CARD;
const C1_END = C1_START + LETTER_CHAPTER1_V3_DURATION_FRAMES;
const C2_TITLE_START = C1_END;
const C2_START = C2_TITLE_START + PAUSE_CHAPTER_CARD;
const C2_END = C2_START + LETTER_CHAPTER2_V3_DURATION_FRAMES;
const END_HOLD = C2_END + PAUSE_END_HOLD;

export const LETTER_DYNASTY_FULL_V3_DURATION_FRAMES = END_HOLD;

const ChapterTitleCard: React.FC<{ chapterNum: number; title: string }> = ({ chapterNum, title }) => {
  const frame = useCurrentFrame();
  // Fade in 0-1.5s, hold 1s, fade out 1.5s
  const opacity = interpolate(
    frame,
    [0, 1.5 * FPS, 2.5 * FPS, 4 * FPS],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", opacity }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontSize: 30,
            color: MM.gold,
            letterSpacing: "0.3em",
            marginBottom: 24,
            ...TEXT_STROKE,
          }}
        >
          CHAPTER {chapterNum}
        </div>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 96,
            color: MM.cream,
            letterSpacing: "0.02em",
            ...TEXT_STROKE,
          }}
        >
          {title}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const EndHold: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 1.5 * FPS, 5 * FPS, 6 * FPS], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: MM.bg }}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", opacity }}>
        <div
          style={{
            fontFamily: "Georgia, serif",
            fontWeight: 700,
            fontSize: 78,
            color: MM.gold,
            letterSpacing: "0.06em",
            ...TEXT_STROKE,
          }}
        >
          MIDNIGHT MAGNATES
        </div>
        <div
          style={{
            marginTop: 18,
            fontFamily: "Georgia, serif",
            fontStyle: "italic",
            fontSize: 28,
            color: MM.cream,
            letterSpacing: "0.18em",
          }}
        >
          THE LETTER THAT BUILT A DYNASTY
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const LetterDynastyFullV3: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: MM.bg }}>
    <Sequence from={0} durationInFrames={LETTER_HOOK_V3_DURATION_FRAMES}>
      <LetterDynastyHookV3 />
    </Sequence>
    <Sequence from={CO_START} durationInFrames={LETTER_COLD_OPEN_V3_DURATION_FRAMES}>
      <LetterDynastyColdOpenV3 />
    </Sequence>
    <Sequence from={C1_TITLE_START} durationInFrames={PAUSE_CHAPTER_CARD}>
      <ChapterTitleCard chapterNum={1} title="The Five Arrows" />
    </Sequence>
    <Sequence from={C1_START} durationInFrames={LETTER_CHAPTER1_V3_DURATION_FRAMES}>
      <LetterDynastyChapter1V3 />
    </Sequence>
    <Sequence from={C2_TITLE_START} durationInFrames={PAUSE_CHAPTER_CARD}>
      <ChapterTitleCard chapterNum={2} title="The Couriers" />
    </Sequence>
    <Sequence from={C2_START} durationInFrames={LETTER_CHAPTER2_V3_DURATION_FRAMES}>
      <LetterDynastyChapter2V3 />
    </Sequence>
    <Sequence from={C2_END} durationInFrames={PAUSE_END_HOLD}>
      <EndHold />
    </Sequence>
  </AbsoluteFill>
);
