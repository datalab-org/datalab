<template>
  <div class="admin-display">
    <template v-if="selectedItem === 'Users'">
      <UserTable />
    </template>
    <template v-if="selectedItem === 'Access Tokens'">
      <TokenTable />
    </template>
  </div>
</template>

<script>
import UserTable from "./UserTable.vue";
import TokenTable from "./TokenTable.vue";

export default {
  name: "AdminDisplay",
  components: {
    UserTable,
    TokenTable,
  },
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
