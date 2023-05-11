<template>
  <div v-if="statsAvailable" class="center ml-auto mr-auto">
    <table>
      <tr>
        <td>Active Users</td>
        <td>Samples</td>
        <td>Cells</td>
      </tr>
      <tr>
        <td>{{ counts["users"] }}</td>
        <td>{{ counts["samples"] }}</td>
        <td>{{ counts["cells"] }}</td>
      </tr>
    </table>
  </div>
</template>

<script>
import { getStats } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      statsAvailable: false,
    };
  },
  computed: {
    counts() {
      return this.$store.state.counts || { users: 0, samples: 0, cells: 0 };
    },
  },
  methods: {
    fetchStats() {
      getStats().catch(() => {
        this.statsAvailable = false;
      });
      this.statsAvailable = true;
    },
  },
  created() {
    this.fetchStats();
  },
};
</script>
