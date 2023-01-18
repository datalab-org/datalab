<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link> |
    <router-link to="/item-graph">Item graph</router-link>
  </div>

  <itemGraph />
</template>

<script>
import itemGraph from "@/components/itemGraph";
export default {
  components: {
    itemGraph,
  },
};
</script>
