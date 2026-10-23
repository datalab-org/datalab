<template>
  <span class="font-weight-bold" data-testid="group-header">
    {{ label }}
    <span class="badge badge-secondary badge-pill ml-1">{{ count }}</span>
  </span>
</template>

<script>
export default {
  name: "DataTableGroupHeader",
  props: {
    label: {
      type: String,
      required: true,
    },
    // Rows in the whole group, not only on the current page.
    count: {
      type: Number,
      required: true,
    },
  },
};
</script>
