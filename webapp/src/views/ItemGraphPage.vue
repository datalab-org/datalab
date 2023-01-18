<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link> |
    <router-link to="/item-graph">Item graph</router-link>
  </div>
  <ItemGraph style="height: 600px" />
</template>

<script>
import ItemGraph from "@/components/ItemGraph.vue";
export default {
  components: {
    ItemGraph,
  },
};
</script>
