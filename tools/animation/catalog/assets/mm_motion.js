// Midnight Magnates motion primitives — shared across all 99 animation formats.
//
// Conventions:
//  - All primitives accept (tl, opts) where tl is a paused GSAP timeline.
//  - Every primitive supports `start` (default 0) and `duration` (default scene duration - 1).
//  - All eases are sleep-safe: sine.inOut / power1.inOut / power2.out only (no elastic / back / bounce).
//  - `repeat: -1` is BANNED — every yoyo computes finite Math.ceil((D - start) / cycle) * 2.

window.MM = (function () {
  const log = (...a) => { /* console.log("[mm]", ...a); */ };

  // --- 1. Starfield twinkle ---
  // Expects an SVG with id `selector` containing <circle class="star"/> and <circle class="star-bright"/>.
  function starfield(tl, opts = {}) {
    const sel = opts.selector || "#starfield";
    const start = opts.start ?? 0.2;
    const D = opts.duration ?? 5.0;
    tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 1.4, ease: "sine.out" }, start);
    const cycle = 1.0;
    const reps = Math.max(2, Math.ceil((D - 1.4) / cycle) * 2);
    tl.to(sel, { opacity: 0.65, duration: cycle, yoyo: true, repeat: reps, ease: "sine.inOut", overwrite: "auto" }, start + 1.3);
  }

  // --- 2. Comet pass ---
  // Expects an SVG with id `selector` containing <path id="comet-trail"> + <circle id="comet-dot">.
  function cometPass(tl, opts = {}) {
    const trail = opts.trail || "#comet-trail";
    const dot = opts.dot || "#comet-dot";
    const start = opts.start ?? 1.4;
    const dur = opts.duration ?? 2.0;
    const endX = opts.endX ?? 2000;
    const endY = opts.endY ?? 460;
    tl.fromTo(trail, { strokeDashoffset: 800 }, { strokeDashoffset: -200, duration: dur, ease: "sine.out" }, start);
    tl.fromTo(dot, { cx: -50, cy: -50 }, { cx: endX, cy: endY, duration: dur, ease: "sine.out" }, start);
    tl.to(trail, { opacity: 0, duration: 0.5, ease: "sine.in" }, start + dur - 0.4);
    tl.to(dot, { opacity: 0, duration: 0.4, ease: "sine.in" }, start + dur - 0.3);
  }

  // --- 3. Window-glow breathe ---
  // Expects elements matching `selector` (e.g., ".glow"). Each gets staggered fade-in + breath cycle.
  function glowBreathe(tl, opts = {}) {
    const sel = opts.selector || ".glow";
    const start = opts.start ?? 0.4;
    const D = opts.duration ?? 5.0;
    const peak = opts.peak ?? 0.8;
    const trough = opts.trough ?? 0.35;
    document.querySelectorAll(sel).forEach((el, i) => {
      const stagger = start + i * 0.12;
      tl.fromTo(el, { opacity: 0 }, { opacity: peak, duration: 0.9, ease: "sine.out" }, stagger);
      const cycle = 1.0 + (i % 3) * 0.15;
      const reps = Math.max(2, Math.ceil((D - stagger - 0.9) / cycle) * 2);
      tl.to(el, { opacity: trough, duration: cycle, yoyo: true, repeat: reps, ease: "sine.inOut", overwrite: "auto" }, stagger + 0.9);
    });
  }

  // --- 4. Particle drift (fireflies / dust / smoke motes) ---
  // Expects elements matching `selector` (e.g., ".firefly"). Each drifts on a deterministic offset.
  function particleDrift(tl, opts = {}) {
    const sel = opts.selector || ".firefly";
    const start = opts.start ?? 0.5;
    const D = opts.duration ?? 5.5;
    const targetOpacity = opts.opacity ?? 0.85;
    const spread = opts.spread ?? 28;
    const els = document.querySelectorAll(sel);
    els.forEach((el, i) => {
      // mulberry32-ish: a tiny seeded pattern per index
      const s = (i * 7919) | 0;
      const ang = ((s * 0.0001) % 1) * Math.PI * 2;
      const dx = Math.cos(ang) * spread;
      const dy = Math.sin(ang) * spread * 0.6;
      const s0 = start + i * 0.18;
      tl.fromTo(el, { opacity: 0, scale: 0.4 },
        { opacity: targetOpacity, scale: 1, duration: 0.6, ease: "sine.out" }, s0);
      const cycle = 2.4 + (i % 3) * 0.35;
      const reps = Math.max(2, Math.ceil((D - s0 - 0.6) / cycle) * 2);
      tl.to(el, {
        x: `+=${dx}`, y: `+=${dy}`, opacity: targetOpacity * 0.45,
        duration: cycle, yoyo: true, repeat: reps, ease: "sine.inOut", overwrite: "auto",
      }, s0 + 0.6);
    });
  }

  // --- 5. Title burn-in (Playfair headline + subtitle) ---
  function titleBurn(tl, opts = {}) {
    const title = opts.title || "#title";
    const subtitle = opts.subtitle || "#subtitle";
    const start = opts.start ?? 1.4;
    tl.fromTo(title, { opacity: 0, y: -14, filter: "blur(8px)" },
      { opacity: 0.95, y: 0, filter: "blur(0px)", duration: 1.2, ease: "sine.out" }, start);
    if (document.querySelector(subtitle)) {
      tl.fromTo(subtitle, { opacity: 0, y: -6 },
        { opacity: 0.85, y: 0, duration: 1.0, ease: "sine.out" }, start + 0.6);
    }
  }

  // --- 6. Type-in (typewriter) ---
  // Animates width: 0 -> 100% on `selector`, ideally a span with `overflow:hidden; white-space:nowrap`.
  function typeIn(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.6;
    const dur = opts.duration ?? 1.4;
    tl.fromTo(sel, { width: 0 }, { width: "100%", duration: dur, ease: "none" }, start);
  }

  // --- 7. Slam-in (overshoot via power2.out, NOT elastic) ---
  function slamIn(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.2;
    const fromScale = opts.fromScale ?? 1.5;
    const fromY = opts.fromY ?? -40;
    const dur = opts.duration ?? 0.55;
    tl.fromTo(sel,
      { opacity: 0, scale: fromScale, y: fromY, rotation: opts.fromRotate ?? 0 },
      { opacity: 1, scale: 1, y: 0, rotation: 0, duration: dur, ease: "power2.out" },
      start
    );
    // Settle micro-bounce — finite, sleep-safe
    tl.to(sel, { scale: 1.02, duration: 0.18, yoyo: true, repeat: 1, ease: "sine.inOut" }, start + dur);
  }

  // --- 8. Pan (horizontal) ---
  // Pans `selector` from initialX -> targetX over duration. Used by panorama/timeline formats.
  function panX(tl, opts = {}) {
    const sel = opts.selector || "#pan-img";
    const x0 = opts.x0 ?? 0;
    const x1 = opts.x1 ?? -800;
    const start = opts.start ?? 0.4;
    const dur = opts.duration ?? 6.0;
    tl.fromTo(sel, { x: x0 }, { x: x1, duration: dur, ease: "sine.inOut" }, start);
  }
  // Pan vertical
  function panY(tl, opts = {}) {
    const sel = opts.selector || "#pan-img";
    const y0 = opts.y0 ?? 0;
    const y1 = opts.y1 ?? -800;
    const start = opts.start ?? 0.4;
    const dur = opts.duration ?? 6.0;
    tl.fromTo(sel, { y: y0 }, { y: y1, duration: dur, ease: "sine.inOut" }, start);
  }

  // --- 9. Parallax layers ---
  // Expects parallax layers with class `.layer-d` plus a data-depth attr 0..1.
  function parallaxPush(tl, opts = {}) {
    const sel = opts.selector || ".layer-d";
    const start = opts.start ?? 0.0;
    const D = opts.duration ?? 6.0;
    document.querySelectorAll(sel).forEach((el) => {
      const depth = parseFloat(el.dataset.depth || "0.5");
      const dx = (opts.dx ?? -40) * (1 - depth);
      const dy = (opts.dy ?? 0) * (1 - depth);
      const scaleEnd = 1 + (opts.zoom ?? 0.08) * (1 - depth);
      tl.fromTo(el, { x: 0, y: 0, scale: 1 }, { x: dx, y: dy, scale: scaleEnd, duration: D, ease: "sine.inOut" }, start);
    });
  }

  // --- 10. Card flip — flip an element from back to front around Y axis ---
  function cardFlip(tl, opts = {}) {
    const back = opts.back;
    const front = opts.front;
    const start = opts.start ?? 0.4;
    const dur = opts.duration ?? 0.9;
    if (back) {
      tl.fromTo(back, { rotationY: 0, opacity: 1 }, { rotationY: 90, opacity: 0.3, duration: dur / 2, ease: "sine.in" }, start);
    }
    tl.fromTo(front, { rotationY: -90, opacity: 0 }, { rotationY: 0, opacity: 1, duration: dur / 2, ease: "sine.out" }, start + dur / 2);
  }

  // --- 11. SVG path draw (DrawSVG-style via stroke-dasharray fallback) ---
  function pathDraw(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.4;
    const dur = opts.duration ?? 1.8;
    // Compute total length once; subsequent renders cache via dataset.
    const el = document.querySelector(sel);
    if (!el || !el.getTotalLength) return;
    const len = el.dataset.pathLen ? parseFloat(el.dataset.pathLen) : el.getTotalLength();
    el.dataset.pathLen = len;
    el.style.strokeDasharray = `${len}`;
    el.style.strokeDashoffset = `${len}`;
    tl.fromTo(sel, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: dur, ease: "sine.inOut" }, start);
  }

  // --- 12. Ken-Burns drift on hero image ---
  function kenBurns(tl, opts = {}) {
    const sel = opts.selector || "#hero";
    const start = opts.start ?? 0.0;
    const D = opts.duration ?? 6.0;
    const scaleEnd = opts.scaleEnd ?? 1.04;
    const dx = opts.dx ?? -20;
    const dy = opts.dy ?? -8;
    tl.fromTo(sel, { scale: 1.0, x: 0, y: 0 }, { scale: scaleEnd, x: dx, y: dy, duration: D, ease: "sine.inOut" }, start);
  }

  // --- 13. Beat flash (every N seconds, the scene brightens) ---
  function beatFlash(tl, opts = {}) {
    const sel = opts.selector || "#root";
    const start = opts.start ?? 0.0;
    const D = opts.duration ?? 6.0;
    const bpm = opts.bpm ?? 110;
    const beatLen = 60 / bpm;
    const peak = opts.peak ?? 1.15;
    const beats = Math.floor(D / beatLen);
    for (let i = 0; i < beats; i++) {
      tl.to(sel, { filter: `brightness(${peak})`, duration: 0.08, ease: "power2.out" }, start + i * beatLen);
      tl.to(sel, { filter: `brightness(1.0)`, duration: beatLen - 0.08, ease: "sine.inOut" }, start + i * beatLen + 0.08);
    }
  }

  // --- 14. Count-up number ---
  // Updates textContent on `selector` from `from` to `to` over `dur`.
  function countUp(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.4;
    const dur = opts.duration ?? 1.8;
    const from = opts.from ?? 0;
    const to = opts.to ?? 100;
    const prefix = opts.prefix ?? "";
    const suffix = opts.suffix ?? "";
    const obj = { v: from };
    const el = document.querySelector(sel);
    if (!el) return;
    tl.to(obj, {
      v: to, duration: dur, ease: "sine.out",
      onUpdate: () => { el.textContent = prefix + Math.round(obj.v) + suffix; },
    }, start);
  }

  // --- 15. Stamp slam (rotate-in stamp with overshoot then settle) ---
  function stampSlam(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.8;
    const dur = opts.duration ?? 0.5;
    const fromAngle = opts.fromAngle ?? -28;
    const toAngle = opts.toAngle ?? -12;
    tl.fromTo(sel,
      { opacity: 0, scale: 1.8, rotation: fromAngle },
      { opacity: 1, scale: 1.0, rotation: toAngle, duration: dur, ease: "power2.out" },
      start
    );
  }

  // --- 16. Highlight sweep (gold underline that draws across text) ---
  function highlightSweep(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 1.0;
    const dur = opts.duration ?? 0.9;
    tl.fromTo(sel, { scaleX: 0, transformOrigin: "left center" },
      { scaleX: 1, duration: dur, ease: "sine.inOut" }, start);
  }

  // --- 17. Scene fade in/out (universal at root) ---
  function sceneFade(tl, opts = {}) {
    const D = opts.duration ?? 6.0;
    tl.fromTo("#root", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "sine.out" }, 0);
    tl.to("#root", { opacity: 0, duration: 0.5, ease: "sine.in" }, D - 0.5);
  }

  // --- 18. Ink bleed (text ink-darkens via filter or opacity) ---
  function inkBleed(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.6;
    const dur = opts.duration ?? 0.8;
    tl.fromTo(sel, { opacity: 0.0, filter: "blur(4px)" },
      { opacity: 1.0, filter: "blur(0px)", duration: dur, ease: "sine.out" }, start);
  }

  // --- 19. Bar fill (HP/MP style horizontal fill) ---
  function barFill(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.5;
    const dur = opts.duration ?? 1.0;
    tl.fromTo(sel, { scaleX: 0, transformOrigin: "left center" },
      { scaleX: 1, duration: dur, ease: "sine.out" }, start);
  }

  // --- 20. Spin (slow rotation, finite repeats) ---
  function spinSlow(tl, opts = {}) {
    const sel = opts.selector;
    const start = opts.start ?? 0.0;
    const D = opts.duration ?? 6.0;
    const speed = opts.speed ?? 30;
    tl.to(sel, { rotation: speed * D, duration: D, ease: "none" }, start);
  }

  return {
    starfield, cometPass, glowBreathe, particleDrift, titleBurn, typeIn, slamIn,
    panX, panY, parallaxPush, cardFlip, pathDraw, kenBurns, beatFlash, countUp,
    stampSlam, highlightSweep, sceneFade, inkBleed, barFill, spinSlow,
  };
})();
