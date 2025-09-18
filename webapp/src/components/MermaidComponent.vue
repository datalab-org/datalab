<template>
  <NodeViewWrapper class="mermaid-node">
    <div ref="diagram" class="mermaid-diagram"></div>

    <div class="mermaid-actions">
      <button class="btn btn-sm btn-outline-primary" @click="startEdit">✏️ Edit</button>
      <button class="btn btn-sm btn-outline-danger" @click="deleteNode">🗑 Delete</button>
    </div>

    <div v-if="editing" class="mermaid-editor">
      <textarea v-model="draft" class="form-control"></textarea>
      <div ref="preview" class="mermaid-preview"></div>
      <div class="mt-2">
        <button class="btn btn-success btn-sm" @click="applyEdit">✅ Apply</button>
        <button class="btn btn-secondary btn-sm" @click="cancelEdit">❌ Cancel</button>
      </div>
    </div>
  </NodeViewWrapper>
</template>

<script>
import { ref, watch, onMounted } from "vue";
import { NodeViewWrapper } from "@tiptap/vue-3";
import mermaid from "mermaid";

export default {
  components: { NodeViewWrapper },
  props: {
    node: { type: Object, required: true },
    updateAttributes: { type: Function, required: true },
    deleteNode: { type: Function, required: true },
  },
  setup(props) {
    const diagram = ref(null);
    const preview = ref(null);
    const editing = ref(false);
    const draft = ref(props.node.attrs.code);

    const renderMermaid = (el, code) => {
      if (!el) return;
      el.innerHTML = code;
      try {
        mermaid.init(undefined, el);
      } catch (e) {
        console.error("Mermaid render error", e);
      }
    };

    onMounted(() => {
      renderMermaid(diagram.value, props.node.attrs.code);
    });

    watch(
      () => props.node.attrs.code,
      (newCode) => renderMermaid(diagram.value, newCode),
    );

    watch(draft, (val) => {
      if (editing.value && preview.value) {
        renderMermaid(preview.value, val);
      }
    });

    const startEdit = () => {
      draft.value = props.node.attrs.code;
      editing.value = true;
    };
    const applyEdit = () => {
      props.updateAttributes({ code: draft.value });
      editing.value = false;
    };
    const cancelEdit = () => {
      editing.value = false;
    };

    return { diagram, preview, editing, draft, startEdit, applyEdit, cancelEdit };
  },
};
</script>
