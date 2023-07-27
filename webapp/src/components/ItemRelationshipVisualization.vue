<template>
  <label class="mr-2">Relationships</label>
  <div>
    <ItemGraph
      :graphData="graphData"
      style="height: 200px; width: 100%; border: 1px solid transparent; border-radius: 5px"
      :defaultGraphStyle="'elk-stress'"
      :showOptions="false"
    />
  </div>
</template>

<script>
// import FormattedItemName from "@/components/FormattedItemName"
import ItemGraph from "@/components/ItemGraph";
import { getItemGraph } from "@/server_fetch_utils.js";

export default {
  computed: {
    graphData() {
      return this.$store.state.itemGraphData;
    },
  },
  props: {
    item_id: String,
  },
  async mounted() {
    await getItemGraph({ item_id: this.item_id });
  },
  components: {
    ItemGraph,
  },
};
</script>

<style scoped>
.nav-link {
  cursor: pointer;
}

.contents-item {
  cursor: pointer;
}

.contents-blocktype {
  font-style: italic;
  color: gray;
  margin-right: 1rem;
}

.contents-blocktitle {
  color: #004175;
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}
</style>
