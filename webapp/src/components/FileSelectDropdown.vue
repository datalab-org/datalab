<template>
  <div class="form-group form-inline">
    <label class="mr-4"><b>Select a file:</b></label>
    <select class="form-control file-select-dropdown" :value="localModelValue" @input="handleInput">
      <option v-if="defaultToAllFiles" value="null">All compatible files</option>
      <option v-for="file_id in available_file_ids" :key="file_id" :value="file_id">
        {{ all_files_name(file_id) }}
      </option>
      <option disabled>
        Accepted filetypes:
        <span v-for="(extension, index) in extensions" :key="extension">
          <span v-if="index != 0">,&thinsp;</span>
          {{ extension }}
        </span>
      </option>
    </select>

    <span v-if="all_files[modelValue] && all_files[modelValue].is_live" class="ml-2">
      <b>Live</b> (last updated: {{ lastModified }})
    </span>
  </div>
</template>

<script>
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  props: {
    modelValue: {
      default: null,
      type: String,
    },
    item_id: { type: String, required: true },
    block_id: { type: String, required: true },
    extensions: {
      type: Array, // array of strings, file extensions
      default: () => [""], // show all files
    },
    defaultToAllFiles: {
      // Whether to have the default option be "all files"
      type: Boolean,
      default: false,
    },
    updateBlockOnChange: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update:modelValue"],
  computed: {
    localModelValue() {
      // Handle stringification of modelValue in cases where it needs to be 'null' or otherwise
      return this.modelValue === null ? "null" : String(this.modelValue);
    },
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    available_file_ids() {
      let sample_files = this.$store.state.all_item_data[this.item_id].file_ObjectIds;
      return sample_files.filter((file_id) => {
        let filename = this.all_files_name(file_id).toLowerCase();
        return this.extensions
          .map((extension) => filename?.endsWith(extension))
          .some((element) => element); // check if the extension is any of the extensions
      });
    },
    lastModified() {
      const today = new Date();
      const modifiedDate = new Date(this.all_files[this.modelValue].last_modified);

      if (today.toLocaleDateString("en-GB") == modifiedDate.toLocaleDateString("en-GB")) {
        return modifiedDate.toLocaleTimeString("en-GB");
      }
      return modifiedDate.toLocaleDateString("en-GB");
    },
  },
  methods: {
    all_files_name(file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.name || "File not found";
    },
    handleInput(event) {
      let event_value = event.target.value;
      if (event_value === "null") {
        event_value = null;
      }
      this.$emit("update:modelValue", event_value);
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
.file-select-dropdown {
  min-width: 20rem;
}
</style>
