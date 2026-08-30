import { API_URL } from "@/resources.js";

/**
 * Helpers shared by the editor extensions that deal with an item's attached
 * files (images inserted from the file list, and links to data files).
 */

/** Kept in step with the media block's list of displayable images. */
export const IMAGE_EXTENSIONS = [".png", ".jpeg", ".jpg", ".tif", ".tiff", ".gif", ".webp", ".svg"];

/** MIME type used when dragging a file out of the file list. */
export const FILE_DRAG_MIME = "application/x-datalab-file";

/**
 * Matches a link that points at an attached file, on any host.
 *
 * File ids are Mongo ObjectIds, so requiring 24 hex characters keeps this from
 * firing on unrelated links that happen to contain "/files/". Matching on the
 * URL rather than on a stored attribute is deliberate: links dragged into a
 * description long before this existed still resolve as files, with no
 * migration and no rewriting of saved documents.
 */
export const FILE_HREF_PATTERN = /\/files\/([0-9a-f]{24})\/([^/?#]+)/i;

/** URL that serves a file's content, as used by the file list and media block. */
export function datalabFileUrl(fileId, fileName) {
  return `${API_URL}/files/${fileId}/${fileName ?? ""}`;
}

/** Pull the file id and name back out of a file URL, or null if it isn't one. */
export function parseFileHref(href) {
  const match = typeof href === "string" ? href.match(FILE_HREF_PATTERN) : null;
  if (!match) return null;
  let fileName = match[2];
  try {
    fileName = decodeURIComponent(fileName);
  } catch {
    // Leave a malformed escape sequence as-is rather than losing the name.
  }
  return { fileId: match[1], fileName };
}

export function isImageFileName(name) {
  const lower = (name ?? "").toLowerCase();
  return IMAGE_EXTENSIONS.some((extension) => lower.endsWith(extension));
}
