<template>
  <Modal v-model="isOpen" :is-large="true">
    <template #header>
      {{ isEditing ? "Edit Mermaid Diagram" : "Create Mermaid Diagram" }}
    </template>

    <template #body>
      <div class="row">
        <div class="col-md-6">
          <div class="form-group">
            <label for="mermaid-code">Mermaid Code</label>
            <textarea
              id="mermaid-code"
              v-model="localCode"
              class="form-control font-monospace"
              rows="15"
              placeholder="graph TD;
  A[Start] --> B[Process];
  B --> C[End];"
            ></textarea>
            <small class="form-text text-muted">Enter your Mermaid diagram code above</small>
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group">
            <label>Preview</label>
            <div class="border rounded p-3 bg-white overflow-auto" style="min-height: 350px">
              <div ref="previewContainer"></div>
              <div v-if="previewError" class="alert alert-danger mt-2">{{ previewError }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="!localCode.trim()"
        @click="handleSave"
      >
        {{ isEditing ? "Update Diagram" : "Insert Diagram" }}
      </button>
      <button type="button" class="btn btn-secondary" @click="handleClose">Cancel</button>
    </template>
  </Modal>
</template>

<script>
import Modal from "@/components/Modal.vue";

export default {
  components: { Modal },
  props: {
    modelValue: { type: Boolean, default: false },
    code: {
      type: String,
      default: "graph TD;\n  A[Start] --> B[Process];\n  B --> C[End];",
    },
    isEditing: { type: Boolean, default: false },
  },
  emits: ["update:modelValue", "save"],
  data() {
    return {
      localCode: "",
      previewError: null,
      debounceTimer: null,
    };
  },
  computed: {
    isOpen: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        this.localCode = this.code;
        this.$nextTick(this.renderPreview);
      }
    },
    localCode() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(this.renderPreview, 300);
    },
  },
  beforeUnmount() {
    clearTimeout(this.debounceTimer);
  },
  methods: {
    async renderPreview() {
      if (!this.$refs.previewContainer || !this.localCode.trim()) return;

      const container = this.$refs.previewContainer;
      container.innerHTML = "";
      this.previewError = null;

      let attempts = 0;
      while (!window.mermaid && attempts < 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
      }

      if (!window.mermaid) {
        this.previewError = "Mermaid library not loaded";
        return;
      }

      try {
        if (!window.mermaid._initialized) {
          window.mermaid.initialize({
            startOnLoad: false,
            theme: "default",
            securityLevel: "sandbox",
          });
          window.mermaid._initialized = true;
        }

        const div = document.createElement("div");
        div.textContent = this.localCode;
        container.appendChild(div);

        await window.mermaid.init(undefined, div);
      } catch {
        this.previewError = "Invalid Mermaid syntax - check your code";
      }
    },
    handleSave() {
      if (this.localCode.trim()) {
        this.$emit("save", this.localCode);
        this.isOpen = false;
      }
    },
    handleClose() {
      this.isOpen = false;
    },
  },
};
</script>
