import { Node, mergeAttributes } from "@tiptap/core";
import { VueNodeViewRenderer } from "@tiptap/vue-3";
import MermaidComponent from "@/components/MermaidComponent.vue";

export const MermaidNode = Node.create({
  name: "mermaid",
  group: "block",
  atom: true,

  addAttributes() {
    return {
      code: {
        default: "graph TD; A[Start] --> B[End];",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "div[data-type='mermaid']",
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ["div", mergeAttributes({ "data-type": "mermaid" }, HTMLAttributes)];
  },

  addNodeView() {
    return VueNodeViewRenderer(MermaidComponent);
  },
});
