/**
 * Letter Dynasty — full episode composition.
 * Chains Hook → Cold Open → Chapter 1 → Chapter 2 in sequence.
 * Total: 5:34 (8019 frames @ 24fps).
 */

import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { MM } from "./MMSvg";
import {
  LETTER_HOOK_V2_DURATION_FRAMES,
  LetterDynastyHookV2,
} from "./HookV2";
import {
  LETTER_COLD_OPEN_V2_DURATION_FRAMES,
  LetterDynastyColdOpenV2,
} from "./ColdOpenV2";
import {
  LETTER_CHAPTER1_V2_DURATION_FRAMES,
  LetterDynastyChapter1V2,
} from "./Chapter1V2";
import {
  LETTER_CHAPTER2_V2_DURATION_FRAMES,
  LetterDynastyChapter2V2,
} from "./Chapter2V2";

const HOOK_END = LETTER_HOOK_V2_DURATION_FRAMES;
const CO_END = HOOK_END + LETTER_COLD_OPEN_V2_DURATION_FRAMES;
const C1_END = CO_END + LETTER_CHAPTER1_V2_DURATION_FRAMES;
const C2_END = C1_END + LETTER_CHAPTER2_V2_DURATION_FRAMES;

export const LETTER_DYNASTY_FULL_V2_DURATION_FRAMES = C2_END;

export const LetterDynastyFullV2: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: MM.bg }}>
    <Sequence from={0} durationInFrames={LETTER_HOOK_V2_DURATION_FRAMES}>
      <LetterDynastyHookV2 />
    </Sequence>
    <Sequence
      from={HOOK_END}
      durationInFrames={LETTER_COLD_OPEN_V2_DURATION_FRAMES}
    >
      <LetterDynastyColdOpenV2 />
    </Sequence>
    <Sequence
      from={CO_END}
      durationInFrames={LETTER_CHAPTER1_V2_DURATION_FRAMES}
    >
      <LetterDynastyChapter1V2 />
    </Sequence>
    <Sequence
      from={C1_END}
      durationInFrames={LETTER_CHAPTER2_V2_DURATION_FRAMES}
    >
      <LetterDynastyChapter2V2 />
    </Sequence>
  </AbsoluteFill>
);
