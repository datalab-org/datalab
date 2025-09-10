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
        ],
        [TableUp.moduleName]: {
          customSelect: defaultCustomSelect,
          customBtn: false,
          fullSwitch: true,
          modules: [
            { module: TableAlign },
            { module: TableResizeScale },
            { module: TableSelection },
            { module: TableMenuContextmenu },
          ],
        },
        markdownShortcuts: {},
      };

      this.quill = new Quill(this.$refs.quillContainer, {
        theme: "snow",
        placeholder: this.placeholder,
        modules,
      });

      if (this.modelValue) {
        this.quill.root.innerHTML = this.modelValue;
      }

      this.quill.on("text-change", () => {
        const html = this.quill.root.innerHTML;
        this.$emit("update:modelValue", html === "<p><br></p>" ? "" : html);
      });
    },
  },
};
</script>
