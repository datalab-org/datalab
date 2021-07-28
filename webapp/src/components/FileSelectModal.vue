<template>
  <div class="modal-enclosure">
    <Modal v-model="fileSelectModalIsOpen">
      <template v-slot:header>
        Select files to add
        <button
          @click="fetchRemoteTree"
          :disabled="isLoadingRemoteTree"
          class="ml-4 btn btn-small btn-default"
        >
          <font-awesome-icon
            v-show="isLoadingRemoteTree"
            :icon="['fa', 'sync']"
            class="fa-spin"
          />
          Update tree
        </button>
      </template>

      <template v-slot:body>
        <SelectableFileTree
          :defaultSearchTerm="sample_id"
          @update:selectedEntries="selectedRemoteFiles = $event"
        />
      </template>

      <template v-slot:footer>
        <button
          type="button"
          class="btn btn-info"
          :disabled="isLoadingRemoteFiles || selectedRemoteFiles.length < 1"
          @click="loadSelectedRemoteFiles"
        >
          <font-awesome-icon
            v-show="isLoadingRemoteFiles"
            :icon="['fa', 'sync']"
            class="fa-spin"
          />
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

import {
  fetchRemoteTree,
  fetchCachedRemoteTree,
  addRemoteFileToSample,
} from "@/server_fetch_utils";

export default {
  data() {
    return {
      selectedRemoteFiles: [],
      isLoadingRemoteFiles: false,
    };
  },
  props: {
    sample_id: {
      type: String,
      required: true,
    },
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
  methods: {
    fetchRemoteTree: fetchRemoteTree, // imported directly from server_fetch_utils. Note: automatically sets and usets the remote tree loading status.
    async loadCachedTree() {
      var response_json = await fetchCachedRemoteTree(); // imported from server_fetch_utils. Note: automatically sets and usets the remote tree loading status.
      // What happens if the reponse is an error?
      console.log(
        `loadCachedTree received, ${response_json.seconds_since_last_update} seconds out of date:`
      );
      if (response_json.seconds_since_last_update > 3600) {
        console.log(
          "cache more than 1 hr out of date. Fetching new sample tree"
        );
        this.fetchRemoteTree();
      }
    },
    async loadSelectedRemoteFiles() {
      this.isLoadingRemoteFiles = true;
      var promises = [];
      for (let i = 0; i < this.selectedRemoteFiles.length; i++) {
        console.log("processing load from remote server for entry");
        console.log(this.selectedRemoteFiles[i]);
        promises.push(
          addRemoteFileToSample(this.selectedRemoteFiles[i], this.sample_id)
        );
      }
      await Promise.all(promises);
      this.isLoadingRemoteFiles = false;
    },
  },
  components: {
    Modal,
    SelectableFileTree,
  },
  mounted() {
    this.loadCachedTree();
  },
};
</script>

<style scoped>
.modal-enclosure >>> .modal-header {
  padding: 0.5rem 1rem;
}

.modal-enclosure >>> .modal-dialog {
  max-width: 95%;
  min-height: 95vh;
  margin-top: 2.5vh;
  margin-bottom: 2.5vh;
}

.modal-enclosure >>> .modal-content {
  height: 95vh;
  /*overflow: scroll;*/
}
</style>
