"""threejs_diorama — the AHM 3D ("medium_diorama" hero) render tier.

Renders a Three.js / WebGL scene (recognizable procedural 3D models on the video
THEME's basemap, with lighting + shadows) to a 1080p MP4. This is the engine
behind the Garrett-barn / Booth-leap class of shots — the "different process"
that yields recognizable 3D forms, replacing the flat CSS-3D `diorama.py` for
hero 3D beats.

Pipeline (proven on this 8GB machine via projects/threejs-car-test):
  scene .html (exposes window.__SCENE__ = {renderFrame(i), totalFrames, fps,
  width, height})  ->  OFF-SCREEN non-headless Chrome (real GPU WebGL; pure
  headless WebGL is unreliable)  ->  deterministic per-frame toDataURL capture
  ->  ffmpeg stitch  ->  MP4.

LOCKED conventions (see memory ahm_3d_diorama_threejs):
  * Ground plane = the THEME's basemap as a CanvasTexture (geo-accurate when the
    real basemap PNG is passed) — NOT a hardcoded parchment.
  * Lighting is theme/era-appropriate; night scenes still must READ (self-QA
    loop catches "too dark"). Tone-map + expose so forms are visible.
  * Every LIVING creature must have idle motion (bob / sway / head / occasional
    neigh-or-gesture). Static living figures are a QA fail (qa_creature_animation).
  * Render via this module — never hand-roll a parallel capture script in a
    project dir (Rule Zero).

A scene HTML is authored per-shot (like the HyperFrames shots, but Three.js).
`SCENE_CONTRACT` documents the window.__SCENE__ interface the HTML must expose.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# puppeteer is installed in the threejs proof project; allow override via env.
DEFAULT_NODE_MODULES = REPO_ROOT / "projects" / "threejs-car-test" / "node_modules"

SCENE_CONTRACT = """\
The scene .html MUST expose, after WebGL setup completes:
  window.__SCENE__ = {
    fps: <int>, totalFrames: <int>, width: <int>, height: <int>,
    renderFrame(i):  // DETERMINISTIC — set all animation state from t=i/fps and
                     // call renderer.render(scene, camera). No wall-clock.
  };
  // guard live preview with: if (!window.__HEADLESS__) requestAnimationFrame(loop);
Recommended renderer flags: WebGLRenderer({antialias:true, preserveDrawingBuffer:true}),
shadowMap.enabled = true. The capture sets window.__HEADLESS__ = true."""

# The capture harness (off-screen WebGL → per-frame PNG). Written next to the
# scene at render time so puppeteer resolves from node_modules.
_CAPTURE_JS = r"""
const puppeteer = require('puppeteer');
const path = require('path'); const fs = require('fs');
const HTML = 'file://' + process.argv[2];
const FRAMES = process.argv[3];
(async () => {
  if (!fs.existsSync(FRAMES)) fs.mkdirSync(FRAMES, { recursive: true });
  for (const f of fs.readdirSync(FRAMES)) if (f.endsWith('.png')) fs.unlinkSync(path.join(FRAMES, f));
  const browser = await puppeteer.launch({ headless: false, args: [
    '--window-position=10000,10000', '--window-size=1320,820',
    '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox' ] });
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('[err]', m.text()); });
  await page.evaluateOnNewDocument(() => { window.__HEADLESS__ = true; });
  await page.goto(HTML, { waitUntil: 'networkidle0' });
  await page.waitForFunction(
    () => window.__SCENE__ && typeof window.__SCENE__.renderFrame === 'function', { timeout: 30000 });
  const meta = await page.evaluate(() => ({ totalFrames: __SCENE__.totalFrames,
    fps: __SCENE__.fps, width: __SCENE__.width, height: __SCENE__.height }));
  await page.setViewport({ width: meta.width, height: meta.height, deviceScaleFactor: 1 });
  console.log('META ' + JSON.stringify(meta));
  for (let i = 0; i < meta.totalFrames; i++) {
    await page.evaluate(f => __SCENE__.renderFrame(f), i);
    const url = await page.evaluate(() => document.querySelector('canvas').toDataURL('image/png'));
    fs.writeFileSync(path.join(FRAMES, 'f_' + String(i).padStart(5, '0') + '.png'),
      Buffer.from(url.split(',')[1], 'base64'));
    if (i % 24 === 0) console.log('frame ' + i + '/' + meta.totalFrames);
  }
  await browser.close(); console.log('DONE ' + meta.totalFrames);
})().catch(e => { console.error(e); process.exit(1); });
"""


def _resolve_node_modules(node_modules: str | os.PathLike | None) -> Path:
    nm = Path(node_modules) if node_modules else Path(
        os.environ.get("AHM_NODE_MODULES", DEFAULT_NODE_MODULES))
    if not (nm / "puppeteer").exists():
        raise RuntimeError(
            f"puppeteer not found at {nm}. Install it (npm i puppeteer) or set "
            f"AHM_NODE_MODULES / pass node_modules=.")
    return nm


def render_diorama(scene_html: str | os.PathLike, out_mp4: str | os.PathLike, *,
                   fps: int = 24, crf: int = 18, node_modules=None,
                   keep_frames: bool = False) -> dict:
    """Render a Three.js scene HTML to MP4. Returns capture metadata.

    The scene's own __SCENE__.fps drives frame timing; `fps` here is the encode
    rate (kept equal by default).
    """
    scene_html = Path(scene_html).resolve()
    out_mp4 = Path(out_mp4).resolve()
    if not scene_html.exists():
        raise FileNotFoundError(scene_html)
    nm = _resolve_node_modules(node_modules)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="ahm3d_"))
    frames = work / "frames"
    cap_js = work / "_capture.js"
    cap_js.write_text(_CAPTURE_JS)
    try:
        env = {**os.environ, "NODE_PATH": str(nm)}
        proc = subprocess.run(
            ["node", str(cap_js), str(scene_html), str(frames)],
            env=env, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            raise RuntimeError(f"capture failed:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        meta = {}
        for line in proc.stdout.splitlines():
            if line.startswith("META "):
                meta = json.loads(line[5:])
        n = len(list(frames.glob("f_*.png")))
        if n == 0:
            raise RuntimeError("capture produced 0 frames (WebGL likely failed)")
        scene_fps = meta.get("fps", fps)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(scene_fps),
             "-i", str(frames / "f_%05d.png"), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-crf", str(crf), str(out_mp4)],
            check=True)
        meta["frames"] = n
        meta["out"] = str(out_mp4)
        return meta
    finally:
        if not keep_frames:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Render a Three.js diorama scene to MP4.")
    ap.add_argument("scene_html")
    ap.add_argument("out_mp4")
    ap.add_argument("--node-modules", default=None)
    args = ap.parse_args()
    info = render_diorama(args.scene_html, args.out_mp4, node_modules=args.node_modules)
    print(json.dumps(info, indent=2))
