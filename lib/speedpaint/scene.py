#!/usr/bin/env python3
"""Speed-paint HyperFrames scene generator (sequential sketch + coloring-book fill).

SKETCH: SVG stroke paths drawn STRICTLY one-at-a-time; durations normalized so
        the whole sketch finishes by sketch_secs (then a GAP) BEFORE color starts.
COLOR:  a <canvas> reveals the color image per a precomputed ORDER MAP
        (segment.py): one whole coloring-book cell fills at a time, center-out,
        strictly sequential.
FINAL:  HARD RULE — NO camera/effects during sketch or color. The frame is locked
        until COLOR_END; the camera push + ambient life play ONLY during the hold.

Public API: build_scene(...) writes index.html and returns total duration (s).
"""
import argparse
import os
import xml.etree.ElementTree as ET

SVGNS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVGNS)

# Sleep preset: night-designed source art reveals TRUE-to-source; the ONLY change
# is a dark blackboard canvas + pale chalk ink for the sketch (no grade/tint/vignette).
SLEEP_PAPER = "#0E1320"
SLEEP_INK = "#aab6cc"
NORMAL_PAPER = "#F7F1E6"
NORMAL_INK = "#3a3631"


def sketch_inner(svg):
    root = ET.parse(svg).getroot()
    vb = root.get("viewBox") or f"0 0 {root.get('width')} {root.get('height')}"
    out = []
    for i, p in enumerate(root.findall(f".//{{{SVGNS}}}path")):
        d = p.get("d")
        if d:
            out.append(f'<path class="stroke" id="s{i}" d="{d}" />')
    return vb, "\n".join(out)


HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8" /><title>%%TITLE%%</title>
<style>
  body { margin: 0; background: #0e0e12; }
  #scene { position: relative; width: %%OUTW%%px; height: %%OUTH%%px; overflow: hidden; background: %%PAPER%%; }
  #sketch, #paint { position: absolute; inset: 0; width: %%OUTW%%px; height: %%OUTH%%px; }
  #paint { filter: %%CANVASFILTER%%; }
  .stroke { fill: none; stroke: %%INK%%; stroke-width: %%STROKE%%; stroke-linejoin: round; stroke-linecap: round; }
  #tint { position: absolute; inset: 0; pointer-events: none; background: %%TINT%%; opacity: %%TINTOP%%; mix-blend-mode: multiply; }
  #vignette { position: absolute; inset: 0; pointer-events: none;
              background: radial-gradient(ellipse 80% 78% at 50% 46%, rgba(0,0,0,0) 40%, rgba(0,0,0,%%VIGNETTE%%) 100%); }
  #camera { position: absolute; inset: 0; width: %%OUTW%%px; height: %%OUTH%%px; transform-origin: %%FXPCT%% %%FYPCT%%; will-change: transform; }
  #fxlayer { position: absolute; inset: 0; width: %%OUTW%%px; height: %%OUTH%%px; pointer-events: none; }
  #glow { position: absolute; inset: 0; pointer-events: none; opacity: 0; mix-blend-mode: screen;
          background: radial-gradient(ellipse 52% 48% at %%FXPCT%% %%FYPCT%%, rgba(176,198,236,0.20), rgba(176,198,236,0) 70%); }
</style></head>
<body>
<div id="scene" data-composition-id="%%COMP%%" data-start="0" data-duration="%%DUR%%"
     data-width="%%OUTW%%" data-height="%%OUTH%%">
  <div id="camera">
    <svg id="sketch" class="clip" data-start="0" data-duration="%%DUR%%" data-track-index="0"
         viewBox="0 0 %%VBW%% %%VBH%%" preserveAspectRatio="xMidYMid slice"
         xmlns="http://www.w3.org/2000/svg">
%%SKETCH_PATHS%%
    </svg>
    <canvas id="paint" class="clip" data-start="0" data-duration="%%DUR%%" data-track-index="1"
            width="%%CW%%" height="%%CH%%"></canvas>
    <svg id="fxlayer" viewBox="0 0 %%OUTW%% %%OUTH%%" xmlns="http://www.w3.org/2000/svg"></svg>
    <div id="glow"></div>
  </div>
  <div id="tint"></div>
  <div id="vignette"></div>
</div>

<img id="colorImg" src="%%COLOR%%" style="display:none" crossorigin="anonymous" />
<img id="orderImg" src="%%ORDER%%" style="display:none" crossorigin="anonymous" />

<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {};
  const CW = %%CW%%, CH = %%CH%%, N = CW * CH;
  const SKETCH_SECS = %%SKETCH_SECS%%, GAP = %%GAP%%, PAINT_SECS = %%PAINT_SECS%%;
  const COLOR_AT = SKETCH_SECS + GAP;
  const NS = "http://www.w3.org/2000/svg";
  // seeded PRNG (mulberry32) so particle layout is identical across render workers
  function rng(seed) { let a = seed >>> 0; return function () {
    a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  // ---------- color reveal (coloring-book order map) ----------
  const cvs = document.getElementById('paint'), ctx = cvs.getContext('2d', { willReadFrequently: true });
  const colorImg = document.getElementById('colorImg'), orderImg = document.getElementById('orderImg');
  let ready = false, out, sortedIdx, orderArr, ptr = 0, curThr = -1, pendingP = 0;

  function setup() {
    const oc = document.createElement('canvas'); oc.width = CW; oc.height = CH;
    const o = oc.getContext('2d', { willReadFrequently: true });
    o.drawImage(colorImg, 0, 0, CW, CH);
    const cd = o.getImageData(0, 0, CW, CH).data;
    o.clearRect(0, 0, CW, CH); o.drawImage(orderImg, 0, 0, CW, CH);
    const od = o.getImageData(0, 0, CW, CH).data;
    orderArr = new Uint8Array(N);
    for (let i = 0; i < N; i++) orderArr[i] = od[i*4];      // R channel = reveal time
    const counts = new Uint32Array(256);
    for (let i = 0; i < N; i++) counts[orderArr[i]]++;
    const pos = new Uint32Array(256); let acc = 0;
    for (let v = 0; v < 256; v++) { pos[v] = acc; acc += counts[v]; }
    sortedIdx = new Uint32Array(N);
    const cur = pos.slice();
    for (let i = 0; i < N; i++) { const v = orderArr[i]; sortedIdx[cur[v]++] = i; }
    out = ctx.createImageData(CW, CH);
    out.data.set(cd);
    for (let i = 0; i < N; i++) out.data[i*4+3] = 0;        // start fully hidden
    ready = true; reveal(pendingP);
  }
  function reveal(p) {
    if (!ready) { pendingP = p; return; }
    const thr = Math.round(p * 255);
    if (thr >= curThr) {
      while (ptr < N && orderArr[sortedIdx[ptr]] <= thr) { out.data[sortedIdx[ptr]*4+3] = 255; ptr++; }
    } else {
      while (ptr > 0 && orderArr[sortedIdx[ptr-1]] > thr) { ptr--; out.data[sortedIdx[ptr]*4+3] = 0; }
    }
    curThr = thr; ctx.putImageData(out, 0, 0);
  }
  let loaded = 0; const onload = () => { if (++loaded === 2) setup(); };
  if (colorImg.complete && orderImg.complete) setup();
  else { colorImg.onload = onload; orderImg.onload = onload; }

  // ---------- sketch: strictly sequential strokes ----------
  const strokes = Array.from(document.querySelectorAll('#sketch path'));
  const sinfo = strokes.map(p => {
    let len = 0; try { len = p.getTotalLength(); } catch(e) {}
    const b = p.getBBox();
    return { p, len, cx: b.x+b.width/2, cy: b.y+b.height/2 };
  });
  sinfo.sort((a,b) => (Math.floor(a.cy/120) - Math.floor(b.cy/120)) || (a.cx - b.cx));
  const tl = gsap.timeline({ paused: true });
  let raw = sinfo.map(o => Math.max(o.len, 6));
  const tot = raw.reduce((a,b)=>a+b, 0) || 1;
  let cursor = 0;
  sinfo.forEach((o, i) => {
    o.p.style.strokeDasharray = o.len || 1;
    o.p.style.strokeDashoffset = o.len || 1;
    const dur = raw[i] / tot * SKETCH_SECS;                 // sum == SKETCH_SECS exactly
    tl.to(o.p, { strokeDashoffset: 0, duration: dur, ease: "none" }, cursor);
    cursor += dur;                                          // sequential
  });

  // ---------- camera move + ambient life — STRICTLY on the finished still ----------
  // HARD RULE: NO camera movement or effects while sketching or coloring. The
  // frame is locked until COLOR_END; everything below begins only once the final
  // image is fully painted, during the hold.
  const TOTAL = %%DUR%%, HOLD = %%HOLD%%, ZOOM = %%ZOOM%%, NPART = %%NPART%%, LIFE = %%LIFE%%;
  const OW = %%OUTW%%, OH = %%OUTH%%, COLOR_END = COLOR_AT + PAINT_SECS;
  tl.to({}, { duration: TOTAL }, 0);                  // anchor timeline length to full duration
  gsap.set('#camera', { scale: 1 });                  // locked still through sketch + color
  if (HOLD > 0.3) {
    tl.fromTo('#camera', { scale: 1 }, { scale: ZOOM, duration: HOLD, ease: "power1.inOut" }, COLOR_END);
    if (LIFE) {
      const fadeIn = Math.min(0.9, HOLD * 0.35);
      tl.fromTo('#glow', { opacity: 0 }, { opacity: 0.85, duration: fadeIn, ease: "sine.in" }, COLOR_END);
      tl.to('#glow', { opacity: 1.0, duration: 1.7, repeat: Math.max(0, Math.floor(HOLD / 1.7)), yoyo: true, ease: "sine.inOut" }, COLOR_END + fadeIn);
      const prng = rng(424242), fx = document.getElementById('fxlayer');
      for (let i = 0; i < NPART; i++) {
        const c = document.createElementNS(NS, 'circle');
        const x = prng() * OW, y = prng() * OH;
        c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 1.3 + prng() * 3.0);
        c.setAttribute('fill', '%%MOTE%%'); c.style.opacity = 0;
        fx.appendChild(c);
        tl.fromTo(c, { attr: { cy: y } }, { attr: { cy: y - (10 + prng() * 40) }, duration: HOLD, ease: "none" }, COLOR_END);
        const tw = 1.4 + prng() * 1.8;
        tl.fromTo(c, { opacity: 0 }, { opacity: 0.07 + prng() * 0.12, duration: tw,
                   repeat: Math.max(0, Math.floor(HOLD / tw)), yoyo: true, ease: "sine.inOut" }, COLOR_END + prng() * Math.min(tw, HOLD * 0.3));
      }
    }
  }

  // Drive the canvas reveal from the timeline clock so EVERY seeked frame is
  // correct — including the hold and frames rendered by parallel workers that
  // seek straight past the color phase (a per-tween onUpdate would miss those).
  tl.eventCallback("onUpdate", () => {
    const p = Math.min(1, Math.max(0, (tl.time() - COLOR_AT) / PAINT_SECS));
    reveal(p);
  });

  window.__timelines["%%COMP%%"] = tl;
</script>
</body></html>
"""


def build_scene(sketch_svg, color, order, out, *, title="Speed Paint", comp="speedpaint",
                out_w=1920, out_h=1080, canvas_w=1920, canvas_h=1080,
                sketch_secs=5.0, gap=0.4, paint_secs=5.0, hold_secs=3.0,
                mode="normal", paper=None, ink=None, stroke=1.5,
                canvas_filter="none", tint="none", tint_opacity=0.0, vignette=0.0,
                focus_x=0.5, focus_y=0.42, zoom=1.08, particles=16, mote="#cdd6e6", life=True):
    """Write a HyperFrames speed-paint index.html. Returns total duration (seconds)."""
    if mode == "sleep":
        if paper is None: paper = SLEEP_PAPER
        if ink is None: ink = SLEEP_INK
    if paper is None: paper = NORMAL_PAPER
    if ink is None: ink = NORMAL_INK
    if not life:
        particles, zoom = 0, 1.0

    total = sketch_secs + gap + paint_secs + hold_secs
    vb, sketch_paths = sketch_inner(sketch_svg)
    vbw, vbh = vb.split()[2], vb.split()[3]
    out_dir = os.path.dirname(out) or "."
    color_rel = os.path.relpath(color, out_dir)
    order_rel = os.path.relpath(order, out_dir)
    repl = {
        "%%TITLE%%": title, "%%COMP%%": comp,
        "%%OUTW%%": str(out_w), "%%OUTH%%": str(out_h),
        "%%VBW%%": str(vbw), "%%VBH%%": str(vbh),
        "%%CW%%": str(canvas_w), "%%CH%%": str(canvas_h),
        "%%DUR%%": str(total),
        "%%SKETCH_SECS%%": str(sketch_secs), "%%GAP%%": str(gap), "%%PAINT_SECS%%": str(paint_secs),
        "%%HOLD%%": str(hold_secs), "%%ZOOM%%": str(zoom), "%%NPART%%": str(particles),
        "%%LIFE%%": ("true" if life else "false"), "%%MOTE%%": mote,
        "%%FXPCT%%": f"{focus_x*100:.1f}%", "%%FYPCT%%": f"{focus_y*100:.1f}%",
        "%%PAPER%%": paper, "%%INK%%": ink, "%%STROKE%%": str(stroke),
        "%%COLOR%%": color_rel, "%%ORDER%%": order_rel,
        "%%SKETCH_PATHS%%": sketch_paths,
        "%%CANVASFILTER%%": canvas_filter,
        "%%TINT%%": (tint if tint != "none" else "transparent"),
        "%%TINTOP%%": str(tint_opacity if tint != "none" else 0.0),
        "%%VIGNETTE%%": str(vignette),
    }
    html = HTML
    for k, v in repl.items():
        html = html.replace(k, v)
    os.makedirs(out_dir, exist_ok=True)
    with open(out, "w") as f:
        f.write(html)
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sketch-svg", required=True)
    ap.add_argument("--color", required=True)
    ap.add_argument("--order", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="normal", choices=["normal", "sleep"])
    ap.add_argument("--sketch-secs", type=float, default=5.0)
    ap.add_argument("--paint-secs", type=float, default=5.0)
    ap.add_argument("--hold-secs", type=float, default=3.0)
    ap.add_argument("--focus-x", type=float, default=0.5)
    ap.add_argument("--focus-y", type=float, default=0.42)
    ap.add_argument("--zoom", type=float, default=1.08)
    ap.add_argument("--particles", type=int, default=16)
    ap.add_argument("--stroke", type=float, default=1.5)
    ap.add_argument("--no-life", dest="life", action="store_false", default=True)
    a = ap.parse_args()
    total = build_scene(a.sketch_svg, a.color, a.order, a.out, mode=a.mode,
                        sketch_secs=a.sketch_secs, paint_secs=a.paint_secs, hold_secs=a.hold_secs,
                        focus_x=a.focus_x, focus_y=a.focus_y, zoom=a.zoom, particles=a.particles,
                        stroke=a.stroke, life=a.life)
    print(f"wrote {a.out} | dur={total}s")
