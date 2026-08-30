<template>
  <Modal v-model="isOpen" :is-large="true">
    <template #header> Insert an image from attached files </template>

    <template #body>
      <p v-if="imageFiles.length === 0" class="text-muted mb-0">
        No image files are attached to this item. Attach one to the item first, then insert it here.
      </p>
      <div v-else class="image-grid">
        <button
          v-for="file in imageFiles"
          :key="file.immutable_id"
          type="button"
          class="image-option"
          :class="{ selected: selectedId === file.immutable_id }"
          :title="file.name"
          @click="selectedId = file.immutable_id"
          @dblclick="insert"
        >
          <img :src="urlFor(file)" :alt="file.name" />
          <span class="image-name">{{ file.name }}</span>
        </button>
      </div>
    </template>

    <template #footer>
      <button type="button" class="btn btn-info" :disabled="!selectedFile" @click="insert">
        Insert
      </button>
      <button type="button" class="btn btn-secondary" @click="isOpen = false">Cancel</button>
    </template>
  </Modal>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { datalabFileUrl, isImageFileName } from "@/editor/files.js";

export default {
  components: { Modal },

  props: {
    modelValue: { type: Boolean, default: false },
    item_id: { type: String, required: true },
  },

  emits: ["update:modelValue", "select"],

  data() {
    return { selectedId: null };
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
    imageFiles() {
      const files = this.$store.state.all_item_data[this.item_id]?.files ?? [];
      return files.filter((file) => isImageFileName(file.name));
    },
    selectedFile() {
      return this.imageFiles.find((file) => file.immutable_id === this.selectedId) ?? null;
    },
  },

  watch: {
    modelValue(open) {
      if (open) {
        this.selectedId = null;
      }
    },
  },

  methods: {
    urlFor(file) {
      return datalabFileUrl(file.immutable_id, file.name);
    },
    insert() {
      if (!this.selectedFile) return;
      this.$emit("select", {
        fileId: this.selectedFile.immutable_id,
        fileName: this.selectedFile.name,
      });
      this.isOpen = false;
    },
  },
};
</script>

<style scoped>
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
  max-height: 60vh;
  overflow-y: auto;
}

.image-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem;
  background: none;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  cursor: pointer;
}

.image-option:hover {
  border-color: #adb5bd;
}

.image-option.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.image-option img {
  width: 100%;
  height: 100px;
  object-fit: contain;
}

.image-name {
  font-size: 0.75rem;
  word-break: break-all;
  text-align: center;
}
</style>
