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
  width: 100%;
  padding: 1em;
  margin: 0.5em;
  border: 1px solid lightgray;
  border-radius: 0.5em;
}
</style>
