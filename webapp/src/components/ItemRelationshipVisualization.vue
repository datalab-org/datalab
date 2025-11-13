<template>
  <FieldLabelDescriptionTooltip html-for="item-relationships" :description="description">
    <font-awesome-icon icon="project-diagram" /> Relationships
  </FieldLabelDescriptionTooltip>
  <div style="position: relative">
    <div
      v-if="isLoading"
      class="position-absolute w-100 h-100 top-0 start-0 d-flex justify-content-center align-items-center"
      style="background-color: rgba(255, 255, 255, 0.7); z-index: 100"
    >
      <div class="card p-3 shadow-sm">
        <div class="text-center">
          <font-awesome-icon
            :icon="['fa', 'sync']"
            class="fa-2x text-primary mb-2"
            :spin="true"
            aria-label="loading"
          />
          <p class="mb-0 fw-medium">Loading graph...</p>
        </div>
      </div>
    </div>
    <ItemGraph
      :graph-data="graphData"
      style="height: 200px; width: 100%; border: 1px solid transparent; border-radius: 5px"
      :default-graph-style="'elk-stress'"
      :show-options="false"
    />
  </div>
</template>

<script>
// import FormattedItemName from "@/components/FormattedItemName"
import ItemGraph from "@/components/ItemGraph";
import { getItemGraph } from "@/server_fetch_utils.js";
import FieldLabelDescriptionTooltip from "@/components/FieldLabelDescriptionTooltip";

export default {
  components: {
    ItemGraph,
    FieldLabelDescriptionTooltip,
  },
  props: {
    item_id: { type: String, required: true },
    description: {
      type: String,
      default: null,
    },
  },
  computed: {
    graphData() {
      return this.$store.state.itemGraphData;
    },
    isLoading() {
      return this.$store.state.itemGraphIsLoading;
    },
  },
  mounted() {
    getItemGraph({ item_id: this.item_id });
  },
};
</script>
