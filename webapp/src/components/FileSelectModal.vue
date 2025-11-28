<template>
  <div class="modal-enclosure">
    <Modal v-model="fileSelectModalIsOpen">
      <template #header>
        Select files to add
        <button
          :disabled="isLoadingRemoteTree"
          class="ml-4 btn btn-small btn-default"
          @click="fetchRemoteTree"
        >
          <font-awesome-icon v-show="isLoadingRemoteTree" :icon="['fa', 'sync']" class="fa-spin" />
          Update tree
        </button>
      </template>

      <template #body>
        <SelectableFileTree
          :default-search-term="item_id"
          @update:selected-entries="selectedRemoteFiles = $event"
        />
      </template>

      <template #footer>
        <button
          type="button"
          class="btn btn-info"
          :disabled="isLoadingRemoteFiles || selectedRemoteFiles.length < 1"
          @click="loadSelectedRemoteFiles"
        >
          <font-awesome-icon v-show="isLoadingRemoteFiles" :icon="['fa', 'sync']" class="fa-spin" />
          {{ loadFilesButtonValue }}
        </button>
        <button
          type="button"
          class="btn btn-secondary"
          data-dismiss="modal"
          @click="fileSelectModalIsOpen = false"
        >
          Close
        </button>
      </template>
    </Modal>
  </div>
</template>

<script>
import Modal from "@/components/Modal";
import SelectableFileTree from "@/components/SelectableFileTree";

import { fetchRemoteTree, addRemoteFileToSample } from "@/server_fetch_utils";

export default {
  components: {
    Modal,
    SelectableFileTree,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      selectedRemoteFiles: [],
      isLoadingRemoteFiles: false,
    };
  },
  computed: {
    isLoadingRemoteTree() {
      return this.$store.state.remoteDirectoryTreeIsLoading;
    },
    // Change the text on the load files button based for singular/plural file uploads
    loadFilesButtonValue() {
      const len = this.selectedRemoteFiles.length;
      if (len == 1) {
        return "Load 1 file";
      }
      if (len > 1) {
        return `Load ${len} files`;
      }
      return "Load files";
    },
    // A computed setter to 2-way fileSelectModalisOpen to the vuex store property
    fileSelectModalIsOpen: {
      get() {
        return this.$store.state.fileSelectModalIsOpen;
      },
      set(value) {
        this.$store.commit("setFileSelectModalOpenStatus", value);
      },
    },
  },
  mounted() {
    this.loadCachedTree();
  },
  methods: {
    fetchRemoteTree: fetchRemoteTree, // imported directly from server_fetch_utils. Note: automatically sets and usets the remote tree loading status.
    async loadCachedTree() {
      var response_json = await fetchRemoteTree(false);
      if (!response_json) {
        return;
      }
      var oldest_cache_update = null;
      var seconds_since_oldest_update = null;
      if ("meta" in response_json) {
        if ("oldest_cache_update" in response_json.meta) {
          oldest_cache_update = new Date(response_json.meta.oldest_cache_update + "Z");
          seconds_since_oldest_update = (new Date() - oldest_cache_update) / 1000;
          console.log(
            `loadCachedTree received, oldest dir update was ${seconds_since_oldest_update} s ago`,
          );
        }
      }

      if (seconds_since_oldest_update == null || seconds_since_oldest_update > 3600) {
        console.log("cache is probably more than 1 hr out of date. Fetching new sample tree");
        this.fetchRemoteTree(true);
      }
    },
    async loadSelectedRemoteFiles() {
      this.isLoadingRemoteFiles = true;
      var promises = [];
      for (let i = 0; i < this.selectedRemoteFiles.length; i++) {
        console.log("processing load from remote server for entry");
        console.log(this.selectedRemoteFiles[i]);
        promises.push(addRemoteFileToSample(this.selectedRemoteFiles[i], this.item_id));
      }
      await Promise.all(promises);
      this.isLoadingRemoteFiles = false;
    },
  },
};
</script>

<style scoped>
.modal-enclosure :deep(.modal-header) {
  padding: 0.5rem 1rem;
}

.modal-enclosure :deep(.modal-dialog) {
  max-width: 95%;
  min-height: 95vh;
  margin-top: 2.5vh;
  margin-bottom: 2.5vh;
}

.modal-enclosure :deep(.modal-content) {
  height: 95vh;
  /*overflow: scroll;*/
}
</style>
