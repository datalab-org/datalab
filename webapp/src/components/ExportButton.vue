<template>
  <div class="export-button">
    <button
      :disabled="isExporting"
      class="btn btn-sm btn-outline-primary"
      :data-testid="`${exportType}-export-button`"
      @click="handleExport"
    >
      <span v-if="!isExporting"> <i class="fa fa-download"></i> Export as .eln </span>
      <span v-else> <i class="fa fa-spinner fa-spin"></i> Exporting&hellip; </span>
    </button>
    <ExportProgressModal
      ref="progressModal"
      :export-type="exportType"
      @close="isExporting = false"
    />
  </div>
</template>

<script>
import { startCollectionExport, startItemExport } from "@/server_fetch_utils";
import { DialogService } from "@/services/DialogService";
import ExportProgressModal from "@/components/ExportProgressModal";

export default {
  name: "ExportButton",
  components: {
    ExportProgressModal,
  },
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
    };
  },
  computed: {
    exportType() {
      return this.collectionId ? "collection" : "item";
    },
  },
  methods: {
    async handleExport() {
      if (this.isExporting) {
        return;
      }
      try {
        this.isExporting = true;

        let response;
        if (this.collectionId) {
          response = await startCollectionExport(this.collectionId);
        } else if (this.itemId) {
          response = await startItemExport(this.itemId);
        } else {
          throw new Error("Either collectionId or itemId must be provided");
        }

        this.$refs.progressModal.start(response.task_id);
      } catch (error) {
        console.error("Export failed:", error);
        this.isExporting = false;
        DialogService.error({
          title: "Export Failed",
          message: error.message || "Failed to start the export. Please try again.",
        });
      }
    },
  },
};
</script>
