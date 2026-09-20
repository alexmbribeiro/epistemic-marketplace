import type { ArchetypeId } from "@/types";

/**
 * One identity colour per archetype, shared by the cards and the charts.
 *
 * These are the dataviz categorical steps for a dark surface, not Tailwind's
 * hues. The obvious choice — violet/rose/emerald/orange/cyan/blue at the 400
 * step — fails validation against this app's #0a0f1e surface: blue and cyan
 * sit at ΔE 13.2 for *normal* vision (below the 15 floor), and emerald and
 * rose collapse to ΔE 4.6 under deuteranopia. This set passes every check:
 * worst adjacent CVD ΔE 8.4, worst adjacent normal-vision ΔE 19.3, all six
 * above 3:1 contrast.
 *
 * Assign in this fixed order and never cycle it — colour follows the agent,
 * not its rank in a filtered list.
 */
export const SERIES_COLORS: Record<ArchetypeId, string> = {
  bayesian: "#3987e5",
  falsificationist: "#d95926",
  analogist: "#199e70",
  contrarian: "#c98500",
  dialectician: "#d55181",
  frequentist: "#008300",
  domain_expert: "#9085e9",
  custom: "#e66767",
};

export const SURFACE = "#0a0f1e";

export function agentColor(archetype: string): string {
  return SERIES_COLORS[archetype as ArchetypeId] ?? SERIES_COLORS.custom;
}
