<template>
  <Navbar />
  <div class="container">
    <ItemGraph :graphData="graphData" style="height: 600px" />
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
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
    Navbar,
    ItemGraph,
  },
};
</script>
