<template>
  <div class="container">
    <label class="mr-2">Files</label>
    <div class="card">
      <div id="filearea" class="card-body overflow-auto">
        <FileListItem
          v-for="(file, file_id) in stored_files"
          :key="file_id"
          :file="file"
          :file-id="file_id"
          @delete-file-from-sample="deleteFile"
        />
      </div>
      <div class="row">
        <button
          id="uppy-trigger"
          class="btn btn-default btn-sm mb-3 ml-4 text-start d-flex align-items-center"
          type="button"
        >
          <font-awesome-icon class="upload-icon" icon="file" fixed-width />
          <span class="ms-1">Upload files</span>
        </button>
        <button
          class="btn btn-default btn-sm mb-3 ml-2 text-start d-flex align-items-center"
          type="button"
          @click="setFileSelectModalOpen"
        >
          <font-awesome-icon class="remote-upload-icon" icon="cloud-upload-alt" fixed-width />
          <span class="ms-1">Add files from server</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import FileListItem from "./FileListItem.vue";
import { deleteFileFromSample } from "@/server_fetch_utils";

export default {
  components: {
    FileListItem,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    stored_files: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      serverFileModalIsOpen: false,
    };
  },
  methods: {
    deleteFile(file_id) {
      deleteFileFromSample(this.item_id, file_id);
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
  font-family: "Andalé Mono", monospace;
}

.filelink:hover {
  text-decoration: none;
}

.link-icon,
.unlink-icon,
.upload-icon,
.remote-upload-icon {
  margin-left: 0.2rem;
  margin-right: 0.2rem;
  color: #888;
  font-size: small;
}

#filearea {
  max-height: 14rem;
  padding: 0.9rem 1.25rem;
}

#uppy-trigger {
  scroll-anchor: auto;
}
</style>
