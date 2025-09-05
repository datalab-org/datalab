<template>
  <component
    :is="currentEditor"
    v-model="content"
    :placeholder="placeholder"
    :enable-markdown="enableMarkdown"
    :test-id="testId"
    @update:model-value="handleUpdate"
  />
</template>

<script>
import TinyMceInline from "./TinyMceInline.vue";
import QuillEditor from "./QuillEditor.vue";

export default {
  name: "EditorTransition",
  components: {
    TinyMceInline,
    QuillEditor,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    placeholder: {
      type: String,
      default: "",
    },
    forceEditor: {
      type: String,
      default: null,
    },
    enableMarkdown: {
      type: Boolean,
      default: true,
    },
    testId: {
      type: String,
      default: "rich-text-editor",
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      content: this.modelValue,
      editorType: null,
    };
  },
  computed: {
    currentEditor() {
      return this.editorType === "tinymce" ? "TinyMceInline" : "QuillEditor";
    },
  },
  watch: {
    modelValue(newVal) {
      this.content = newVal;
    },
  },
  created() {
    this.determineEditorType();
  },
  methods: {
    handleUpdate(value) {
      this.$emit("update:modelValue", value);
    },
    determineEditorType() {
      if (this.forceEditor) {
        this.editorType = this.forceEditor;
        return;
      }

      if (!this.content || this.content.trim() === "") {
        this.editorType = "quill";
        return;
      }

      const tinymceIndicators = [
        "mce-",
        "data-mce-",
        '<table style="width: 50%"',
        "margin-left: 1rem",
      ];

      const isLegacy = tinymceIndicators.some((indicator) => this.content.includes(indicator));

      this.editorType = isLegacy ? "tinymce" : "quill";
    },
  },
};
</script>
