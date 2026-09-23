/**
 * Model output occasionally arrives as `{ crux: "..." }` where the schema
 * declares a plain string, which React refuses to render. The backend
 * normalises new debates at the source; this keeps debates already stored in
 * the wrong shape — and anything still in flight — from crashing the page.
 */
export function asText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  if (typeof value === "object") {
    const inner = Object.values(value as Record<string, unknown>);
    if (inner.length === 1 && typeof inner[0] === "string") return inner[0];
  }
  return String(value);
}
