<template>
  <div ref="editorContainer" class="position-relative">
    <div
      v-if="editor && (showToolbar || markdownMode)"
      class="btn-toolbar mb-2 border rounded p-2 shadow-sm bg-white sticky-top overflow-auto flex-wrap"
      style="z-index: 10; row-gap: 0.5rem"
    >
      <div v-for="group in toolbarGroups" :key="group.name" class="btn-group btn-group-sm mr-2">
        <button
          v-for="btn in visibleButtons(group)"
          :key="btn.name"
          type="button"
          class="btn btn-outline-secondary"
          :class="{
            active: btn.isActive?.(editor),
            disabled: markdownMode && btn.name !== 'toggleMarkdown',
          }"
          :disabled="btn.isDisabled?.(editor) || (markdownMode && btn.name !== 'toggleMarkdown')"
          :title="btn.title"
          :style="btn.buttonStyle?.()"
          @click="btn.command(editor, $event)"
        >
          <font-awesome-icon v-if="btn.icon" :icon="btn.icon" />
          <span v-else>{{ btn.label }}</span>
        </button>
      </div>
      <div
        v-if="editor"
        class="custom-control custom-switch ml-2 d-flex align-items-center"
        style="height: 38px"
      >
        <input
          id="markdownToggleSwitch"
          v-model="markdownMode"
          type="checkbox"
          class="custom-control-input"
          @change="toggleMarkdownView"
        />
        <label class="custom-control-label" for="markdownToggleSwitch">
          {{ markdownMode ? "Markdown" : "Preview" }}
        </label>
      </div>
    </div>

    <teleport to="body">
      <div
        v-if="showColorPicker"
        class="position-absolute bg-white border rounded shadow p-2"
        :style="{ top: pickerPosition.top + 'px', left: pickerPosition.left + 'px', zIndex: 9999 }"
      >
        <div class="d-grid" style="grid-template-columns: repeat(6, 1fr); gap: 6px; width: 220px">
          <button
            class="btn btn-sm btn-outline-secondary"
            type="button"
            title="Reset to default"
            style="width: 28px; height: 28px; padding: 0"
            @click="resetColor"
          >
            <font-awesome-icon icon="times" />
          </button>
          <button
            v-for="c in predefinedColors"
            :key="c"
            class="btn p-0"
            type="button"
            :aria-label="c"
            :class="{ 'border-dark border-2': currentColor === c }"
            :style="{
              backgroundColor: c,
              width: '28px',
              height: '28px',
              border: '1px solid #dee2e6',
            }"
            @click="setColor(c)"
          />
        </div>
      </div>
    </teleport>

    <editor-content
      v-if="!markdownMode"
      :editor="editor"
      class="form-control-plaintext border rounded p-2 d-inline-block w-100"
      :class="{ 'border-primary': showToolbar }"
    />

    <textarea
      v-else
      v-model="markdownContent"
      class="form-control border rounded p-2 w-100"
      style="font-family: monospace; min-height: 200px; white-space: pre-wrap"
      placeholder="Edit in Markdown..."
      @blur="applyMarkdownChanges"
      @input="editor.commands.updateMarkdownContent(markdownContent)"
    />

    <MermaidModal
      v-model="showMermaidModal"
      :code="mermaidDraft"
      :is-editing="editingMermaid"
      @save="handleMermaidSave"
    />
  </div>
</template>

<script>
import { Editor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import { Table, TableRow, TableCell, TableHeader } from "@tiptap/extension-table";
import Placeholder from "@tiptap/extension-placeholder";
import { Color } from "@tiptap/extension-color";
import { TextStyle } from "@tiptap/extension-text-style";
import Highlight from "@tiptap/extension-highlight";
import Typography from "@tiptap/extension-typography";
import Mathematics from "@tiptap/extension-mathematics";
import "katex/dist/katex.min.css";

import { MermaidNode } from "@/editor/nodes/MermaidNode";
import MermaidModal from "@/components/MermaidModal.vue";

import { CrossReferenceNode } from "@/editor/nodes/CrossReferenceNode";
import { CrossReferenceInputRule } from "@/editor/extensions/CrossReferenceInputRule";

import { MarkdownToggle } from "@/editor/extensions/MarkdownToggle";

export default {
  components: { EditorContent, MermaidModal },

  props: {
    modelValue: { type: String, default: "" },
    placeholder: { type: String, default: "Add a description" },
    inline: { type: Boolean, default: true },
  },

  emits: ["update:modelValue"],

  data() {
    return {
      editor: null,
      showToolbar: false,
      showColorPicker: false,
      pickerPosition: { top: 0, left: 0 },
      currentColor: "#000000",
      predefinedColors: ["#000000", "#FFFFFF"].concat(
        Array.from({ length: 12 }, (_, h) =>
          Array.from({ length: 6 }, (_, l) => `hsl(${h * 30}, 90%, ${30 + l * 10}%)`),
        ).flat(),
      ),
      handleDocumentClick: null,
      handleCrossRefClick: null,
      showMermaidModal: false,
      mermaidDraft: "",
      editingMermaid: false,
      markdownMode: false,
      markdownContent: "",
    };
  },

  computed: {
    toolbarGroups() {
      return [
        {
          name: "formatting",
          buttons: [
            {
              name: "bold",
              icon: "bold",
              title: "Bold",
              command: (ed) => ed.chain().focus().toggleBold().run(),
              isActive: (ed) => ed.isActive("bold"),
              isDisabled: (ed) => !ed.can().chain().focus().toggleBold().run(),
            },
            {
              name: "italic",
              icon: "italic",
              title: "Italic",
              command: (ed) => ed.chain().focus().toggleItalic().run(),
              isActive: (ed) => ed.isActive("italic"),
              isDisabled: (ed) => !ed.can().chain().focus().toggleItalic().run(),
            },
            {
              name: "underline",
              icon: "underline",
              title: "Underline",
              command: (ed) => ed.chain().focus().toggleUnderline().run(),
              isActive: (ed) => ed.isActive("underline"),
              isDisabled: (ed) => !ed.can().chain().focus().toggleUnderline().run(),
            },
            {
              name: "strike",
              icon: "strikethrough",
              title: "Strikethrough",
              command: (ed) => ed.chain().focus().toggleStrike().run(),
              isActive: (ed) => ed.isActive("strike"),
              isDisabled: (ed) => !ed.can().chain().focus().toggleStrike().run(),
            },
          ],
        },
        {
          name: "headings",
          buttons: [
            {
              name: "h1",
              label: "H1",
              title: "Heading 1",
              command: (ed) => ed.chain().focus().setHeading({ level: 1 }).run(),
              isActive: (ed) => ed.isActive("heading", { level: 1 }),
            },
            {
              name: "h2",
              label: "H2",
              title: "Heading 2",
              command: (ed) => ed.chain().focus().setHeading({ level: 2 }).run(),
              isActive: (ed) => ed.isActive("heading", { level: 2 }),
            },
            {
              name: "h3",
              label: "H3",
              title: "Heading 3",
              command: (ed) => ed.chain().focus().setHeading({ level: 3 }).run(),
              isActive: (ed) => ed.isActive("heading", { level: 3 }),
            },
            {
              name: "paragraph",
              label: "¶",
              title: "Normal text",
              command: (ed) => ed.chain().focus().setParagraph().run(),
              isActive: (ed) => ed.isActive("paragraph"),
            },
          ],
        },
        {
          name: "lists",
          buttons: [
            {
              name: "bulletList",
              icon: "list-ul",
              title: "Bullet List",
              command: (ed) => ed.chain().focus().toggleBulletList().run(),
              isActive: (ed) => ed.isActive("bulletList"),
            },
            {
              name: "orderedList",
              icon: "list-ol",
              title: "Ordered List",
              command: (ed) => ed.chain().focus().toggleOrderedList().run(),
              isActive: (ed) => ed.isActive("orderedList"),
            },
          ],
        },
        {
          name: "tables",
          buttons: [
            {
              name: "insertTable",
              icon: "table",
              title: "Insert Table",
              command: (ed) =>
                ed.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
            },
            {
              name: "addColumn",
              label: "+ Col",
              title: "Add Column After",
              command: (ed) => ed.chain().focus().addColumnAfter().run(),
              isVisible: (ed) => ed.isActive("table"),
            },
            {
              name: "addRow",
              label: "+ Row",
              title: "Add Row After",
              command: (ed) => ed.chain().focus().addRowAfter().run(),
              isVisible: (ed) => ed.isActive("table"),
            },
            {
              name: "deleteColumn",
              label: "× Col",
              title: "Delete Column",
              command: (ed) => ed.chain().focus().deleteColumn().run(),
              isVisible: (ed) => ed.isActive("table"),
            },
            {
              name: "deleteRow",
              label: "× Row",
              title: "Delete Row",
              command: (ed) => ed.chain().focus().deleteRow().run(),
              isVisible: (ed) => ed.isActive("table"),
            },
            {
              name: "deleteTable",
              icon: "trash",
              title: "Delete Table",
              command: (ed) => ed.chain().focus().deleteTable().run(),
              isVisible: (ed) => ed.isActive("table"),
            },
          ],
        },
        {
          name: "insert",
          buttons: [
            {
              name: "mathInline",
              label: "ƒ(x)",
              title: "Insert Inline Math",
              command: (editor) => {
                const formula = window.prompt("Math formula (KaTeX)", "x^2 + y^2");
                if (!formula) return;

                editor.chain().focus().insertInlineMath({ latex: formula }).run();
              },
              isActive: (ed) => ed.isActive("inlineMath"),
            },
            {
              name: "link",
              icon: "link",
              title: "Add Link",
              command: () => this.setLink(),
              isActive: (ed) => ed.isActive("link"),
            },
            {
              name: "image",
              icon: "image",
              title: "Add Image",
              command: () => this.addImage(),
            },
            {
              name: "hr",
              icon: "minus",
              title: "Horizontal Rule",
              command: (ed) => ed.chain().focus().setHorizontalRule().run(),
            },
          ],
        },
        {
          name: "color",
          buttons: [
            {
              name: "color",
              icon: "palette",
              title: "Text Color",
              command: (ed, evt) => this.toggleColorPicker(evt),
              buttonStyle: () => ({ color: this.currentColor }),
            },
          ],
        },
        {
          name: "mermaid",
          buttons: [
            {
              name: "insertMermaid",
              icon: "project-diagram",
              title: "Insert Mermaid",
              command: () => this.startMermaidCreate(),
            },
            {
              name: "editMermaid",
              icon: "pen",
              title: "Edit Mermaid",
              command: () => this.startMermaidEdit(),
              isVisible: (ed) => ed.isActive("mermaid"),
            },
            {
              name: "deleteMermaid",
              icon: "trash",
              title: "Delete Mermaid",
              command: (ed) => ed.chain().focus().deleteSelection().run(),
              isVisible: (ed) => ed.isActive("mermaid"),
            },
          ],
        },
        {
          name: "view",
          buttons: [],
        },
        {
          name: "clear",
          buttons: [
            {
              name: "clear",
              icon: "remove-format",
              title: "Clear Formatting",
              command: (ed) => ed.chain().focus().clearNodes().unsetAllMarks().run(),
            },
          ],
        },
      ];
    },
  },

  watch: {
    modelValue(value) {
      if (this.editor && this.editor.getHTML() !== value) {
        this.editor.commands.setContent(value, false);
      }
    },
  },

  mounted() {
    this.editor = new Editor({
      extensions: [
        StarterKit.configure({ heading: { levels: [1, 2, 3, 4, 5, 6] } }),
        Underline,
        Image.configure({ inline: true }),
        Link.configure({
          openOnClick: false,
          HTMLAttributes: { target: "_blank", rel: "noopener noreferrer" },
        }),
        Table.configure({ resizable: true }),
        TableRow,
        TableHeader,
        TableCell,
        Placeholder.configure({ placeholder: this.placeholder }),
        TextStyle,
        Color,
        Highlight.configure({ multicolor: true }),
        Typography,
        MermaidNode,
        CrossReferenceNode,
        CrossReferenceInputRule,
        MarkdownToggle,
        Mathematics.configure({
          HTMLAttributes: {
            class: "math",
          },
          inlineOptions: {
            onClick: (node, pos) => {
              const currentLatex = node.attrs.latex || "";
              const newLatex = window.prompt("Edit Math formula (KaTeX):", currentLatex);
              if (newLatex !== null && this.editor) {
                this.editor
                  .chain()
                  .setNodeSelection(pos)
                  .updateInlineMath({ latex: newLatex })
                  .focus()
                  .run();
              }
            },
          },
          blockOptions: {
            onClick: (node, pos) => {
              const currentLatex = node.attrs.latex || "";
              const newLatex = window.prompt("Edit Math formula (KaTeX):", currentLatex);
              if (newLatex !== null && this.editor) {
                this.editor
                  .chain()
                  .setNodeSelection(pos)
                  .updateBlockMath({ latex: newLatex })
                  .focus()
                  .run();
              }
            },
          },
          katexOptions: {
            throwOnError: false,
            strict: false,
            trust: true,
            macros: {
              "\\R": "\\mathbb{R}",
              "\\N": "\\mathbb{N}",
              "\\Z": "\\mathbb{Z}",
              "\\C": "\\mathbb{C}",
              "\\d": "\\mathrm{d}",
            },
          },
        }),
      ],
      content: this.modelValue,
    });

    this.editor.on("update", () => this.$emit("update:modelValue", this.editor.getHTML()));
    this.editor.on("focus", () => {
      if (!this.markdownMode) {
        this.showToolbar = true;
      }
    });

    this.editor.on("blur", () => {
      if (!this.markdownMode) {
        setTimeout(() => {
          const suggestionEl = document.querySelector(".tiptap-suggestions");
          if (
            !this.$el.contains(document.activeElement) &&
            (!suggestionEl || !suggestionEl.contains(document.activeElement))
          ) {
            this.showToolbar = false;
            this.showColorPicker = false;
          }
        }, 150);
      }
    });

    this.editor.view.dom.addEventListener(
      "mousedown",
      (e) => {
        const crossRefEl = e.target.closest(".cross-reference-wrapper");
        if (crossRefEl) {
          e.preventDefault();
          e.stopPropagation();
        }
      },
      true,
    );

    this.handleDocumentClick = (e) => this.handleClickOutside(e);
    document.addEventListener("click", this.handleDocumentClick);
    this.handleCrossRefClick = (e) => {
      const crossRefEl = e.target.closest(".cross-reference-wrapper");
      if (crossRefEl) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    this.editor.view.dom.addEventListener("mousedown", this.handleCrossRefClick, true);
  },

  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    if (this.editor) {
      this.editor.view.dom.removeEventListener("mousedown", this.handleCrossRefClick, true);
      this.editor.destroy();
    }
  },

  methods: {
    visibleButtons(group) {
      return group.buttons.filter((btn) => !btn.isVisible || btn.isVisible(this.editor));
    },
    handleClickOutside(event) {
      const editorElement = this.$refs.editorContainer;
      if (editorElement && !editorElement.contains(event.target)) {
        this.showToolbar = false;
        this.showColorPicker = false;
      }
    },
    toggleColorPicker(event) {
      if (this.showColorPicker) return (this.showColorPicker = false);
      const rect = event.currentTarget.getBoundingClientRect();
      this.pickerPosition = { top: rect.bottom + window.scrollY, left: rect.left + window.scrollX };
      this.currentColor = this.getActiveColor();
      this.showColorPicker = true;
    },
    getActiveColor() {
      if (!this.editor) return "#000000";
      const attrs =
        this.editor.getAttributes("textStyle") || this.editor.getAttributes("color") || {};
      return attrs.color || "#000000";
    },
    resetColor() {
      this.editor?.chain().focus().setColor("#000000").run();
      this.currentColor = "#000000";
      this.showColorPicker = false;
    },
    setColor(color) {
      this.editor?.chain().focus().setColor(color).run();
      this.currentColor = color;
      this.showColorPicker = false;
    },
    setLink() {
      const previousUrl = this.editor.getAttributes("link").href;
      const url = window.prompt("URL", previousUrl);
      if (url === null) return;
      if (url === "") this.editor.chain().focus().extendMarkRange("link").unsetLink().run();
      else this.editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
    },
    addImage() {
      const url = window.prompt("Image URL");
      if (url) this.editor.chain().focus().setImage({ src: url }).run();
    },
    startMermaidCreate() {
      this.mermaidDraft = "graph TD;\n  A[Start] --> B[Process];\n  B --> C[End];";
      this.editingMermaid = false;
      this.showMermaidModal = true;
    },
    startMermaidEdit() {
      const { state } = this.editor;
      const { from, to } = state.selection;
      let mermaidNode = null;
      state.doc.nodesBetween(from, to, (node) => {
        if (node.type.name === "mermaid") {
          mermaidNode = node;
          return false;
        }
      });
      if (mermaidNode) {
        this.mermaidDraft = mermaidNode.attrs.code || "graph TD;\n  A[Start] --> B[Process];";
        this.editingMermaid = true;
        this.showMermaidModal = true;
      }
    },
    handleMermaidSave(code) {
      if (this.editingMermaid) {
        const { state } = this.editor;
        const { from, to } = state.selection;
        state.doc.nodesBetween(from, to, (node, pos) => {
          if (node.type.name === "mermaid") {
            this.editor
              .chain()
              .focus()
              .setNodeSelection(pos)
              .updateAttributes("mermaid", { code })
              .run();
            return false;
          }
        });
      } else {
        this.editor.chain().focus().insertContent({ type: "mermaid", attrs: { code } }).run();
      }
      this.showMermaidModal = false;
      this.mermaidDraft = "";
      this.editingMermaid = false;
    },
    toggleMarkdownView() {
      if (this.markdownMode) {
        this.markdownContent = this.editor.commands.getMarkdownContent();
        if (!this.markdownContent) {
          this.editor.commands.toggleMarkdownView();
          this.markdownContent = this.editor.commands.getMarkdownContent();
        }
      } else {
        this.applyMarkdownChanges();
      }
    },
    applyMarkdownChanges() {
      if (this.markdownMode) {
        this.editor.commands.updateMarkdownContent(this.markdownContent);
      }
    },
  },
};
</script>

<style scoped>
:deep(.ProseMirror table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

:deep(.ProseMirror table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

:deep(.ProseMirror table td),
:deep(.ProseMirror table th) {
  border: 1px solid #dee2e6;
  text-align: center;
}
</style>
