/**
 * Utilities for a `display_order` array that mixes block IDs (plain strings)
 * with section markers (plain objects), as produced by the `Section` model on
 * the backend. A section marker groups every block ID that follows it in the
 * array, up to the next section marker or the end of the array, under itself.
 */

/**
 * @param {string|object} entry - An entry from a `display_order` array.
 * @returns {boolean} Whether the entry is a section marker rather than a block ID.
 */
export function isSection(entry) {
  return typeof entry === "object" && entry !== null && entry.type === "section";
}

/**
 * Creates a new section marker with a freshly generated ID.
 *
 * @param {string} title - The initial title for the section.
 * @returns {{type: "section", section_id: string, title: string, description: null}}
 */
export function createSection(title) {
  return {
    type: "section",
    section_id: `section_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    title,
    description: null,
  };
}

/**
 * Groups a flat `display_order` array into renderable entries: ungrouped
 * blocks pass through as-is, while a section and the block IDs nested under
 * it are collected together.
 *
 * @param {Array<string|object>} displayOrder
 * @returns {Array<
 *   {type: "block", block_id: string} | {type: "section", section: object, block_ids: string[]}
 * >}
 */
export function groupDisplayOrder(displayOrder) {
  const groups = [];
  for (const entry of displayOrder || []) {
    if (isSection(entry)) {
      groups.push({ type: "section", section: entry, block_ids: [] });
      continue;
    }
    const lastGroup = groups[groups.length - 1];
    if (lastGroup?.type === "section") {
      lastGroup.block_ids.push(entry);
    } else {
      groups.push({ type: "block", block_id: entry });
    }
  }
  return groups;
}

/**
 * Returns only the block IDs from a `display_order` array, skipping section markers.
 *
 * @param {Array<string|object>} displayOrder
 * @returns {string[]}
 */
export function blockIdsOf(displayOrder) {
  return (displayOrder || []).filter((entry) => !isSection(entry));
}
