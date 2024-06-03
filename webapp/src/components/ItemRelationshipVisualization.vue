<template>
  <label class="pr-2">Relationships</label>
  <div>
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

export default {
  components: {
    ItemGraph,
  },
  props: {
    item_id: String,
  },
  computed: {
    graphData() {
      return this.$store.state.itemGraphData;
    },
  },
  async mounted() {
    await getItemGraph({ item_id: this.item_id });
  },
};
</script>
