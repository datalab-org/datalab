<template>
  <a class="nav-item nav-link" @click="handleExport"> <i class="fa fa-download"></i> Export </a>
  <ExportButton
    ref="exportButton"
    :item-id="itemId"
    :collection-id="collectionId"
    style="display: none"
  />
  <SampleGraphExportModal
    v-if="itemType !== 'collections'"
    ref="graphExportModal"
    :item-id="itemId"
  />
</template>

<script>
import ExportButton from "@/components/ExportButton";
import SampleGraphExportModal from "@/components/SampleGraphExportModal";

export default {
  name: "ExportDropdown",
  components: {
    ExportButton,
    SampleGraphExportModal,
  },
  props: {
    itemId: {
      type: String,
      default: null,
    },
    collectionId: {
      type: String,
      default: null,
    },
    itemType: {
      type: String,
      required: true,
    },
  },
  methods: {
    handleExport() {
      if (this.itemType === "collections") {
        this.$refs.exportButton.handleExport();
      } else {
        this.$refs.graphExportModal.show();
      }
    },
  },
};
</script>
