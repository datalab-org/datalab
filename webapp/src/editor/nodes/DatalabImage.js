import Image from "@tiptap/extension-image";
import { datalabFileUrl, parseFileHref } from "@/editor/files.js";

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
        parseHTML: (element) =>
          element.getAttribute("data-file-id") ??
          parseFileHref(element.getAttribute("src"))?.fileId ??
          null,
        renderHTML: (attributes) =>
          attributes.fileId ? { "data-file-id": attributes.fileId } : {},
      },

      fileName: {
        default: null,
        parseHTML: (element) =>
          element.getAttribute("data-file-name") ??
          parseFileHref(element.getAttribute("src"))?.fileName ??
          null,
        renderHTML: (attributes) =>
          attributes.fileName ? { "data-file-name": attributes.fileName } : {},
      },

      src: {
        ...parent.src,
        parseHTML: (element) => {
          const src = element.getAttribute("src");
          const fileId = element.getAttribute("data-file-id");
          if (fileId) {
            return datalabFileUrl(fileId, element.getAttribute("data-file-name"));
          }
          // An image embedded before this extension existed carries no data
          // attributes, but its src may still identify an attached file.
          const file = parseFileHref(src);
          return file ? datalabFileUrl(file.fileId, file.fileName) : src;
        },
      },
    };
  },
});
