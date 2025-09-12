<template>
  <div class="quill-editor-wrapper">
    <div ref="quillContainer" :data-testid="testId"></div>
  </div>
</template>

<script>
import Quill from "quill";
import "quill/dist/quill.snow.css";

import MarkdownShortcuts from "quill-markdown-shortcuts";
Quill.register("modules/markdownShortcuts", MarkdownShortcuts);

import mermaid from "mermaid";
window.mermaid = mermaid;
import QuillMermaid from "quill-mermaid";
import "quill-mermaid/dist/index.css";
Quill.register(
  {
    "modules/mermaid": QuillMermaid,
  },
  true,
);

import TableUp, {
  defaultCustomSelect,
  TableAlign,
  TableMenuContextmenu,
  TableResizeScale,
  TableSelection,
} from "quill-table-up";
import "quill-table-up/index.css";
import "quill-table-up/table-creator.css";

Quill.register({ [`modules/${TableUp.moduleName}`]: TableUp }, true);

export default {
  name: "QuillEditor",
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    placeholder: {
      type: String,
      default: "Add a description",
    },
    testId: {
      type: String,
      default: "quill-input",
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      quill: null,
    };
  },
  mounted() {
    this.initializeQuill();
  },
  beforeUnmount() {
    if (this.quill) {
      this.quill = null;
    }
  },
  methods: {
    initializeQuill() {
      mermaid.initialize({
        startOnLoad: false,
        theme: "default",
      });
      const modules = {
        toolbar: [
          ["bold", "italic", "underline", "strike"],
          [{ script: "sub" }, { script: "super" }],
          [{ color: [] }, { background: [] }],
          ["clean"],
          [{ align: [] }],
          [{ list: "bullet" }, { list: "ordered" }],
          [{ indent: "-1" }, { indent: "+1" }],
          [{ header: [1, 2, 3, 4, 5, 6, false] }],
          ["link", "image"],
          ["blockquote", "code-block"],
          [{ [TableUp.toolName]: [] }],
          ["mermaid-chart"],
        ],
        [TableUp.moduleName]: {
          customSelect: defaultCustomSelect,
          modules: [
            { module: TableAlign },
            { module: TableResizeScale },
            { module: TableSelection },
            { module: TableMenuContextmenu },
          ],
        },
        mermaid: {
          selectorOptions: {
            onDestroy() {},
            onRemove() {},
            onEdit() {},
          },
          historyStackOptions: {
            maxStack: 100,
            delay: 1000,
          },
        },
        markdownShortcuts: {},
      };

      this.quill = new Quill(this.$refs.quillContainer, {
        theme: "snow",
        placeholder: this.placeholder,
        modules,
      });

      if (this.modelValue) {
        try {
          const delta = JSON.parse(this.modelValue);
          if (delta.ops) {
            setTimeout(() => {
              this.quill.setContents(delta);

              const mermaidModule = this.quill.getModule("mermaid");
              if (mermaidModule && mermaidModule.renderCharts) {
                mermaidModule.renderCharts();
              }
            }, 0);
          } else {
            this.quill.root.innerHTML = this.modelValue;
          }
        } catch (e) {
          this.quill.root.innerHTML = this.modelValue;
        }
      }

      this.quill.on("text-change", () => {
        const delta = this.quill.getContents();
        const deltaString = JSON.stringify(delta);
        this.$emit("update:modelValue", deltaString);
      });
    },
  },
};
</script>
