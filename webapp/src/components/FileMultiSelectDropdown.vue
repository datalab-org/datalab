<template>
  <div class="multi-file-selector form-group">
    <label
      ><b>{{ mainLabel }}</b></label
    >
    <div class="dual-listbox-container">
      <div class="listbox">
        <label :for="`available-${block_id}`">Available Files:</label>
        <ul
          :id="`available-${block_id}`"
          class="list-group file-list"
          role="listbox"
          aria-multiselectable="false"
        >
          <li
            v-for="fileId in availableFiles"
            :key="fileId"
            class="list-group-item list-group-item-action"
            :class="{ active: selectedAvailable === fileId }"
            role="option"
            :aria-selected="selectedAvailable === fileId"
            tabindex="0"
            @click="selectAvailable(fileId)"
            @dblclick="addSelected(fileId)"
            @keydown.enter.prevent="addSelected(fileId)"
            @keydown.space.prevent="selectAvailable(fileId)"
          >
            {{ getFileName(fileId) }}
          </li>
          <li v-if="!availableFiles.length" class="list-group-item disabled">
            No available files found.
          </li>
          <li class="list-group-item list-group-item-light small disabled mt-2">
            Accepted:
            <span v-for="(extension, index) in extensions" :key="extension">
              <span v-if="index != 0">,&thinsp;</span>
              {{ extension }}
            </span>
          </li>
        </ul>
      </div>

      <div class="action-buttons">
        <button
          class="btn btn-secondary mb-2"
          :disabled="!selectedAvailable"
          aria-label="Add selected file"
          @click="addSelected()"
        >
          &gt;
        </button>
        <button
          class="btn btn-secondary"
          :disabled="!selectedSelected"
          aria-label="Remove selected file"
          @click="removeSelected()"
        >
          &lt;
        </button>
      </div>

      <div class="listbox">
        <label :for="`selected-${block_id}`">Selected Files (Ordered):</label>
        <ul
          :id="`selected-${block_id}`"
          class="list-group file-list"
          role="listbox"
          aria-multiselectable="false"
        >
          <li
            v-for="(fileId, index) in modelValue"
            :key="fileId"
            class="list-group-item list-group-item-action"
            :class="{ active: selectedSelected === fileId }"
            role="option"
            :aria-selected="selectedSelected === fileId"
            tabindex="0"
            @click="selectSelected(fileId, index)"
            @dblclick="removeSelected(fileId)"
            @keydown.enter.prevent="removeSelected(fileId)"
            @keydown.space.prevent="selectSelected(fileId, index)"
          >
            {{ index + 1 }}. {{ getFileName(fileId) }}
            <span v-if="isLive(fileId)" class="live-indicator ml-2">
              <b>Live</b> ({{ lastModified(fileId) }})
            </span>
          </li>
          <li v-if="!modelValue.length" class="list-group-item disabled">No files selected.</li>
        </ul>
      </div>

      <div class="order-buttons">
        <button
          class="btn btn-light mb-2"
          :disabled="!canMoveUp"
          aria-label="Move selected file up"
          @click="moveUp()"
        >
          &#9650;
        </button>
        <button
          class="btn btn-light"
          :disabled="!canMoveDown"
          aria-label="Move selected file down"
          @click="moveDown()"
        >
          &#9660;
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { updateBlockFromServer } from "@/server_fetch_utils.js"; // Assuming this path is correct

export default {
  name: "MultiFileSelector",
  props: {
    modelValue: {
      // Now expects an array of file IDs
      type: Array,
      default: () => [],
    },
    item_id: { type: String, required: true },
    block_id: { type: String, required: true },
    extensions: {
      type: Array, // array of strings, file extensions
      default: () => [""], // show all files (if empty string means all)
    },
    updateBlockOnChange: {
      type: Boolean,
      default: false,
    },
    mainLabel: {
      type: String,
      default: "Select and order files:",
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      selectedAvailable: null, // ID of the highlighted file in the available list
      selectedSelected: null, // ID of the highlighted file in the selected list
      selectedSelectedIndex: -1, // Index of the highlighted file in the selected list
    };
  },
  computed: {
    all_files_map() {
      // Create a map for potentially faster lookups if the list is large
      const fileMap = new Map();
      const files = this.$store.state.all_item_data[this.item_id]?.files || [];
      files.forEach((file) => fileMap.set(file.immutable_id, file));
      return fileMap;
    },
    all_available_file_ids() {
      // All file IDs potentially available for this item
      const allIds = this.$store.state.all_item_data[this.item_id]?.file_ObjectIds || [];
      const showAll =
        this.extensions.length === 0 || (this.extensions.length === 1 && this.extensions[0] === "");

      return allIds.filter((file_id) => {
        const file = this.all_files_map.get(file_id);
        if (!file) return false; // Skip if file details not found

        if (showAll) return true; // Show all if extensions are empty or just ""

        const filename = file.name?.toLowerCase() || "";
        return this.extensions.some((extension) => filename.endsWith(extension.toLowerCase()));
      });
    },
    availableFiles() {
      // Filter out files that are already selected
      const selectedSet = new Set(this.modelValue);
      return this.all_available_file_ids.filter((id) => !selectedSet.has(id));
    },
    canMoveUp() {
      return this.selectedSelected !== null && this.selectedSelectedIndex > 0;
    },
    canMoveDown() {
      return (
        this.selectedSelected !== null && this.selectedSelectedIndex < this.modelValue.length - 1
      );
    },
  },
  methods: {
    getFileName(file_id) {
      // Use the map for lookup
      return this.all_files_map.get(file_id)?.name || `File ID ${file_id} not found`;
    },
    isLive(file_id) {
      const file = this.all_files_map.get(file_id);
      return file?.is_live || false;
    },
    lastModified(file_id) {
      const file = this.all_files_map.get(file_id);
      if (!file || !file.last_modified) return "";

      const today = new Date();
      const modifiedDate = new Date(file.last_modified);

      try {
        if (today.toLocaleDateString("en-GB") === modifiedDate.toLocaleDateString("en-GB")) {
          return modifiedDate.toLocaleTimeString("en-GB");
        }
        return modifiedDate.toLocaleDateString("en-GB");
      } catch (e) {
        console.error("Error formatting date:", e);
        return file.last_modified; // fallback
      }
    },
    selectAvailable(fileId) {
      this.selectedAvailable = fileId;
      this.selectedSelected = null; // Deselect in the other list
      this.selectedSelectedIndex = -1;
    },
    selectSelected(fileId, index) {
      this.selectedSelected = fileId;
      this.selectedSelectedIndex = index;
      this.selectedAvailable = null; // Deselect in the other list
    },
    addSelected(fileIdToAdd = null) {
      const id = fileIdToAdd || this.selectedAvailable;
      if (!id) return;

      // Create a new array to ensure reactivity
      const newSelectedFiles = [...this.modelValue, id];
      this.emitUpdate(newSelectedFiles);

      // Reset selection in available list
      this.selectedAvailable = null;
    },
    removeSelected(fileIdToRemove = null) {
      const id = fileIdToRemove || this.selectedSelected;
      if (!id) return;

      const newSelectedFiles = this.modelValue.filter((fileId) => fileId !== id);
      this.emitUpdate(newSelectedFiles);

      // Reset selection in selected list
      this.selectedSelected = null;
      this.selectedSelectedIndex = -1;
    },
    moveUp() {
      if (!this.canMoveUp) return;

      const index = this.selectedSelectedIndex;
      const newSelectedFiles = [...this.modelValue]; // Create mutable copy
      // Swap elements
      [newSelectedFiles[index], newSelectedFiles[index - 1]] = [
        newSelectedFiles[index - 1],
        newSelectedFiles[index],
      ];

      this.selectedSelectedIndex = index - 1; // Update selected index
      this.emitUpdate(newSelectedFiles);
    },
    moveDown() {
      if (!this.canMoveDown) return;

      const index = this.selectedSelectedIndex;
      const newSelectedFiles = [...this.modelValue]; // Create mutable copy
      // Swap elements
      [newSelectedFiles[index], newSelectedFiles[index + 1]] = [
        newSelectedFiles[index + 1],
        newSelectedFiles[index],
      ];

      this.selectedSelectedIndex = index + 1; // Update selected index
      this.emitUpdate(newSelectedFiles);
    },
    emitUpdate(newSelectedArray) {
      this.$emit("update:modelValue", newSelectedArray);
      if (this.updateBlockOnChange) {
        updateBlockFromServer(
          this.item_id,
          this.block_id,
          this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
        );
      }
    },
  },
};
</script>

<style scoped>
.multi-file-selector {
  /* Add styles for the overall container if needed */
}

.dual-listbox-container {
  display: flex;
  gap: 1rem; /* Space between elements */
  align-items: flex-start; /* Align tops */
}

.listbox {
  flex: 1; /* Allow listboxes to grow */
  min-width: 15rem; /* Minimum width */
}

.file-list {
  height: 150px; /* Or adjust as needed */
  overflow-y: auto;
  border: 1px solid #ced4da; /* Bootstrap-like border */
  border-radius: 0.25rem; /* Bootstrap-like border radius */
}

.list-group-item {
  cursor: pointer;
  padding: 0.5rem 0.75rem; /* Adjust padding */
  /* Ensure disabled items are not clickable */
}
.list-group-item.disabled {
  cursor: not-allowed;
  background-color: #e9ecef;
  color: #6c757d;
}
.list-group-item.active {
  /* Style for selected item (using Bootstrap's active class) */
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
}

.action-buttons,
.order-buttons {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.5rem; /* Space between buttons */
  align-self: center; /* Center vertically */
}

.order-buttons {
  margin-left: 0.5rem; /* Space from selected list */
}

/* Improve focus visibility for keyboard navigation */
.list-group-item:focus {
  outline: 2px solid #007bff;
  outline-offset: -1px;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}
.live-indicator {
  font-size: 0.8em;
  color: #28a745; /* Green color for live indicator */
  font-weight: normal;
}
</style>
