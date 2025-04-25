<template>
  <div class="file-group">
    <a @click="onDelete">
      <font-awesome-icon icon="times" fixed-width class="delete-file-button" />
    </a>
    <a class="filelink" target="_blank" :href="`${$API_URL}/files/${fileId}/${file.name}`">
      {{ file.name }}
    </a>
    <font-awesome-icon v-if="file.is_live === true" class="link-icon" :icon="['fa', 'link']" />
    <font-awesome-icon
      v-else-if="file.source_server_name != null"
      class="unlink-icon"
      :icon="['fa', 'unlink']"
    />
    <span v-if="file.source_server_name != null">
      <span class="server-name">
        <font-awesome-icon :icon="['fas', 'hdd']" class="toplevel-icon" />
        {{ file.source_server_name }}
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
</template>

<script>
import { formatDistance } from "date-fns";

export default {
  name: "FileListItem",
  props: {
    file: {
      type: Object,
      required: true,
    },
    fileId: {
      type: String,
      required: true,
    },
  },
  emits: ["deleteFileFromSample"],
  methods: {
    formatDistance,
    onDelete() {
      this.$emit("deleteFileFromSample", this.fileId);
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

.delete-file-button {
  color: #888;
  margin-right: 0.1rem;
}

.delete-file-button:hover {
  color: black;
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
