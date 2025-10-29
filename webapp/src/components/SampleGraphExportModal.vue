<template>
  <div ref="modalElement" class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Export Sample and Related Items</h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
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
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="isExporting || selectedSampleIds.length === 0"
            @click="handleExport"
          >
            <span v-if="!isExporting">
              <i class="fa fa-download"></i> Export Selected ({{ selectedSampleIds.length }})
            </span>
            <span v-else> <i class="fa fa-spinner fa-spin"></i> Exporting... </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getItemGraph,
  startSampleExport,
  getExportStatus,
  getExportDownloadUrl,
} from "@/server_fetch_utils";
import { DialogService } from "@/services/DialogService";

export default {
  name: "SampleGraphExportModal",
  props: {
    itemId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isLoading: false,
      isExporting: false,
      relatedSamples: [],
      selectedSampleIds: [],
      selectAll: false,
      pollInterval: null,
      modalInstance: null,
    };
  },
  mounted() {
    this.modalInstance = new window.bootstrap.Modal(this.$refs.modalElement);
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
    if (this.modalInstance) {
      this.modalInstance.dispose();
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
            this.modalInstance.hide();
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
      this.modalInstance.show();
      this.loadRelatedSamples();
    },
  },
};
</script>
