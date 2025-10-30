<template>
  <Modal v-model="isModalOpen" :is-large="true">
    <template #header>Export Sample and Related Items</template>

    <template #body>
      <div v-if="isLoading" class="text-center">
        <i class="fa fa-spinner fa-spin fa-2x"></i>
        <p class="mt-2">Loading related samples...</p>
      </div>
      <div v-else-if="relatedSamples.length === 0">
        <p>No related samples found for this item.</p>
      </div>
      <div v-else>
        <p>Select the samples you want to include in the export:</p>
        <div class="form-check">
          <input
            id="select-all"
            v-model="selectAll"
            type="checkbox"
            class="form-check-input"
            @change="toggleSelectAll"
          />
          <label class="form-check-label" for="select-all">
            <strong>Select All</strong>
          </label>
        </div>
        <hr />
        <div v-for="sample in relatedSamples" :key="sample.id" class="form-check">
          <input
            :id="`sample-${sample.id}`"
            v-model="selectedSampleIds"
            type="checkbox"
            class="form-check-input"
            :value="sample.id"
          />
          <label class="form-check-label" :for="`sample-${sample.id}`">
            {{ sample.name }} ({{ sample.id }})
            <span v-if="sample.type" class="badge badge-secondary ml-2">
              {{ sample.type }}
            </span>
          </label>
        </div>
        <hr />
        <div class="form-check">
          <input
            id="create-collection"
            v-model="createCollection"
            type="checkbox"
            class="form-check-input"
          />
          <label class="form-check-label" for="create-collection">
            <strong>Create a collection from selected samples</strong>
          </label>
        </div>
        <div v-if="createCollection" class="mt-3">
          <div class="form-group">
            <label for="collection-id">Collection ID</label>
            <input
              id="collection-id"
              v-model="collectionId"
              type="text"
              class="form-control"
              placeholder="Enter collection ID"
            />
          </div>
          <div class="form-group">
            <label for="collection-title">Collection Title</label>
            <input
              id="collection-title"
              v-model="collectionTitle"
              type="text"
              class="form-control"
              placeholder="Enter collection title"
            />
          </div>
        </div>
      </div>
    </template>

    <template #footer>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="
          isExporting ||
          selectedSampleIds.length === 0 ||
          (createCollection && (!collectionId || !collectionTitle))
        "
        @click="handleExport"
      >
        <span v-if="!isExporting">
          <i class="fa fa-download"></i> Export Selected ({{ selectedSampleIds.length }})
        </span>
        <span v-else> <i class="fa fa-spinner fa-spin"></i> Exporting... </span>
      </button>
      <button type="button" class="btn btn-secondary" @click="isModalOpen = false">Cancel</button>
    </template>
  </Modal>
</template>

<script>
import Modal from "@/components/Modal";
import {
  getItemGraph,
  startSampleExport,
  getExportStatus,
  getExportDownloadUrl,
  createNewCollection,
} from "@/server_fetch_utils";
import { DialogService } from "@/services/DialogService";

export default {
  name: "SampleGraphExportModal",
  components: {
    Modal,
  },
  props: {
    itemId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isModalOpen: false,
      isLoading: false,
      isExporting: false,
      relatedSamples: [],
      selectedSampleIds: [],
      selectAll: false,
      pollInterval: null,
      createCollection: false,
      collectionId: "",
      collectionTitle: "",
    };
  },
  watch: {
    isModalOpen(newValue) {
      if (newValue) {
        this.loadRelatedSamples();
      } else {
        this.relatedSamples = [];
        this.selectedSampleIds = [];
      }
    },
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  },
  methods: {
    async loadRelatedSamples() {
      try {
        this.isLoading = true;
        const graphData = await getItemGraph({ item_id: this.itemId });

        this.relatedSamples = graphData.nodes
          .filter((node) => node.data.id !== this.itemId)
          .map((node) => ({
            id: node.data.id,
            name: node.data.name || node.data.id,
            type: node.data.type,
          }));

        this.selectedSampleIds = this.relatedSamples.map((s) => s.id);
        this.selectAll = true;
        this.createCollection = false;
        this.collectionId = `${this.itemId}-collection`;
        this.collectionTitle = `${this.itemId} and related samples`;
      } catch (error) {
        console.error("Failed to load related samples:", error);
        DialogService.error({
          title: "Loading Failed",
          message: "Failed to load related samples. Please try again.",
        });
      } finally {
        this.isLoading = false;
      }
    },

    toggleSelectAll() {
      if (this.selectAll) {
        this.selectedSampleIds = this.relatedSamples.map((s) => s.id);
      } else {
        this.selectedSampleIds = [];
      }
    },

    async handleExport() {
      try {
        this.isExporting = true;

        if (this.createCollection) {
          if (!this.collectionId.trim() || !this.collectionTitle.trim()) {
            DialogService.error({
              title: "Validation Error",
              message: "Please enter both collection ID and title.",
            });
            this.isExporting = false;
            return;
          }

          try {
            const startingMembers = [
              { item_id: this.itemId },
              ...this.selectedSampleIds.map((id) => ({ item_id: id })),
            ];

            await createNewCollection(this.collectionId, this.collectionTitle, {
              starting_members: startingMembers,
            });

            DialogService.alert({
              title: "Collection Created",
              message: `Collection "${this.collectionTitle}" created successfully with ${startingMembers.length} items.`,
              type: "info",
            });
          } catch (error) {
            console.error("Failed to create collection:", error);
            DialogService.error({
              title: "Collection Creation Failed",
              message: "Failed to create collection. Continuing with export...",
            });
          }
        }

        const response = await startSampleExport(this.itemId, {
          include_related: true,
          related_item_ids: this.selectedSampleIds,
        });
        const taskId = response.task_id;

        this.pollExportStatus(taskId);
      } catch (error) {
        console.error("Export failed:", error);
        this.isExporting = false;
        DialogService.error({
          title: "Export Failed",
          message: error.message || "Failed to start the export. Please try again.",
        });
      }
    },

    async pollExportStatus(taskId) {
      this.pollInterval = setInterval(async () => {
        try {
          const status = await getExportStatus(taskId);

          if (status.status === "ready") {
            clearInterval(this.pollInterval);
            this.downloadExport(taskId);
            this.isExporting = false;
            this.isModalOpen = false;
            DialogService.alert({
              title: "Export Complete",
              message: "Your samples have been exported successfully.",
              type: "info",
            });
          } else if (status.status === "error") {
            clearInterval(this.pollInterval);
            this.isExporting = false;
            DialogService.error({
              title: "Export Failed",
              message: status.error_message || "An error occurred during export.",
            });
          }
        } catch (error) {
          clearInterval(this.pollInterval);
          this.isExporting = false;
          console.error("Error polling export status:", error);
        }
      }, 2000);
    },

    downloadExport(taskId) {
      const downloadUrl = getExportDownloadUrl(taskId);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.style.display = "none";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    show() {
      this.isModalOpen = true;
    },
  },
};
</script>
