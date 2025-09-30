import { Node, mergeAttributes } from "@tiptap/core";
import { VueNodeViewRenderer } from "@tiptap/vue-3";
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
});
