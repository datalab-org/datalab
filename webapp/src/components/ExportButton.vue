<template>
  <div class="export-button">
    <button
      :disabled="isExporting"
      class="btn btn-sm btn-outline-primary"
      :data-testid="`${exportType}-export-button`"
      @click="handleExport"
    >
      <span v-if="!isExporting"> <i class="fa fa-download"></i> Export as .eln </span>
      <span v-else> <i class="fa fa-spinner fa-spin"></i> {{ exportStatusText }} </span>
    </button>
  </div>
</template>

<script>
import {
  startCollectionExport,
  startItemExport,
  getExportStatus,
  getExportDownloadUrl,
} from "@/server_fetch_utils";
import { DialogService } from "@/services/DialogService";

export default {
  name: "ExportButton",
  props: {
    collectionId: {
      type: String,
      default: null,
    },
    itemId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      isExporting: false,
      exportStatusText: "Preparing export...",
      pollInterval: null,
    };
  },
  computed: {
    exportType() {
      return this.collectionId ? "collection" : "item";
    },
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  },
  methods: {
    async handleExport() {
      try {
        this.isExporting = true;
        this.exportStatusText = "Starting export...";

        console.log("Export - collectionId:", this.collectionId, "itemId:", this.itemId);

        let response;
        if (this.collectionId) {
          response = await startCollectionExport(this.collectionId);
        } else if (this.itemId) {
          response = await startItemExport(this.itemId);
        } else {
          throw new Error("Either collectionId or itemId must be provided");
        }

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
      this.exportStatusText = "Processing...";

      this.pollInterval = setInterval(async () => {
        try {
          const status = await getExportStatus(taskId);

          if (status.status === "ready") {
            clearInterval(this.pollInterval);
            this.downloadExport(taskId);
            this.isExporting = false;
            DialogService.alert({
              title: "Export Complete",
              message: `Your ${this.exportType} has been exported successfully.`,
              type: "info",
            });
          } else if (status.status === "error") {
            clearInterval(this.pollInterval);
            this.isExporting = false;
            DialogService.error({
              title: "Export Failed",
              message: status.error_message || "An error occurred during export.",
            });
          } else if (status.status === "processing") {
            this.exportStatusText = "Generating .eln file...";
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
  },
};
</script>
