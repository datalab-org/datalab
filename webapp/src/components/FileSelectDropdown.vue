<template>
  <div class="form-inline">
    <div class="form-group">
      <label class="mr-4"><b>Select a file:</b></label>
      <select class="form-control" :value="modelValue" @input="handleInput">
        <option
          v-for="file_id in available_file_ids"
          :key="file_id"
          :value="file_id"
        >
          {{ all_files[file_id].name }}
        </option>
      </select>

      <span
        v-if="all_files[modelValue] && all_files[modelValue].is_live"
        class="ml-2"
      >
        <b>Live</b> (last updated: {{ lastModified }})
      </span>
    </div>
  </div>
</template>

<script>
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  props: {
    modelValue: String,
    sample_id: String,
    block_id: String,
    extensions: {
      type: Array, // array of strings, file extensions
      default: () => [""], // show all files
    },
    updateBlockOnChange: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    all_files() {
      return this.$store.state.files;
    },
    available_file_ids() {
      let sample_files =
        this.$store.state.all_sample_data[this.sample_id].file_ObjectIds;
      return sample_files.filter((file_id) => {
        let filename = this.all_files[file_id].name;
        return this.extensions
          .map((extension) => filename.endsWith(extension))
          .some((element) => element); // check if the extension is any of the extensions
      });
    },
    lastModified() {
      const today = new Date();
      const modifiedDate = new Date(
        this.all_files[this.modelValue].last_modified
      );

      if (
        today.toLocaleDateString("en-GB") ==
        modifiedDate.toLocaleDateString("en-GB")
      ) {
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
          this.sample_id,
          this.block_id,
          this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][
            this.block_id
          ]
        );
      }
    },
  },
};
</script>
