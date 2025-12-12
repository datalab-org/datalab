<template>
  <span
    v-if="dotOnly"
    class="dot"
    :title="status.toUpperCase()"
    :class="'badge-' + badgeClass"
  ></span>
  <span v-else class="badge badge-pill text-uppercase" :class="'badge-' + badgeClass">
    {{ status }}
  </span>
</template>

<script>
export default {
  props: {
    dotOnly: { type: Boolean, default: true },
    status: { type: String, required: false, default: "" },
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
  position: relative;
}

.dot.badge-success {
  border-color: #28a745;
  background-color: transparent !important;
  box-shadow:
    0 0 2px #28a745,
    0 0 4px #28a745,
    0 0 6px #28a745;
}

.dot.badge-danger {
  border-color: #dc3545;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #dc3545 1.5px,
    #dc3545 2px
  ) !important;
}

.dot.badge-warning {
  border-color: #ffc107;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #ffc107 1.5px,
    #ffc107 2px
  ) !important;
}

.dot.badge-primary {
  border-color: #007bff;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #007bff 1.5px,
    #007bff 2px
  ) !important;
}

.dot.badge-secondary {
  border-color: #6c757d;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #6c757d 1.5px,
    #6c757d 2px
  ) !important;
}

.dot.badge-info {
  border-color: #17a2b8;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #17a2b8 1.5px,
    #17a2b8 2px
  ) !important;
}

.dot.badge-dark {
  border-color: #343a40;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #343a40 1.5px,
    #343a40 2px
  ) !important;
}
</style>
