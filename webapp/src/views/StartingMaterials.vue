<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link>
  </div>
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <StartingMaterialTable></StartingMaterialTable>
      </div>
    </div>
  </div>
</template>

<script>
import StartingMaterialTable from "@/components/StartingMaterialTable.vue";

export default {
  components: {
    StartingMaterialTable,
  },
};
</script>
