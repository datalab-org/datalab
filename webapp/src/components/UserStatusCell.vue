<template>
  <span v-if="status === 'active'" class="mx-auto dot badge-success"></span>
  <span v-else-if="status === 'unverified'" class="badge activity-badge text-danger">
    Unverified
  </span>
  <span v-else-if="status === 'deactivated'" class="badge activity-badge text-secondary">
    Deactivated
  </span>
</template>

<script>
export default {
  name: "UserStatusCell",
  props: {
    status: {
      type: String,
      required: true,
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
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 1.5px,
    #28a745 1.5px,
    #28a745 2px
  ) !important;
  box-shadow:
    0 0 2px #28a745,
    0 0 4px #28a745,
    0 0 6px #28a745;
}

.activity-badge {
  font-family: var(--font-monospace);
  text-transform: uppercase;
  border: 2px solid;
  border-radius: 0.25rem;
  font-size: 0.8em;
}
</style>
