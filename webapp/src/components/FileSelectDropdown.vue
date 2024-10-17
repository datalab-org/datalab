<template>
  <div class="form-group form-inline">
    <label class="mr-4"><b>Select a file:</b></label>
    <select class="form-control file-select-dropdown" :value="modelValue" @input="handleInput">
      <option v-for="file_id in available_file_ids" :key="file_id" :value="file_id">
        {{ all_files[file_id].name }}
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
      type: String,
      default: "",
    },
    item_id: { type: String, required: true },
    block_id: { type: String, required: true },
    extensions: {
      type: Array, // array of strings, file extensions
      default: () => [""], // show all files
    },
    updateBlockOnChange: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update:modelValue"],
  computed: {
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    available_file_ids() {
      let sample_files = this.$store.state.all_item_data[this.item_id].file_ObjectIds;
      return sample_files.filter((file_id) => {
        let filename = this.all_files[file_id].name;
        return this.extensions
          .map((extension) => filename.endsWith(extension))
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
    handleInput(event) {
      this.$emit("update:modelValue", event.target.value);
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
