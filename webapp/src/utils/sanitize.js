import DOMPurify from "dompurify";

/**
 * Sanitize an untrusted SVG string so it can be safely rendered via `v-html`.
 *
 * Allows the SVG element set (including filters and `<use>`) but strips scripts,
 * styles and event handlers, which are the vectors for XSS in SVG payloads.
 *
 * @param {string|null|undefined} svg - The raw SVG markup.
 * @returns {string} The sanitized SVG, or an empty string for falsy input.
 */
export function sanitizeSVG(svg) {
  if (!svg) return "";
  return DOMPurify.sanitize(svg, {
    USE_PROFILES: { svg: true, svgFilters: true },
    ADD_TAGS: ["use"], // Allow SVG <use> elements
    FORBID_TAGS: ["script", "style"], // Explicitly forbid scripts and styles
    FORBID_ATTR: ["onerror", "onload", "onclick"], // Remove event handlers
  });
}
