<template>
  <div v-if="displayedMetadata && Object.keys(displayedMetadata).length > 0">
    <table class="table table-sm">
      <tbody>
        <tr v-for="(value, key) in displayedMetadata" :key="key">
          <th scope="row">{{ formatLabel(key) }}</th>
          <td>{{ formatValue(key, value) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: {
    metadata: {
      type: Object,
      default: () => ({}),
    },
    labels: {
      type: Object,
      default: () => ({}),
    },
    excludeKeys: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    displayedMetadata() {
      if (!this.metadata) return {};

      const filtered = {};
      for (const [key, value] of Object.entries(this.metadata)) {
        if (!this.excludeKeys.includes(key) && value !== null && value !== undefined) {
          filtered[key] = value;
        }
      }
      return filtered;
    },
  },
  methods: {
    formatLabel(key) {
      if (this.labels[key]) {
        return this.labels[key];
      }

      return key
        .replace(/_/g, " ")
        .replace(/([A-Z])/g, " $1")
        .trim()
        .replace(/^\w/, (c) => c.toUpperCase());
    },
    formatValue(key, value) {
      if (value === null || value === undefined) {
        return "";
      }

      if (typeof value === "object") {
        if (Array.isArray(value)) {
          return value.join(", ");
        }
        return JSON.stringify(value);
      }

      return value;
    },
  },
};
</script>

<style scoped>
th {
  color: #454545;
  font-weight: 500;
}
</style>
