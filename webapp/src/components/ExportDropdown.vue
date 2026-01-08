<template>
  <div class="nav-item dropdown">
    <a
      class="nav-link dropdown-toggle"
      role="button"
      data-toggle="dropdown"
      aria-haspopup="true"
      aria-expanded="false"
      @click="isDropdownVisible = !isDropdownVisible"
    >
      <i class="fa fa-download"></i> Export
    </a>
    <div v-show="isDropdownVisible" class="dropdown-menu" style="display: block">
      <a class="dropdown-item" @click="handleSimpleExport">
        <i class="fa fa-file"></i> Export {{ itemType === "collections" ? "collection" : "item" }}
      </a>
      <a v-if="itemType !== 'collections'" class="dropdown-item" @click="handleGraphExport">
        <i class="fa fa-project-diagram"></i> Export with related items
      </a>
    </div>
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
  </div>
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
  data() {
    return {
      isDropdownVisible: false,
    };
  },
  methods: {
    handleSimpleExport() {
      this.isDropdownVisible = false;
      this.$refs.exportButton.handleExport();
    },
    handleGraphExport() {
      this.isDropdownVisible = false;
      this.$refs.graphExportModal.show();
    },
  },
};
</script>

<style scoped>
.dropdown-item {
  cursor: pointer;
}
</style>
