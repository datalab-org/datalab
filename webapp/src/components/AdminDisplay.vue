<template>
  <div class="admin-display">
    <template v-if="selectedItem === 'Users'"> <UserTable /> </template>
  </div>
</template>

<script>
import UserTable from "./UserTable.vue";

export default {
  components: { UserTable },
  props: ["selectedItem"],
  name: "AdminDisplay",
};
</script>

<style scoped>
.admin-display {
  max-width: 100%;
  min-width: 80%;
  padding: 1em;
  margin: 0.5em;
}
</style>
