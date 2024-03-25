<template>
  <div class="admin-display">
    <template v-if="selectedItem === 'Users'"> User </template>
    <template v-else-if="selectedItem === 'Collections'"> <CollectionTable /> </template>
    <template v-else-if="selectedItem === 'Samples'"> <SampleTable /> </template>
  </div>
</template>

<script>
import CollectionTable from "./CollectionTable.vue";
import SampleTable from "./SampleTable.vue";
export default {
  components: { CollectionTable, SampleTable },
  props: ["selectedItem"],
  name: "AdminDisplay",
};
</script>

<style scoped>
.admin-display {
  width: 100%;
  padding: 1em;
  margin: 0.5em;
  border: 1px solid lightgray;
  border-radius: 0.5em;
}
</style>
