<template>
  <div>
    <h5>Deployment info:</h5>
    <div class="p-3">
      <table>
        <tbody>
          <tr>
            <td>API version</td>
            <td>
              <code>{{ apiVersion }}</code>
            </td>
          </tr>
          <tr>
            <td>App version</td>
            <td>
              <code>{{ appVersion }}</code>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { getInfo } from "@/server_fetch_utils.js";
import { APP_VERSION } from "@/resources.js";

export default {
  data() {
    return {
      apiVersion: "unknown",
      appVersion: APP_VERSION,
    };
  },
  async mounted() {
    const info = this.$store.state.serverInfo;
    if (info) {
      this.apiVersion = info.server_version ?? "unknown";
    } else {
      const fetched = await getInfo();
      this.apiVersion = fetched?.server_version ?? "unknown";
    }
  },
};
</script>

<style scoped>
td,
th {
  text-align: center;
  border: 1px solid #ddd;
}
</style>
