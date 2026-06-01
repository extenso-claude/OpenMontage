"""OpenTimelineIO editor handoff — human-triggered AFTER the final render.

Per the locked decision, the default deliverable is the rendered .mov/.mp4; only
when the human asks do we emit an editable timeline so an editor can tweak it in
DaVinci Resolve (imports .otio natively) or Premiere (via the FCP7 XML the OTIO
core adapter emits, which Premiere + Resolve both import).

The timeline references the REAL media on disk (a conform check then confirms
every clip resolves):
  * Video — per-chapter rendered clips (renders/chapters/*.mp4) if present, else
    the master as a single clip; chapter boundaries become timeline markers.
  * Audio — VO / Music / SFX stems on their own tracks if present.

CLI:  python -m lib.midnight_magnates.otio_export --project <dir> [--fps 24]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import opentimelineio as otio  # noqa: E402


class HandoffError(Exception):
    pass


def _ffprobe_duration(path: Path) -> Optional[float]:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, timeout=60)
        return float(out.stdout.strip())
    except Exception:
        return None


def _rt(seconds: float, fps: int) -> "otio.opentime.RationalTime":
    # Construct from frame count + rate — version-stable across otio releases.
    return otio.opentime.RationalTime(round(seconds * fps), fps)


def _tr(start_s: float, dur_s: float, fps: int) -> "otio.opentime.TimeRange":
    return otio.opentime.TimeRange(start_time=_rt(start_s, fps), duration=_rt(max(dur_s, 1.0 / fps), fps))


def _ext_ref(path: Path, dur_s: float, fps: int) -> "otio.schema.ExternalReference":
    return otio.schema.ExternalReference(
        target_url=str(path.resolve()),
        available_range=_tr(0.0, dur_s, fps),
    )


def _find(project_dir: Path, *rels: str) -> Optional[Path]:
    for r in rels:
        p = project_dir / r
        if p.is_file():
            return p
    return None


def _chapter_markers(project_dir: Path, fps: int) -> List[Tuple[float, str]]:
    """First-cue start time per chapter (from cuelist cue ids 'chNN_…')."""
    cl = project_dir / "artifacts" / "cuelist.json"
    if not cl.is_file():
        return []
    try:
        cues = json.loads(cl.read_text()).get("cues", [])
    except Exception:
        return []
    seen = {}
    for c in cues:
        m = re.match(r"(ch\d{2}_[a-z0-9_]+?)\.", str(c.get("id", "")))
        if not m:
            continue
        ch = m.group(1)
        st = c.get("start_s")
        if isinstance(st, (int, float)) and (ch not in seen or st < seen[ch]):
            seen[ch] = float(st)
    return sorted(((t, ch) for ch, t in seen.items()), key=lambda x: x[0])


def build_timeline(project_dir: Path, fps: int = 24) -> "otio.schema.Timeline":
    project_dir = Path(project_dir).resolve()
    master = _find(project_dir, "renders/master.mp4", "renders/final.mp4")
    chapter_clips = sorted((project_dir / "renders" / "chapters").glob("*.mp4")) \
        if (project_dir / "renders" / "chapters").is_dir() else []
    if not master and not chapter_clips:
        raise HandoffError("no rendered video found (renders/master.mp4|final.mp4 or renders/chapters/*.mp4)")

    tl = otio.schema.Timeline(name=project_dir.name)
    vtrack = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)

    if chapter_clips:
        for cp in chapter_clips:
            dur = _ffprobe_duration(cp) or 5.0
            vtrack.append(otio.schema.Clip(name=cp.stem, media_reference=_ext_ref(cp, dur, fps),
                                           source_range=_tr(0.0, dur, fps)))
    else:
        dur = _ffprobe_duration(master) or 1.0
        clip = otio.schema.Clip(name="master", media_reference=_ext_ref(master, dur, fps),
                                source_range=_tr(0.0, dur, fps))
        for t, ch in _chapter_markers(project_dir, fps):
            if t <= dur:
                clip.markers.append(otio.schema.Marker(
                    name=ch, color=otio.schema.MarkerColor.YELLOW,
                    marked_range=otio.opentime.TimeRange(
                        start_time=_rt(t, fps), duration=_rt(0.0, fps))))
        vtrack.append(clip)
    tl.tracks.append(vtrack)

    # Audio stems -> one track each (so the editor can re-balance / replace).
    stems = [("VO", ["artifacts/vo_full.wav", "artifacts/vo_full.mp3", "artifacts/voice/vo_full.wav"]),
             ("Music", ["artifacts/music_mix.wav", "assets/music/music_mix.wav"]),
             ("SFX", ["artifacts/sfx_mix.wav", "assets/sfx/sfx_mix.wav"])]
    for name, rels in stems:
        sp = _find(project_dir, *rels)
        if not sp:
            continue
        dur = _ffprobe_duration(sp) or (_ffprobe_duration(master) if master else None) or 1.0
        atrack = otio.schema.Track(name=name, kind=otio.schema.TrackKind.Audio)
        atrack.append(otio.schema.Clip(name=name, media_reference=_ext_ref(sp, dur, fps),
                                       source_range=_tr(0.0, dur, fps)))
        tl.tracks.append(atrack)
    return tl


def export(project_dir: Path, fps: int = 24) -> dict:
    project_dir = Path(project_dir).resolve()
    tl = build_timeline(project_dir, fps)
    out_dir = project_dir / "handoff"
    out_dir.mkdir(parents=True, exist_ok=True)
    otio_path = out_dir / (project_dir.name + ".otio")
    otio.adapters.write_to_file(tl, str(otio_path))

    written = {"otio": str(otio_path)}
    # FCP7 XML (Premiere + Resolve import it) if the adapter is available.
    if "fcp_xml" in set(otio.adapters.available_adapter_names()):
        try:
            xml_path = out_dir / (project_dir.name + ".xml")
            otio.adapters.write_to_file(tl, str(xml_path), adapter_name="fcp_xml")
            written["fcpxml"] = str(xml_path)
        except Exception as exc:  # adapter present but failed — report, don't crash
            written["fcpxml_error"] = str(exc)

    # Conform check: every clip's media must resolve on disk.
    missing = []
    for clip in tl.find_clips():
        ref = clip.media_reference
        url = getattr(ref, "target_url", None)
        if url and not Path(url).exists():
            missing.append(url)
    written["clips"] = len(list(tl.find_clips()))
    written["tracks"] = len(tl.tracks)
    written["unresolved_media"] = missing
    return written


def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="midnight_magnates.otio_export")
    ap.add_argument("--project", required=True)
    ap.add_argument("--fps", type=int, default=24)
    args = ap.parse_args(argv)
    try:
        res = export(Path(args.project), args.fps)
    except HandoffError as exc:
        print("HANDOFF FAILED: {0}".format(exc), file=sys.stderr)
        return 1
    print(json.dumps(res, indent=2))
    return 0 if not res.get("unresolved_media") else 1


if __name__ == "__main__":
    sys.exit(_main())
