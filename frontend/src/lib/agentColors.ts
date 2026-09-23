/**
 * The categorical palette, and how a debate's agents get assigned from it.
 *
 * These are dataviz categorical steps for a dark surface, not Tailwind's hues.
 * The obvious choice — violet/rose/emerald/orange/cyan/blue at the 400 step —
 * fails validation against this app's #0a0f1e surface: blue and cyan sit at
 * ΔE 13.2 for *normal* vision (below the 15 floor), and emerald and rose
 * collapse to ΔE 4.6 under deuteranopia. This order passes every check:
 * worst adjacent CVD ΔE 8.4, worst adjacent normal-vision ΔE 19.3, all above
 * 3:1 contrast.
 *
 * There are eight slots and many more agents than that, so colour is assigned
 * per debate rather than fixed per archetype. A ninth series is never a
 * generated hue, which is why a debate is capped at eight agents — every
 * chart then draws from a palette that has actually been validated.
 */
export const SERIES = [
  "#3987e5", // blue
  "#d95926", // orange
  "#199e70", // aqua
  "#c98500", // yellow
  "#d55181", // magenta
  "#008300", // green
  "#9085e9", // violet
  "#e66767", // red
] as const;

export const MAX_SERIES = SERIES.length;

/** Neutral, for anything beyond the validated slots. */
export const NEUTRAL = "#94a3b8";

export const SURFACE = "#0a0f1e";

/**
 * Assign slots in the order given. Pass the debate's agents in a stable order
 * so the chart, the cards and the exchanges all agree — and so a filter that
 * changes the count does not repaint the survivors.
 */
export function paletteFor(keys: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  let slot = 0;
  for (const key of keys) {
    if (key in out) continue;
    out[key] = slot < MAX_SERIES ? SERIES[slot] : NEUTRAL;
    slot += 1;
  }
  return out;
}

export function colorFrom(palette: Record<string, string>, key: string): string {
  return palette[key] ?? NEUTRAL;
}
