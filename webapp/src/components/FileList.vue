<template>
  <div class="container">
    <label class="mr-2">Files</label>
    <div class="card">
      <div id="filearea" class="card-body overflow-auto">
        <div v-for="(file, file_id) in stored_files" :key="file_id" class="file-group">
          <a @click="deleteFile($event, file_id)">
            <font-awesome-icon icon="times" fixed-width class="delete-file-button" />
          </a>
          <a class="filelink" target="_blank" :href="getFileUrl(file_id, file.name)">
            {{ file.name }}
          </a>
          <span v-if="getFileSize(file)" class="file-size">
            ({{ formatFileSize(getFileSize(file)) }})
          </span>

          <font-awesome-icon
            v-if="file.is_live == true"
            v-show="true"
            class="link-icon"
            :icon="['fa', 'link']"
          />
          <font-awesome-icon
            v-else-if="file.source_server_name != null"
            v-show="true"
            class="unlink-icon"
            :icon="['fa', 'unlink']"
          />
          <span v-if="file.source_server_name != null">
            <span class="server-name">
              <font-awesome-icon :icon="['fas', 'hdd']" class="toplevel-icon" />
              {{ file.source_server_name }}
            </span>
            <span v-if="getFileSize(file)" class="file-size">
              ({{ formatFileSize(getFileSize(file)) }})
            </span>

            <span class="last-updated-text">
              (updated
              {{
                formatDistance(new Date(file.last_modified_remote), new Date(), {
                  addSuffix: true,
                })
              }}, last synced
              {{
                formatDistance(new Date(file.last_modified), new Date(), {
                  addSuffix: true,
                })
              }})
            </span>
          </span>
          <span v-else class="last-updated-text">
            (uploaded
            {{
              formatDistance(new Date(file.last_modified), new Date(), {
                addSuffix: true,
              })
            }})
          </span>
        </div>
      </div>
      <div class="row">
        <button id="uppy-trigger" class="btn btn-default btn-sm mb-3 ml-4" type="button">
          <font-awesome-icon class="upload-icon" icon="file" fixed-width />
          Upload files...</button
        ><!-- Surrounding divs so that buttons  don't become full-width in the card -->
        <button
          class="btn btn-default btn-sm mb-3 ml-2"
          type="button"
          @click="setFileSelectModalOpen"
        >
          <font-awesome-icon class="remote-upload-icon" icon="cloud-upload-alt" fixed-width />
          Add files from server...
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import { deleteFileFromSample } from "@/server_fetch_utils";
import { formatDistance } from "date-fns";

export default {
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
  computed: {
    adminSuperUserMode() {
      return this.$store.state.adminSuperUserMode;
    },
  },
  methods: {
    getFileUrl(file_id, filename) {
      const baseUrl = `${this.$API_URL}/files/${file_id}/${filename}`;
      return this.adminSuperUserMode ? `${baseUrl}?sudo=1` : baseUrl;
    },
    formatDistance,
    getFileSize(file) {
      return file.size;
    },
    formatFileSize(size_bytes) {
      if (size_bytes < 1024) return `${size_bytes} B`;
      if (size_bytes < 1024 * 1024) return `${(size_bytes / 1024).toFixed(1)} KB`;
      if (size_bytes < 1024 * 1024 * 1024) return `${(size_bytes / 1024 / 1024).toFixed(1)} MB`;
      return `${(size_bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
    },
    async deleteFile(event, file_id) {
      const confirmed = await DialogService.confirm({
        title: "Unlink File",
        message: "Are you sure you want to unlink this file from this entry?",
        type: "warning",
      });
      if (confirmed) {
        deleteFileFromSample(this.item_id, file_id);
      }
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
  font-family: var(--font-monospace);
}

.filelink:hover {
  text-decoration: none;
}

.link-icon,
.unlink-icon,
.upload-icon,
.remote-upload-icon {
  margin-left: 0.4rem;
  color: #888;
  font-size: small;
}

#filearea {
  max-height: 14rem;
  padding: 0.9rem 1.25rem;
}

.delete-file-button:hover {
  color: #dc3545;
  cursor: pointer;
}

#uppy-trigger {
  scroll-anchor: auto;
  width: 8rem;
}

.last-updated-text {
  font-size: 0.8em;
  color: #888;
  font-style: italic;
  vertical-align: middle;
}
.file-size {
  color: #888;
  font-size: 0.8em;
  margin-left: 0.25rem;
}

.server-name {
  font-family: var(--font-monospace);
  font-weight: 400;
  /*font-style: italic;*/
  color: teal;
  border: solid 1px teal;
  padding: 0.1rem 0.25rem;
  margin-left: 0.5rem;
  border-radius: 0.2rem;
  font-size: 0.8em;
}
</style>
