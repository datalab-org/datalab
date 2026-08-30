import Link from "@tiptap/extension-link";
import { VueMarkViewRenderer } from "@tiptap/vue-3";
import FileLinkMarkView from "@/components/FileLinkMarkView.vue";
import { datalabFileUrl, parseFileHref } from "@/editor/files.js";

/**
 * The stock link mark, rendered as a file badge when it points at an attached
 * file, and left alone otherwise.
 *
 * The decision is made from the `href`, not from a stored attribute, so links
 * that were dragged into a description long before this existed pick up the
 * new rendering with no migration.
 */
export const DatalabFileLink = Link.extend({
  addAttributes() {
    const parent = this.parent?.() ?? {};

    return {
      ...parent,

      href: {
        ...parent.href,
        // `API_URL` is baked in per deployment, so a stored link can name a host
        // this instance no longer serves. Rebuild it whenever the URL identifies
        // an attached file, which also repairs links copied between deployments.
        parseHTML: (element) => {
          const href = element.getAttribute("href");
          const file = parseFileHref(href);
          return file ? datalabFileUrl(file.fileId, file.fileName) : href;
        },
      },
    };
  },

  addMarkView() {
    return VueMarkViewRenderer(FileLinkMarkView);
  },
});
