import { Node, mergeAttributes } from "@tiptap/core";
import { VueNodeViewRenderer } from "@tiptap/vue-3";
import { Plugin } from "prosemirror-state";
import CrossReferenceComponent from "@/components/CrossReferenceComponent.vue";

export const CrossReferenceNode = Node.create({
  name: "crossreference",
  group: "inline",
  inline: true,
  atom: true,

  addAttributes() {
    return {
      itemId: {
        default: null,
        parseHTML: (el) => el.getAttribute("data-item-id"),
        renderHTML: (attrs) => ({ "data-item-id": attrs.itemId }),
      },
      itemType: {
        default: "samples",
        parseHTML: (el) => el.getAttribute("data-item-type"),
        renderHTML: (attrs) => ({ "data-item-type": attrs.itemType }),
      },
      name: {
        default: "",
        parseHTML: (el) => el.getAttribute("data-name"),
        renderHTML: (attrs) => ({ "data-name": attrs.name }),
      },
      chemform: {
        default: "",
        parseHTML: (el) => el.getAttribute("data-chemform"),
        renderHTML: (attrs) => ({ "data-chemform": attrs.chemform }),
      },
    };
  },

  parseHTML() {
    return [{ tag: 'span[data-type="crossreference"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes, { "data-type": "crossreference" })];
  },

  addNodeView() {
    return VueNodeViewRenderer(CrossReferenceComponent);
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handleClick: (view, pos, event) => {
            try {
              const { doc } = view.state;
              const $pos = doc.resolve(pos);
              const node = $pos.nodeAfter || $pos.nodeBefore;
              if (!node) return false;

              if (node.type.name === "crossreference") {
                const { itemId } = node.attrs;
                if (!itemId) return false;

                const url = `/edit/${itemId}`;
                if (event && typeof event.preventDefault === "function") event.preventDefault();
                window.open(url, "_blank");
                return true;
              }
            } catch (err) {
              console.error("CrossReferenceNode handleClick error:", err);
            }
            return false;
          },
        },
      }),
    ];
  },
});
