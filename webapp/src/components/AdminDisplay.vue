<template>
  <div class="admin-display">
    <template v-if="selectedItem === 'Users'"> <UserTable /> </template>
    <template v-else-if="selectedItem === 'Groups'"> <GroupTable /> </template>
  </div>
</template>

<script>
import UserTable from "./UserTable.vue";
import GroupTable from "./GroupTable.vue";

export default {
  name: "AdminDisplay",
  components: { UserTable, GroupTable },
  props: {
    selectedItem: {
      type: String,
      required: true,
    },
  },
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
