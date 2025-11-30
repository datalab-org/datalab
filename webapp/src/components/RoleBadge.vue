<template>
  <span class="badge formatted-role-name" :class="badgeStyle"> {{ role }} </span>
</template>

<script>
export default {
  props: {
    role: { type: String, required: true },
  },
  computed: {
    badgeStyle() {
      switch (this.role) {
        case "admin":
          return "text-warning";
        case "manager":
          return "text-info";
        case "user":
          return "text-success";
        default:
          return "text-danger";
      }
    },
  },
};
</script>

<style scoped>
.formatted-role-name {
  border: 2px solid;
  text-transform: uppercase;
  font-family: var(--font-monospace);
}
</style>
