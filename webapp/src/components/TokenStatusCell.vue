<template>
  <span v-if="active" class="badge badge-success text-uppercase">Active</span>
  <span v-else class="badge badge-danger text-uppercase">Invalidated</span>
</template>

<script>
export default {
  name: "TokenStatusCell",
  props: {
    active: {
      type: Boolean,
      required: true,
    },
  },
};
</script>
