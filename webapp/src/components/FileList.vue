<template>
  <div class="container">
    <label class="mr-2">Files</label>
    <div class="card">
      <div class="card-body overflow-auto" id="filearea">
        <div class="file-group" v-for="file_id in file_ids" :key="file_id">
          <a @click="deleteFile($event, file_id)">
            <font-awesome-icon icon="times" fixed-width class="delete-file-button" />
          </a>
          <a
            class="filelink"
            target="_blank"
            :href="`${$API_URL}/files/${file_id}/${stored_files[file_id].name}`"
          >
            {{ stored_files[file_id].name }}
          </a>
          <font-awesome-icon
            v-if="stored_files[file_id].is_live == true"
            class="link-icon"
            v-show="true"
            :icon="['fa', 'link']"
          />
        </div>
      </div>
      <div class="row">
        <button id="uppy-trigger" class="btn btn-default btn-sm mb-3 ml-4" type="button">
          Upload files...</button
        ><!-- Surrounding divs so that buttons  don't become full-width in the card -->
        <button
          class="btn btn-default btn-sm mb-3 ml-2"
          type="button"
          @click="setFileSelectModalOpen"
        >
          Add files from server...
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { deleteFileFromSample } from "@/server_fetch_utils";

export default {
  data() {
    return {
      serverFileModalIsOpen: false,
    };
  },
  props: {
    sample_id: String,
    file_ids: Array,
    stored_files: Object,
  },
  methods: {
    deleteFile(event, file_id) {
      console.log(`delete file button clicked!`);
      console.log(event);
      deleteFileFromSample(this.sample_id, file_id);
      return false;
    },
    setFileSelectModalOpen() {
      this.$store.commit("setFileSelectModalOpenStatus", true);
    },
  },
};
</script>

<style scoped>
.file-group {
  padding: 0.25rem 0rem;
}

.filelink {
  color: #004175;
}

.filelink:hover {
  text-decoration: none;
}

.link-icon {
  margin-left: 0.4rem;
  color: #888;
  font-size: small;
}
</style>
