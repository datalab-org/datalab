<template>
  <table class="table table-hover table-sm" data-testid="setting-table">
    <thead>
      <tr>
        <th scope="col">Setting</th>
        <th scope="col">Value</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(setting, index) in settings" :key="index" @click="openEditModal(setting)">
        <td>{{ setting.name }}</td>
        <td>{{ setting.value }}</td>
      </tr>
    </tbody>
  </table>
  <EditSettingsModal v-model="editSettingsIsOpen" :setting="selectedSetting" />
</template>

<script>
import { getAllSettings } from "../server_fetch_utils";
import EditSettingsModal from "./EditSettingsModal.vue";

export default {
  data() {
    return {
      settings: null,
      selectedSetting: null,
      editSettingsIsOpen: false,
    };
  },
  components: {
    EditSettingsModal,
  },
  methods: {
    async fetchAllSettings() {
      let data = await getAllSettings();
      if (data != null) {
        this.settings = JSON.parse(JSON.stringify(data));
      }
    },
    openEditModal(setting) {
      this.selectedSetting = setting;
      this.editSettingsIsOpen = true;
    },
  },
  created() {
    this.fetchAllSettings();
  },
};
</script>

<style scoped></style>
