<template>
  <table class="table table-hover table-sm" data-testid="setting-table">
    <thead>
      <tr>
        <th scope="col">Setting</th>
        <th scope="col">Value</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(setting, index) in settings" :key="index">
        <td>{{ setting.name }}</td>
        <td>{{ setting.value }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getAllSettings } from "../server_fetch_utils";
export default {
  data() {
    return {
      settings: null,
    };
  },
  methods: {
    async fetchAllSettings() {
      let data = await getAllSettings();
      if (data != null) {
        this.settings = JSON.parse(JSON.stringify(data));
      }
    },
  },
  created() {
    this.fetchAllSettings();
  },
};
</script>

<style scoped></style>
