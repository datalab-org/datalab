import { parseUTCDate } from "@/field_utils.js";

export const UNDATED_GROUP_KEY = "undated";

/**
 * The time to place a block at in the timeline: its measurement time if known,
 * otherwise its creation time. Mirrors `Block.timestamp` on the server.
 *
 * @param {object | undefined} block - A block payload from `blocks_obj`
 * @returns {Date | null} The timestamp, or null if the block has no valid date
 */
export function blockTimestamp(block) {
  const value = block?.metadata?.measured_at ?? block?.created_at;
  if (!value) {
    return null;
  }
  const date = parseUTCDate(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function localDayKey(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/**
 * Sorts blocks oldest first and groups them by (local) day. Blocks sharing a
 * timestamp keep their manual order; undated blocks come last, in manual order.
 *
 * @param {string[] | undefined} displayOrder - The manual block order
 * @param {object | undefined} blocksObj - Block payloads keyed by block ID
 * @returns {{ key: string, date: Date | null, blockIds: string[] }[]}
 */
export function groupBlocksByDay(displayOrder, blocksObj) {
  const entries = (displayOrder || []).map((blockId, index) => ({
    blockId,
    index,
    date: blockTimestamp(blocksObj?.[blockId]),
  }));

  const dated = entries
    .filter((entry) => entry.date)
    .sort((a, b) => a.date - b.date || a.index - b.index);
  const undated = entries.filter((entry) => !entry.date);

  const groups = dated.reduce((acc, entry) => {
    const key = localDayKey(entry.date);
    const last = acc[acc.length - 1];
    if (last?.key === key) {
      return [...acc.slice(0, -1), { ...last, blockIds: [...last.blockIds, entry.blockId] }];
    }
    return [...acc, { key, date: entry.date, blockIds: [entry.blockId] }];
  }, []);

  return undated.length
    ? [
        ...groups,
        { key: UNDATED_GROUP_KEY, date: null, blockIds: undated.map((entry) => entry.blockId) },
      ]
    : groups;
}
