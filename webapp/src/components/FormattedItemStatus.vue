<template>
  <span class="badge badge-pill text-uppercase" :class="badgeClass">
    {{ status }}
  </span>
</template>

<script>
export default {
  props: {
    status: { type: String, required: true },
    styleOverride: { type: String, default: null },
  },
  computed: {
    badgeClass() {
      if (this.styleOverride) {
        return `badge-${this.styleOverride}`;
      }

      const statusStyleMap = {
        // ItemStatus
        planned: "info",
        active: "success",
        completed: "primary",
        failed: "danger",

        // EquipmentStatus
        working: "success",
        broken: "danger",
        being_fixed: "warning",
        defunct: "dark",
        not_being_fixed: "secondary",

        // StartingMaterialsStatus
        ordered: "info",
        disposed: "dark",
        available: "success",
        unavailable: "danger",
      };

      return `badge-${statusStyleMap[this.status?.toLowerCase()] || "warning"}`;
    },
  },
};
</script>
