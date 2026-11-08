<template>
  <Navbar />
  <div style="position: relative; min-height: 400px">
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
    <ItemGraph v-model:show-collections="showCollections" :graph-data="graphData" />
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import ItemGraph from "@/components/ItemGraph";
import { getItemGraph } from "@/server_fetch_utils.js";

export default {
  components: {
    Navbar,
    ItemGraph,
  },
  data() {
    return {
      graphData: null,
      isLoading: true,
      showCollections: false,
    };
  },
  watch: {
    showCollections() {
      this.loadGraph();
    },
  },
  mounted() {
    this.loadGraph();
  },
  methods: {
    loadGraph() {
      this.isLoading = true;
      getItemGraph({ show_collections: this.showCollections })
        .then((graphData) => {
          this.graphData = graphData;
        })
        .finally(() => {
          this.isLoading = false;
        });
    },
  },
};
</script>
