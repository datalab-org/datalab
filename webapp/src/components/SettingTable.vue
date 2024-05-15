<template>
  <button class="btn btn-default mb-3" @click="createSettingModalIsOpen = true">
    Add a setting
  </button>

  <table class="table table-hover table-sm" data-testid="setting-table">
    <thead>
      <tr>
        <th scope="col">Setting</th>
        <th scope="col">Value</th>
        <th scope="col">Description</th>
        <th scope="col">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(setting, index) in settings" :key="index" @click="openEditModal(setting)">
        <td>{{ setting.name }}</td>
        <td>{{ setting.value }}</td>
        <td>{{ setting.description }}</td>
        <td>
          <button class="btn btn-danger btn-sm" @click.stop="deleteSetting(setting)">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>
  <CreateSettingModal v-model="createSettingModalIsOpen" />
  <EditSettingsModal v-model="editSettingsIsOpen" :setting="selectedSetting" />
</template>

<script>
import { getAllSettings, deleteSetting } from "../server_fetch_utils";
import CreateSettingModal from "./CreateSettingModal.vue";
import EditSettingsModal from "./EditSettingsModal.vue";

export default {
  data() {
    return {
      settings: null,
      selectedSetting: null,
      createSettingModalIsOpen: false,
      editSettingsIsOpen: false,
    };
  },
  components: {
    CreateSettingModal,
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
    async deleteSetting(setting) {
      if (confirm(`Are you sure you want to delete ${setting.name}?`)) {
        await deleteSetting(setting._id.$oid);
      }
    },
  },
  created() {
    this.fetchAllSettings();
  },
};
</script>

<style scoped></style>
