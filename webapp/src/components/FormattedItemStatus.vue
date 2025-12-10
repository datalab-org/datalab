<template>
  <span v-if="alt" class="dot" :title="status" :class="'badge-' + badgeClass"></span>
  <span v-else class="badge badge-pill text-uppercase" :class="'badge-' + badgeClass">
    {{ status }}
  </span>
</template>

<script>
export default {
  props: {
    status: { type: String, required: false },
    alt: { type: Boolean, default: false },
  },
  computed: {
    badgeClass() {
      const statusStyleMap = {
        // SampleStatus
        planned: "secondary",
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

        //CellStatus
        cycled: "primary",
        shorted: "danger",
        dismantled: "warning",
        other: "secondary",
      };

      return `${statusStyleMap[this.status?.toLowerCase()] || ""}`;
    },
  },
};
</script>

<style>
.dot {
  height: 0.5rem;
  width: 0.5rem;
  border-radius: 50%;
  color: #ffffff00;
  border: solid 1px;
  display: inline-block;
  margin-left: auto;
  margin-right: auto;
}
</style>
