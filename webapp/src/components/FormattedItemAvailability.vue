<template>
  <span
    v-if="dotOnly"
    class="dot"
    :title="availability ? availability.toUpperCase() : ''"
    :class="'badge-' + badgeClass"
  ></span>
  <span v-else class="badge badge-pill text-uppercase" :class="'badge-' + badgeClass">
    {{ availability || "unknown" }}
  </span>
</template>

<script>
export default {
  props: {
    dotOnly: { type: Boolean, default: true },
    availability: { type: String, required: false, default: null },
  },
  computed: {
    badgeClass() {
      if (!this.availability) return "secondary";

      const availabilityStyleMap = {
        available: "success",
        unavailable: "danger",
        exhausted: "dark",
        unknown: "secondary",
      };

      return `${availabilityStyleMap[this.availability?.toLowerCase()] || "secondary"}`;
    },
  },
};
</script>

<style scoped>
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
</style>
