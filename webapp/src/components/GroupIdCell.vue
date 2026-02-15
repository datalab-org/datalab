<template>
  <span class="badge badge-light table-group-id">{{ groupId }}</span>
</template>

<script>
export default {
  name: "GroupIdCell",
  props: {
    groupId: {
      type: String,
      required: true,
    },
  },
};
</script>

<style scoped>
.table-group-id {
  border: 2px solid #ccc;
  font-family: var(--font-monospace);
}
</style>
