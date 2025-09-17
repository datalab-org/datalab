<template>
  <div class="tiptap-inline-editor">
    <div
      v-if="editor && showToolbar"
      class="btn-toolbar mb-2 border rounded p-2 shadow-sm sticky-top bg-white"
    >
      <div v-for="group in toolbarGroups" :key="group.name" class="btn-group btn-group-sm mr-2">
        <button
          v-for="btn in visibleButtons(group)"
          :key="btn.name"
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: btn.isActive && btn.isActive(editor) }"
          :disabled="btn.isDisabled && btn.isDisabled(editor)"
          :title="btn.title"
          :style="btn.buttonStyle ? btn.buttonStyle() : {}"
          @click="btn.command(editor, $event)"
        >
          <font-awesome-icon v-if="btn.icon" :icon="btn.icon" />
          <span v-else>{{ btn.label }}</span>
        </button>
      </div>
    </div>

    <teleport to="body">
      <div
        v-if="showColorPicker"
        class="color-picker"
        :style="{ top: pickerPosition.top + 'px', left: pickerPosition.left + 'px' }"
      >
        <div class="color-grid">
          <button
            class="color-button reset"
            type="button"
            title="Reset to default"
            @click="resetColor"
          >
            <font-awesome-icon icon="times" />
          </button>

          <button
            v-for="c in predefinedColors"
            :key="c"
            class="color-button"
            type="button"
            :aria-label="c"
            :class="{ selected: currentColor === c }"
            :style="{ backgroundColor: c }"
            @click="setColor(c)"
          />
        </div>
      </div>
    </teleport>

    <editor-content
      :editor="editor"
      class="form-control-plaintext border rounded p-2"
      :class="{
        'd-inline-block w-100': inline,
        'border-primary': showToolbar,
      }"
    />
  </div>
</template>

<script>
import { Editor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import Placeholder from "@tiptap/extension-placeholder";
import { Color } from "@tiptap/extension-color";
import TextStyle from "@tiptap/extension-text-style";
import Highlight from "@tiptap/extension-highlight";

export default {
  components: { EditorContent },

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
        Image.configure({ inline: true, allowBase64: true }),
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
      ],
      content: this.modelValue,
      onUpdate: () => this.$emit("update:modelValue", this.editor.getHTML()),
      onFocus: () => (this.showToolbar = true),
      onBlur: () => {
        setTimeout(() => {
          if (!this.$el.contains(document.activeElement)) {
            this.showToolbar = false;
            this.showColorPicker = false;
          }
        }, 150);
      },
    });

    this.handleDocumentClick = (e) => this.handleClickOutside(e);
    document.addEventListener("click", this.handleDocumentClick);
  },

  beforeUnmount() {
    document.removeEventListener("click", this.handleDocumentClick);
    this.editor?.destroy();
  },

  methods: {
    visibleButtons(group) {
      return group.buttons.filter((btn) => !btn.isVisible || btn.isVisible(this.editor));
    },
    handleClickOutside(e) {
      if (!this.showColorPicker) return;
      const picker = document.querySelector(".color-picker");
      if (picker && picker.contains(e.target)) return;
      if (this.$el && this.$el.contains(e.target)) return;
      this.showColorPicker = false;
    },
    toggleColorPicker(event) {
      if (this.showColorPicker) {
        this.showColorPicker = false;
        return;
      }
      const rect = event.currentTarget.getBoundingClientRect();
      this.pickerPosition = {
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
      };
      this.currentColor = this.getActiveColor();
      this.showColorPicker = true;
    },
    getActiveColor() {
      if (!this.editor) return "#000000";
      const a = this.editor.getAttributes("textStyle") || this.editor.getAttributes("color") || {};
      return a.color || "#000000";
    },
    resetColor() {
      if (!this.editor) return;
      if (this.editor.can().chain().focus().unsetColor) {
        try {
          this.editor.chain().focus().unsetColor().run();
        } catch (e) {
          this.editor.chain().focus().setColor("#000000").run();
        }
      } else {
        this.editor.chain().focus().setColor("#000000").run();
      }
      this.currentColor = "#000000";
      this.showColorPicker = false;
    },
    setColor(color) {
      if (!this.editor) return;
      this.editor.chain().focus().setColor(color).run();
      this.currentColor = color;
      this.showColorPicker = false;
    },
    setLink() {
      const previousUrl = this.editor.getAttributes("link").href;
      const url = window.prompt("URL", previousUrl);
      if (url === null) return;
      if (url === "") {
        this.editor.chain().focus().extendMarkRange("link").unsetLink().run();
        return;
      }
      this.editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
    },
    addImage() {
      const url = window.prompt("Image URL");
      if (url) this.editor.chain().focus().setImage({ src: url }).run();
    },
    save() {
      this.$emit("update:modelValue", this.editor.getHTML());
    },
    isDirty() {
      return this.editor?.getHTML() !== this.modelValue;
    },
  },
};
</script>

<style scoped>
.form-control-plaintext :deep(.ProseMirror) {
  min-height: 60px;
  outline: none;
}
.form-control-plaintext :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: #6c757d;
  pointer-events: none;
  height: 0;
}
.form-control-plaintext :deep(table) {
  border-collapse: collapse;
  width: 50%;
  margin-left: 1rem;
}
.form-control-plaintext :deep(td),
.form-control-plaintext :deep(th) {
  border: 1px solid #dee2e6;
  padding: 0.5rem;
  min-width: 3rem;
}
.form-control-plaintext :deep(th) {
  font-weight: 600;
}
.form-control-plaintext :deep(.selectedCell) {
  background-color: rgba(0, 123, 255, 0.1);
}
.color-picker {
  position: absolute;
  background: #fff;
  border: 1px solid #dee2e6;
  padding: 6px;
  border-radius: 6px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
  z-index: 9999;
}
.color-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  width: 220px;
  max-height: 220px;
  overflow-y: auto;
  padding: 4px;
}
.color-button {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  cursor: pointer;
  padding: 0;
  outline: none;
}
.color-button.selected {
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.12) inset;
  transform: scale(1.05);
}
.color-button.reset {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #000000;
  font-size: 12px;
  border: 1px dashed #cfcfcf;
}
.color-button:focus {
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.12);
}
.btn-toolbar {
  overflow-x: auto;
  gap: 0.5rem;
}
.btn-group {
  border-right: 1px solid #e5e7eb;
  padding-right: 0.5rem;
  margin-right: 0.5rem;
}
</style>
