/**
 * Shared theme contract for branded reusable components.
 *
 * The Python helper at `brand_assets/tokens/playbook_to_tokens.py` produces
 * objects matching this shape. Components default to sleep-network-base
 * values when no theme is supplied so they render standalone in dev/preview.
 */

export interface BrandTheme {
  // ── Colors ─────────────────────────────────────────────────────────────
  bg: string;                       // page/plate background
  text: string;                     // primary text (cream — never raw white)
  accent: string;                   // brass gold — primary network accent
  accentSecondary?: string | null;
  muted?: string;
  stampRed?: string | null;         // MM-only (CLASSIFIED/REDACTED). null on Huxley.

  // ── Typography ─────────────────────────────────────────────────────────
  fontHeading: string;
  fontBody: string;
  fontMono?: string;
  headingWeight?: number;
  bodyWeight?: number;

  // ── Motion (frames) ────────────────────────────────────────────────────
  fps?: number;
  fadeFrames?: number;              // 1.5s @ 24fps = 36
  holdMinFrames?: number;           // 4.0s @ 24fps = 96
  textCardHoldFrames?: number;      // 5.0s @ 24fps = 120

  // ── Channel identity (for components that surface name/network) ───────
  channelName?: string;
  network?: string;
  communityName?: string;
  closingTagline?: string;

  // Internal — playbook name for traceability.
  _playbook?: string;
}

/**
 * Sleep-network-base defaults. Used when a component is rendered without an
 * explicit theme (dev/preview).
 */
export const NETWORK_BASE_THEME: BrandTheme = {
  bg: "#0d0d1a",
  text: "#f0e6d2",
  accent: "#c9a84c",
  accentSecondary: "#8c6e23",
  muted: "#6a6a7a",
  stampRed: null,
  fontHeading: "Playfair Display, Georgia, serif",
  fontBody: "Georgia, serif",
  fontMono: "Courier New, monospace",
  headingWeight: 700,
  bodyWeight: 400,
  fps: 24,
  fadeFrames: 36,
  holdMinFrames: 96,
  textCardHoldFrames: 120,
  channelName: "",
  network: "Sleep Network",
  communityName: "",
  closingTagline: "",
};

/**
 * Resolve a (possibly partial) theme against the network-base defaults.
 * Components should call this once at the top of render so every token has a value.
 */
export function resolveTheme(theme?: Partial<BrandTheme>): BrandTheme {
  return { ...NETWORK_BASE_THEME, ...(theme ?? {}) };
}
