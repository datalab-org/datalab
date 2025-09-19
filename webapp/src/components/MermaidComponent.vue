<template>
  <node-view-wrapper class="mermaid-node" @click="selectNode">
    <div class="border rounded p-2 bg-light position-relative">
      <div ref="mermaidContainer" class="mermaid-render"></div>
      <div v-if="error" class="alert alert-warning mb-0 mt-2">Invalid Mermaid syntax</div>
    </div>
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper } from "@tiptap/vue-3";
import { DialogService } from "@/services/DialogService";

export default {
  components: {
    NodeViewWrapper,
  },
  props: {
    node: {
      type: Object,
      required: true,
    },
    updateAttributes: {
      type: Function,
      required: true,
    },
    selected: {
      type: Boolean,
      default: false,
    },
    editor: {
      type: Object,
      required: true,
    },
    getPos: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      error: false,
      renderId: null,
    };
  },
  watch: {
    "node.attrs.code": {
      handler() {
        this.renderDiagram();
      },
      immediate: false,
    },
  },
  mounted() {
    this.renderDiagram();
  },
  beforeUnmount() {
    if (this.renderId) {
      const element = document.getElementById(`d${this.renderId}`);
      if (element) {
        element.remove();
      }
    }
  },
  methods: {
    selectNode() {
      const pos = this.getPos();
      this.editor.chain().focus().setNodeSelection(pos).run();
    },

    async renderDiagram() {
      if (!this.$refs.mermaidContainer) return;

      const container = this.$refs.mermaidContainer;
      this.error = false;

      let attempts = 0;
      while (!window.mermaid && attempts < 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
      }

      if (!window.mermaid) {
        this.error = true;
        DialogService.error("Mermaid library not loaded");
        return;
      }

      container.innerHTML = "";

      this.renderId = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      try {
        const graphDefinition = this.node.attrs.code || "graph TD;\n  A[Start] --> B[End];";

        window.mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
        });

        const mermaidDiv = document.createElement("div");
        mermaidDiv.textContent = graphDefinition;
        container.appendChild(mermaidDiv);

        await window.mermaid.init(undefined, mermaidDiv);
      } catch (err) {
        this.error = true;
        console.error("Mermaid render error:", err);

        const errorDiv = document.createElement("div");
        errorDiv.className = "text-danger";
        errorDiv.textContent = "Error rendering diagram";
        container.appendChild(errorDiv);
      }
    },
  },
};
</script>

<style scoped>
.mermaid-node {
  margin: 0.5rem 0;
}
.mermaid-render {
  display: flex;
  justify-content: center;
  min-height: 100px;
}
.mermaid-render :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
