"""Shared shot-HTML reader for the overlay-alignment gate family.

The A5/A6 gates (qa_chapter_ui, qa_duplicate_face, qa_pin_label_pulse_align) all
read the SAME thing the lead actually ships: the per-shot HyperFrames HTML under
``hyperframes/**/shots/*.html``, plus the declared coordinates the author writes
*in that file* (inline ``style`` + the id/class rules in the ``<style>`` block +
``data-*`` provenance). Keeping that parsing here means all three gates resolve
geometry identically (one bounded resolver, not three drifting copies) — the same
reason the I/O contract lives once in ``_contract``.

This is deliberately NOT a CSS layout engine. It reads the small, explicit set of
declared-pixel idioms these shots actually use:

  * absolute box:        left/top/width/height in px (inline style wins; else the
                         matching ``#id`` rule, else a matching ``.class`` rule);
  * centring transform:  ``transform: translate(-50%,-50%)`` re-anchors the box so
                         (left,top) is the CENTER, not the top-left;
  * teardrop pin:        ``border-radius:50% 50% 50% 0`` + ``rotate(45deg)`` — the
                         visible HEAD center is the box center; the pin TIP is the
                         bottom-point of the box (used by the alignment gate);
  * halo / ripple idiom: ``left:50%; top:50%`` + ``margin:-Hpx 0 0 -Wpx`` centres a
                         child on its parent's box center.

Everything is read off declared values in the file — no geographic re-projection,
no Mercator math, no parallel compositor. A gate that needs a value the file does
not declare must surface that (so it can FAIL loudly), never guess.

Public surface:
  iter_shot_html_files(project_dir) -> sorted list of Path (the shot HTMLs)
  parse_shot(path) -> ParsedShot
  ParsedShot.elements -> list[Element]
  Element: id, classes, text, style (dict), data (dict of data-*), src,
           background_url, css_rules (merged), and geometry helpers
           (box(), center(), tip_point()) returning shot-pixel coords or None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Only shots live in /shots/ ; the stitched chapter index.html is out of scope for
# these per-shot gates (the task names the /shots/ files specifically).
_SHOT_GLOB = "shots/*.html"

_PX_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*px")
_URL_RE = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.IGNORECASE)
_TRANSLATE_RE = re.compile(
    r"translate\(\s*(-?\d+(?:\.\d+)?)%\s*,\s*(-?\d+(?:\.\d+)?)%\s*\)", re.IGNORECASE
)
_ROTATE_RE = re.compile(r"rotate\(\s*(-?\d+(?:\.\d+)?)deg\s*\)", re.IGNORECASE)


def _length_tokens(raw: str) -> List[float]:
    """Parse a space-separated CSS length list ('-45px 0 0 -45px') into px floats.
    Each token is ``Npx`` (px stripped) or a bare ``0`` (unit-less zero, allowed by
    CSS). Tokens with other units are treated as 0 (these shots use px/0 only)."""
    out: List[float] = []
    for tok in raw.replace(",", " ").split():
        tok = tok.strip()
        if not tok:
            continue
        m = _PX_RE.fullmatch(tok)
        if m:
            out.append(float(m.group(1)))
        elif tok in ("0", "0px", "-0", "+0"):
            out.append(0.0)
        else:
            try:
                out.append(float(tok))  # bare number (rare) — treat as px
            except ValueError:
                out.append(0.0)
    return out


def iter_shot_html_files(project_dir: Path) -> List[Path]:
    """Every per-shot HTML under hyperframes/**/shots/, sorted for stable output."""
    hf = project_dir / "hyperframes"
    if not hf.is_dir():
        return []
    return sorted(hf.rglob(_SHOT_GLOB))


def _split_declarations(style_text: str) -> Dict[str, str]:
    """Parse a CSS declaration block ('a:1px; b:2px') into {prop: value}.

    Lower-cased property names; values kept verbatim (we need the raw px / url /
    transform text). Robust to a trailing ';' and to ':' inside url()/values by
    splitting each declaration only on its FIRST colon.
    """
    out: Dict[str, str] = {}
    for decl in style_text.split(";"):
        decl = decl.strip()
        if not decl or ":" not in decl:
            continue
        prop, _, val = decl.partition(":")
        prop = prop.strip().lower()
        val = val.strip()
        if prop:
            out[prop] = val
    return out


def _parse_style_block(css: str) -> List[Tuple[List[str], Dict[str, str]]]:
    """Parse a <style> block into [(selectors, declarations), ...].

    Comments are stripped first. Each rule's selector list is split on ',' and the
    declarations parsed with _split_declarations. At-rules / nested blocks are
    skipped defensively (these shots use flat rules only).
    """
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
    rules: List[Tuple[List[str], Dict[str, str]]] = []
    i = 0
    n = len(css)
    while i < n:
        brace = css.find("{", i)
        if brace == -1:
            break
        selector_text = css[i:brace].strip()
        close = css.find("}", brace + 1)
        if close == -1:
            break
        body = css[brace + 1:close]
        i = close + 1
        if not selector_text or selector_text.startswith("@"):
            continue
        selectors = [s.strip() for s in selector_text.split(",") if s.strip()]
        decls = _split_declarations(body)
        if selectors and decls:
            rules.append((selectors, decls))
    return rules


@dataclass
class Element:
    """One HTML element with its declared style/geometry resolved in shot pixels."""

    tag: str
    id: str = ""
    classes: List[str] = field(default_factory=list)
    style: Dict[str, str] = field(default_factory=dict)   # inline style
    data: Dict[str, str] = field(default_factory=dict)    # data-* attributes
    attrs: Dict[str, str] = field(default_factory=dict)   # all raw attributes (svg x1/x2/...)
    src: str = ""                                          # <img src>
    text: str = ""                                         # concatenated inner text
    css_rules: Dict[str, str] = field(default_factory=dict)  # merged from <style>
    parent: int = -1                                      # index of containing element, -1 = root
    index: int = -1                                       # this element's own index

    # ---- resolved declarations (inline overrides the <style> rule) ------------
    def decl(self, prop: str) -> Optional[str]:
        if prop in self.style:
            return self.style[prop]
        return self.css_rules.get(prop)

    def _px(self, prop: str) -> Optional[float]:
        raw = self.decl(prop)
        if raw is None:
            return None
        m = _PX_RE.search(raw)
        return float(m.group(1)) if m else None

    @property
    def background_url(self) -> Optional[str]:
        """The url(...) inside any background / background-image declaration."""
        for prop in ("background-image", "background"):
            raw = self.decl(prop)
            if raw:
                m = _URL_RE.search(raw)
                if m:
                    return m.group(1).strip()
        return None

    @property
    def transform(self) -> str:
        return self.decl("transform") or ""

    def _len(self, prop: str, parent_extent: Optional[float]) -> Optional[float]:
        """Resolve a left/top/width/height length to px. ``Npx`` -> N; a bare/unit
        ``0`` -> 0 (CSS allows unit-less zero); ``P%`` -> P/100 * parent_extent
        (only if the parent extent is known)."""
        raw = self.decl(prop)
        if raw is None:
            return None
        raw = raw.strip()
        if raw in ("0", "-0", "+0", "0px"):
            return 0.0
        if raw.endswith("%"):
            try:
                pct = float(raw[:-1].strip())
            except ValueError:
                return None
            if parent_extent is None:
                return None
            return pct / 100.0 * parent_extent
        m = _PX_RE.search(raw)
        return float(m.group(1)) if m else None

    def local_box(self, parent_w: Optional[float] = None,
                  parent_h: Optional[float] = None) -> Optional[Tuple[float, float, float, float]]:
        """The element's (left, top, width, height) in px RELATIVE TO its containing
        block's top-left, with margins and translate() folded in. ``%`` left/top are
        resolved against (parent_w, parent_h) when supplied.

        Returns None when the element is not a sized, positioned box we can resolve.
        """
        w = self._len("width", parent_w)
        h = self._len("height", parent_h)
        if w is None or h is None:
            return None
        left = self._len("left", parent_w)
        top = self._len("top", parent_h)
        if left is None or top is None:
            return None

        # Negative-margin centring idiom (left:50% + margin:-h/2 ...). Folded in
        # uniformly: margins shift the box whether left/top are px or %.
        left += self._margin("left")
        top += self._margin("top")

        # translate(dx%,dy%) re-anchors relative to the element's own size.
        m = _TRANSLATE_RE.search(self.transform)
        if m:
            left += float(m.group(1)) / 100.0 * w
            top += float(m.group(2)) / 100.0 * h
        return (left, top, w, h)

    def local_origin(self, parent_w: Optional[float] = None,
                     parent_h: Optional[float] = None) -> Optional[Tuple[float, float]]:
        """The element's (left, top) in px relative to its containing block — the
        position origin only, NO width/height required. Used for auto-sized boxes
        (labels) where we still need the top-left to place a child SVG. Margins and a
        px-translate are folded in; a %-translate needs the element's own size, so it
        is applied only when width/height are declared."""
        left = self._len("left", parent_w)
        top = self._len("top", parent_h)
        if left is None or top is None:
            return None
        left += self._margin("left")
        top += self._margin("top")
        m = _TRANSLATE_RE.search(self.transform)
        if m:
            w = self._len("width", parent_w)
            h = self._len("height", parent_h)
            if w is not None:
                left += float(m.group(1)) / 100.0 * w
            if h is not None:
                top += float(m.group(2)) / 100.0 * h
        return (left, top)

    def _margin(self, side: str) -> float:
        """Resolved margin for 'left' or 'top' in px (0 if undeclared).
        Honors margin-left/-top and the ``margin`` shorthand (1/2/3/4 values), where
        each token may be ``Npx`` or a bare ``0`` (CSS allows unit-less zero)."""
        direct = self._px("margin-" + side)
        if direct is not None:
            return direct
        raw = self.decl("margin")
        if not raw:
            return 0.0
        toks = _length_tokens(raw)
        if not toks:
            return 0.0
        # CSS shorthand expansion -> [top, right, bottom, left]
        if len(toks) == 1:
            t = r = b = l = toks[0]
        elif len(toks) == 2:
            t = b = toks[0]; r = l = toks[1]
        elif len(toks) == 3:
            t = toks[0]; r = l = toks[1]; b = toks[2]
        else:
            t, r, b, l = toks[0], toks[1], toks[2], toks[3]
        return t if side == "top" else l

    def is_teardrop(self) -> bool:
        """A brass/oxblood map pin: teardrop border-radius + a 45deg rotation."""
        br = self.decl("border-radius") or ""
        rounded_teardrop = "50% 50% 50% 0" in br
        rotated45 = "rotate(45deg)" in self.transform.replace(" ", "")
        return rounded_teardrop and rotated45

    def is_positioned(self) -> bool:
        """True if this element establishes a positioning context for absolute
        children (position: absolute | relative | fixed). #root and pin containers
        are positioned; a bare <div> wrapper is static and is skipped in the walk."""
        pos = (self.decl("position") or "").strip().lower()
        return pos in ("absolute", "relative", "fixed")


@dataclass
class ParsedShot:
    path: Path
    elements: List[Element]
    raw_html: str

    def by_id(self, el_id: str) -> Optional[Element]:
        for e in self.elements:
            if e.id == el_id:
                return e
        return None

    # ---- absolute (screen-space) geometry -----------------------------------
    # A child's left/top are relative to its nearest POSITIONED ancestor's
    # top-left (its containing block). We resolve a screen-absolute box by adding
    # that ancestor's own absolute top-left, recursively up to #root (which is
    # inset:0 at the frame origin). %-lengths resolve against the ancestor's size.
    def _ancestor(self, el: Element) -> Optional[Element]:
        """Nearest positioned ancestor, or None when we reach the root/#root.
        A static (non-positioned) wrapper is transparent: we keep walking up so a
        <div> with no position does not offset its children (matches CSS)."""
        idx = el.parent
        while idx >= 0:
            cand = self.elements[idx]
            if cand.is_positioned() or cand.id == "root":
                return cand
            idx = cand.parent
        return None

    def abs_box(self, el: Element) -> Optional[Tuple[float, float, float, float]]:
        """Screen-absolute (x, y, w, h) in 1920x1080 shot pixels, or None if the
        element (or any ancestor it depends on) lacks resolvable geometry."""
        anc = self._ancestor(el)
        if anc is None or anc.id == "root":
            # containing block is the frame itself (root is inset:0, size = frame).
            pw, ph = 1920.0, 1080.0
            ox, oy = 0.0, 0.0
        else:
            abox = self.abs_box(anc)
            if abox is None:
                return None
            ox, oy, pw, ph = abox
        local = el.local_box(parent_w=pw, parent_h=ph)
        if local is None:
            return None
        lx, ly, w, h = local
        return (ox + lx, oy + ly, w, h)

    def abs_center(self, el: Element) -> Optional[Tuple[float, float]]:
        b = self.abs_box(el)
        if b is None:
            return None
        x, y, w, h = b
        return (x + w / 2.0, y + h / 2.0)

    def abs_tip(self, el: Element) -> Optional[Tuple[float, float]]:
        """Bottom-center of the element's box — the visible tip of a teardrop pin."""
        b = self.abs_box(el)
        if b is None:
            return None
        x, y, w, h = b
        return (x + w / 2.0, y + h)

    def abs_origin(self, el: Element) -> Optional[Tuple[float, float]]:
        """Screen-absolute (left, top) of the element — its top-left position, with
        NO width/height required (for auto-sized labels). Resolves the containing
        block's origin + size when known, falling back to the ancestor's own origin
        when the ancestor is itself auto-sized."""
        anc = self._ancestor(el)
        if anc is None or anc.id == "root":
            pw, ph = 1920.0, 1080.0
            ox, oy = 0.0, 0.0
        else:
            abox = self.abs_box(anc)
            if abox is not None:
                ox, oy, pw, ph = abox
            else:
                aorigin = self.abs_origin(anc)
                if aorigin is None:
                    return None
                ox, oy = aorigin
                pw = ph = None  # ancestor size unknown -> %-children can't resolve
        local = el.local_origin(parent_w=pw, parent_h=ph)
        if local is None:
            return None
        return (ox + local[0], oy + local[1])

    def children_of(self, el: Element) -> List[Element]:
        return [c for c in self.elements if c.parent == el.index]

    def descendants_of(self, el: Element) -> List[Element]:
        out: List[Element] = []
        stack = self.children_of(el)
        while stack:
            c = stack.pop()
            out.append(c)
            stack.extend(self.children_of(c))
        return out


class _ShotParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: List[Element] = []
        self._stack: List[Element] = []
        self._style_buf: List[str] = []
        self._in_style = False
        self.style_css = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        attrd = {k.lower(): (v or "") for k, v in attrs}
        if tag == "style":
            self._in_style = True
            return
        el = Element(
            tag=tag,
            id=attrd.get("id", ""),
            classes=attrd.get("class", "").split(),
            style=_split_declarations(attrd.get("style", "")),
            data={k: v for k, v in attrd.items() if k.startswith("data-")},
            attrs=attrd,
            src=attrd.get("src", ""),
            parent=self._stack[-1].index if self._stack else -1,
            index=len(self.elements),
        )
        self.elements.append(el)
        # void elements don't nest text/children
        if tag not in ("img", "br", "hr", "meta", "link", "input", "source", "path", "line"):
            self._stack.append(el)

    def handle_startendtag(self, tag: str, attrs) -> None:
        # self-closing (e.g. <img ... />) — register but never push on the stack.
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1].tag == tag and self._stack[-1] is self.elements[-1]:
            self._stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False
            self.style_css += "".join(self._style_buf)
            self._style_buf = []
            return
        # pop the nearest matching open element
        for k in range(len(self._stack) - 1, -1, -1):
            if self._stack[k].tag == tag:
                del self._stack[k:]
                break

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_buf.append(data)
            return
        text = data.strip()
        if text and self._stack:
            # attribute the text to every open ancestor (so a <div> wrapping a
            # <span>Chapter I</span> also "contains" that text for matching).
            for el in self._stack:
                el.text = (el.text + " " + text).strip()


def _merge_css_rules(el: Element, rules: List[Tuple[List[str], Dict[str, str]]]) -> Dict[str, str]:
    """Merge every <style> rule whose selector matches this element by #id or
    .class (in source order, later wins) into a flat declaration map.

    Only simple ``#id`` and ``.class`` selectors are honored (and a trailing-key
    selector like ``#id .child`` is matched on its LAST simple token against this
    element). This is enough for the shots' flat stylesheets and avoids pretending
    to be a full selector engine.
    """
    merged: Dict[str, str] = {}
    for selectors, decls in rules:
        for sel in selectors:
            last = sel.split()[-1]  # rightmost simple selector
            # strip pseudo-elements/classes (::after, :hover) — geometry only.
            last = last.split(":")[0]
            if not last:
                continue
            matched = False
            if last.startswith("#"):
                matched = (last[1:] == el.id)
            elif last.startswith("."):
                matched = (last[1:] in el.classes)
            if matched:
                merged.update(decls)
    return merged


def parse_shot(path: Path) -> ParsedShot:
    """Parse one shot HTML into elements with merged CSS + resolved geometry."""
    raw = path.read_text(errors="replace")
    p = _ShotParser()
    p.feed(raw)
    rules = _parse_style_block(p.style_css)
    for el in p.elements:
        el.css_rules = _merge_css_rules(el, rules)
    return ParsedShot(path=path, elements=p.elements, raw_html=raw)
