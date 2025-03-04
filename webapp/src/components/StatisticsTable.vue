<template>
  <div v-if="counts" class="mx-auto">
    <table>
      <tbody>
        <tr>
          <td :style="{ color: itemTypes['users'].navbarColor }">{{ counts["users"] }}</td>
          <td :style="{ color: itemTypes['samples'].navbarColor }">{{ counts["samples"] }}</td>
          <td :style="{ color: itemTypes['cells'].navbarColor }">{{ counts["cells"] }}</td>
        </tr>
        <tr>
          <th>Active Users</th>
          <th>Samples</th>
          <th>Cells</th>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { getStats } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";

export default {
  data() {
    return {
      counts: null,
      itemTypes: itemTypes,
    };
  },
  async mounted() {
    console.log(this.counts);
    this.counts = await getStats();
    console.log(this.counts);
  },
};
</script>

<style scoped>
table {
  margin-left: auto;
  margin-right: auto;
  margin-top: 20px;
  margin-bottom: 20px;
}

td,
th {
  width: 150px;
  text-align: center;
  margin-left: auto;
  margin-right: auto;
  font-weight: bold;
}

th {
  font-weight: normal;
  border-right: 1px solid #ddd;
  border-left: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
}

td {
  border-top: 1px solid #ddd;
  font-size: 2em;
  border-right: 1px solid #ddd;
  border-left: 1px solid #ddd;
}
</style>
