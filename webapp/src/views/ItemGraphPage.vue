<template>
  <Navbar />
  <ItemGraph :graph-data="graphData" />
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
};
</script>
