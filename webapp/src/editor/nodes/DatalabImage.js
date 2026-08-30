import Image from "@tiptap/extension-image";
import { API_URL } from "@/resources.js";

/**
 * URL that serves the content of an attached file, as used by the media block.
 */
export function datalabFileUrl(fileId, fileName) {
  return `${API_URL}/files/${fileId}/${fileName ?? ""}`;
}

/**
 * The stock image node, extended so that images inserted from an item's attached
 * files remember *which* file they came from.
 *
 * `API_URL` is baked into the bundle per deployment, so an absolute file URL
 * stored inside a description would break for good if the API host ever changed.
 * Keeping the file id alongside it means the `src` can be rebuilt on parse, so
 * existing descriptions repair themselves with no migration.
 *
 * Pasted and base64 images carry no file id and are left exactly as they are.
 */
export const DatalabImage = Image.extend({
  addAttributes() {
    const parent = this.parent?.() ?? {};

    return {
      ...parent,

      fileId: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-file-id"),
        renderHTML: (attributes) =>
          attributes.fileId ? { "data-file-id": attributes.fileId } : {},
      },

      fileName: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-file-name"),
        renderHTML: (attributes) =>
          attributes.fileName ? { "data-file-name": attributes.fileName } : {},
      },

      src: {
        ...parent.src,
        parseHTML: (element) => {
          const fileId = element.getAttribute("data-file-id");
          return fileId
            ? datalabFileUrl(fileId, element.getAttribute("data-file-name"))
            : element.getAttribute("src");
        },
      },
    };
  },
});
