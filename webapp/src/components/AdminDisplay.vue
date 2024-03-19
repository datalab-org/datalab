<template>
  <div class="admin-display">
    <!-- Afficher le contenu basé sur la valeur de selectedItem -->
    <template v-if="selectedItem === 'User'"> User </template>
    <template v-else-if="selectedItem === 'Collection'"> <CollectionTable /> </template>
    <template v-else-if="selectedItem === 'Sample'"> <SampleTable /> </template>
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
  padding: 1em;
  margin: 0.5em;
  border: 1px solid lightgray;
  border-radius: 0.5em;
}
</style>
