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
          <font-awesome-icon
            v-else-if="stored_files[file_id].source_server_name != null"
            class="unlink-icon"
            v-show="true"
            :icon="['fa', 'unlink']"
          />
          <span v-if="stored_files[file_id].source_server_name != null">
            <span class="server-name">
              <font-awesome-icon :icon="['fas', 'hdd']" class="toplevel-icon" />
              {{ stored_files[file_id].source_server_name }}
            </span>
            <span class="last-updated-text">
              (updated
              {{
                formatDistance(new Date(stored_files[file_id].last_modified_remote), new Date(), {
                  addSuffix: true,
                })
              }}, last synced
              {{
                formatDistance(new Date(stored_files[file_id].last_modified), new Date(), {
                  addSuffix: true,
                })
              }})
            </span>
          </span>
          <span v-else class="last-updated-text">
            (uploaded
            {{
              formatDistance(new Date(stored_files[file_id].last_modified), new Date(), {
                addSuffix: true,
              })
            }})
          </span>
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
import { formatDistance } from "date-fns";

export default {
  data() {
    return {
      serverFileModalIsOpen: false,
    };
  },
  props: {
    item_id: String,
    file_ids: Array,
    stored_files: Object,
  },
  methods: {
    formatDistance,
    deleteFile(event, file_id) {
      console.log(`delete file button clicked!`);
      console.log(event);
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
.unlink-icon {
  margin-left: 0.4rem;
  color: #888;
  font-size: small;
}

#filearea {
  max-height: 14rem;
  padding: 0.9rem 1.25rem;
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

.server-name {
  font-family: "Andalé Mono", monospace;
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
