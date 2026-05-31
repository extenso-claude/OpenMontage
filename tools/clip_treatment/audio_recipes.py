"""Audio Treatment Library
==========================

Recipes for transformative audio treatment of third-party clip audio.
Used when a clip's source audio is being KEPT (e.g., Carter's toast,
Khomeini speech) but needs transformation for fair-use cover.

Five canonical roles per clip-moment (see clip_vo_dialogue_handling memory):

- vo-over    -> source audio gets muted or heavily ducked, VO plays through
- vo-pause   -> source audio leads, VO is silent for this moment
- mixed      -> source audio is treated AND VO speaks; ducked under -8dB
- ambient    -> source audio replaced with custom ambient bed
- stripped   -> source audio fully removed, room tone or silence in its place

The treatments below apply when audio is being KEPT (vo-pause / mixed roles).
Pure muting is handled by the FFmpeg `-an` flag at composition time.
"""
from __future__ import annotations

import dataclasses
import shlex
import subprocess
from pathlib import Path
from typing import Callable, Dict


@dataclasses.dataclass
class AudioRecipe:
    name: str
    description: str
    transformative_score: int  # 1=marginal, 5=fundamentally different waveform
    af_builder: Callable[[], str]
    best_for: list[str]

    def filter_chain(self) -> str:
        return self.af_builder()


# ---------------------------------------------------------------------------
# Pitch / formant shifts
# ---------------------------------------------------------------------------

def _pitch_down_4st():
    # 4 semitones down without speed change. asetrate then atempo to restore.
    return "asetrate=44100*0.7937,aresample=44100,atempo=1.26"


def _pitch_down_6st():
    return "asetrate=44100*0.7071,aresample=44100,atempo=1.4142"


def _pitch_up_3st():
    # Subtle pitch-up gives a slightly dreamy quality good for sleep niche.
    return "asetrate=44100*1.1892,aresample=44100,atempo=0.8409"


def _pitch_up_1st():
    # +1 semitone — almost imperceptible character shift; useful as a mild "different voice" gesture.
    return "asetrate=44100*1.05946,aresample=44100,atempo=0.94387"


def _pitch_up_2st():
    # +2 semitones — noticeable lift; preserves intelligibility well.
    return "asetrate=44100*1.12246,aresample=44100,atempo=0.89090"


def _pitch_down_1st():
    # -1 semitone — subtle deepening; the lightest copyright-defeat tier.
    return "asetrate=44100*0.94387,aresample=44100,atempo=1.05946"


def _pitch_down_2st():
    # -2 semitones — moderate deepening; the safest "still natural" floor.
    return "asetrate=44100*0.89090,aresample=44100,atempo=1.12246"


# ---------------------------------------------------------------------------
# EQ / band-passes
# ---------------------------------------------------------------------------

def _telephone_eq():
    # Tight band-pass 300-3400Hz mimics telephone line. Strong "found audio" feel.
    return "highpass=f=300,lowpass=f=3400,acompressor=threshold=0.5:ratio=3"


def _radio_eq():
    # AM-radio compression + bandwidth
    return "highpass=f=200,lowpass=f=5000,acompressor=threshold=0.4:ratio=4:attack=20:release=200"


def _muffled_pillow():
    # Heavy low-pass for "heard through a wall" / sleep memory feel
    return "lowpass=f=800,acompressor=threshold=0.6:ratio=2"


def _underwater():
    # Phasey, ducking, dreamy
    return "lowpass=f=1200,aphaser=in_gain=0.5:out_gain=0.7:delay=3:decay=0.6:speed=0.4"


# ---------------------------------------------------------------------------
# Space / reverb
# ---------------------------------------------------------------------------

def _memory_reverb():
    # Big slow-decay reverb, lows rolled off. The "this is a memory" treatment.
    return "highpass=f=400,aecho=0.7:0.7:80|200|400:0.4|0.3|0.2"


def _hallway_echo():
    return "aecho=0.6:0.6:60|150:0.5|0.3"


def _close_room():
    # Tight dry reverb — implies a small space, not the broadcast studio of source
    return "aecho=0.5:0.5:20|40:0.3|0.2"


# ---------------------------------------------------------------------------
# Combined "looks"
# ---------------------------------------------------------------------------

def _leaked_recording():
    # The most copyright-protective: pitch down + telephone EQ + a touch of reverb.
    return "asetrate=44100*0.7937,aresample=44100,atempo=1.26,highpass=f=300,lowpass=f=3400,acompressor=threshold=0.5:ratio=3,aecho=0.5:0.5:30|70:0.3|0.15"


def _dream_pitch_up():
    # Sleep-mood: pitch up slightly, soften, gentle reverb
    return "asetrate=44100*1.1225,aresample=44100,atempo=0.8909,lowpass=f=3500,aecho=0.6:0.6:50|120:0.4|0.25"


def _classified_archive():
    # Treatment for "this is an old declassified recording" feel.
    # Simplified to single -af chain: pitch-down + bandwidth + compressor.
    # Noise floor is handled by the compressor settings and the muffled low/high cuts.
    return "asetrate=44100*0.8909,aresample=44100,atempo=1.1225,highpass=f=200,lowpass=f=4500,acompressor=threshold=0.5:ratio=4:attack=20:release=300,aecho=0.4:0.4:30|80:0.2|0.1"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RECIPES: Dict[str, AudioRecipe] = {
    # Pitch shifts (highest transformative score)
    "pitch_down_1st":     AudioRecipe("pitch_down_1st",     "Pitch -1 semitone (mild deepening).",                                       2, _pitch_down_1st,     ["dialogue", "speech"]),
    "pitch_down_2st":     AudioRecipe("pitch_down_2st",     "Pitch -2 semitones (moderate deepening).",                                  3, _pitch_down_2st,     ["dialogue", "speech"]),
    "pitch_down_4st":     AudioRecipe("pitch_down_4st",     "Pitch -4 semitones (formant preserving via atempo).",                       4, _pitch_down_4st,     ["dialogue", "speech"]),
    "pitch_down_6st":     AudioRecipe("pitch_down_6st",     "Pitch -6 semitones (heavier disguise).",                                    5, _pitch_down_6st,     ["dialogue", "speech"]),
    "pitch_up_1st":       AudioRecipe("pitch_up_1st",       "Pitch +1 semitone (very mild lift).",                                       2, _pitch_up_1st,       ["dialogue", "ambient"]),
    "pitch_up_2st":       AudioRecipe("pitch_up_2st",       "Pitch +2 semitones (noticeable lift).",                                     3, _pitch_up_2st,       ["dialogue", "ambient"]),
    "pitch_up_3st":       AudioRecipe("pitch_up_3st",       "Pitch +3 semitones (dreamy / sleep-tuned).",                                4, _pitch_up_3st,       ["dialogue", "ambient"]),

    # EQ / band
    "telephone_eq":       AudioRecipe("telephone_eq",       "Telephone band-pass 300-3400Hz + compression.",                             3, _telephone_eq,       ["dialogue", "speech"]),
    "radio_eq":           AudioRecipe("radio_eq",           "AM-radio bandwidth + compression.",                                         3, _radio_eq,           ["dialogue", "broadcast"]),
    "muffled_pillow":     AudioRecipe("muffled_pillow",     "Heavy low-pass: 'heard through a wall'. Sleep-friendly.",                   3, _muffled_pillow,     ["ambient", "memory"]),
    "underwater":         AudioRecipe("underwater",         "Phasey low-pass: dreamy / submerged.",                                      3, _underwater,         ["ambient", "memory"]),

    # Space / reverb
    "memory_reverb":      AudioRecipe("memory_reverb",      "Big slow reverb, lows rolled off. 'Memory' feel.",                          3, _memory_reverb,      ["dialogue", "memory"]),
    "hallway_echo":       AudioRecipe("hallway_echo",       "Light hallway echo.",                                                       2, _hallway_echo,       ["dialogue", "speech"]),
    "close_room":         AudioRecipe("close_room",         "Tight dry reverb implying small space.",                                    2, _close_room,         ["dialogue"]),

    # Combined looks
    "leaked_recording":   AudioRecipe("leaked_recording",   "Pitch -4st + telephone EQ + light reverb. Maximum Content-ID-defeat.",       5, _leaked_recording,   ["dialogue", "speech"]),
    "dream_pitch_up":     AudioRecipe("dream_pitch_up",     "Pitch +2st + soft low-pass + gentle reverb. Sleep-mood.",                   4, _dream_pitch_up,     ["dialogue", "ambient"]),
    "classified_archive": AudioRecipe("classified_archive", "Pitch -2st + 200-4500Hz band + compression + reverb. 'Declassified' feel.", 4, _classified_archive, ["dialogue", "archival"]),
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def list_audio_recipes(min_score: int = 0) -> list[str]:
    return [n for n, r in RECIPES.items() if r.transformative_score >= min_score]


def apply_audio_treatment(
    input_path: str | Path,
    output_path: str | Path,
    recipe_name: str,
    keep_video: bool = True,
    overwrite: bool = True,
    normalize_to_lufs: float | None = -14.0,
) -> dict:
    """Apply a named audio recipe.

    normalize_to_lufs: if not None, append a loudnorm pass that brings the
    treated output to the target integrated LUFS. Defaults to -14 (broadcast
    spoken-word standard) so pitch-shifted / band-limited recipes don't feel
    quiet next to the untreated VO.
    """
    if recipe_name not in RECIPES:
        raise ValueError(f"Unknown recipe: {recipe_name}. Try: {list(RECIPES)}")

    recipe = RECIPES[recipe_name]
    af = recipe.filter_chain()
    if normalize_to_lufs is not None:
        af = f"{af},loudnorm=I={normalize_to_lufs}:TP=-1.5:LRA=11"

    # Pick audio codec from output extension so mp3 container gets libmp3lame, m4a/aac gets aac, etc.
    out_ext = Path(output_path).suffix.lower()
    if out_ext == ".mp3":
        acodec = ["libmp3lame", "-b:a", "192k"]
    elif out_ext in (".m4a", ".aac", ".mp4"):
        acodec = ["aac", "-b:a", "192k"]
    elif out_ext == ".wav":
        acodec = ["pcm_s16le"]
    else:
        acodec = ["aac", "-b:a", "192k"]

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-i", str(input_path),
        "-af", af,
    ]
    if keep_video:
        cmd.extend(["-c:v", "copy"])
    cmd.extend(["-c:a"] + acodec)
    cmd.append(str(output_path))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "recipe": recipe_name,
        "transformative_score": recipe.transformative_score,
        "input": str(input_path),
        "output": str(output_path),
        "filter_chain": af,
        "success": proc.returncode == 0,
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]) if proc.stderr else "",
        "cmd": " ".join(shlex.quote(c) for c in cmd),
    }


if __name__ == "__main__":
    print(f"Audio recipe count: {len(RECIPES)}")
    for name, r in RECIPES.items():
        print(f"  - {name:22s} (transform_score={r.transformative_score}) {r.description}")
