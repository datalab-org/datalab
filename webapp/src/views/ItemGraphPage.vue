<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link> |
    <router-link to="/item-graph">Item graph</router-link>
  </div>

  <div class="container">
    <ItemGraph :graphData="graphData" style="height: 600px" />
  </div>
</template>

<script>
import ItemGraph from "@/components/ItemGraph";
import { getItemGraph } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      isLoaded: false,
    };
  },
  computed: {
    graphData() {
      return this.$store.state.itemGraphData;
    },
  },
  async mounted() {
    await getItemGraph();
  },
  components: {
    ItemGraph,
  },
};
</script>
