<template>
  <form @submit.prevent="submitForm" class="modal-enclosure" data-testid="create-setting-form">
    <Modal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)">
      <template v-slot:header> Add new setting </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="create-setting-name" class="col-form-label">Name:</label>
            <select v-model="setting.name" class="form-control" id="create-setting-name">
              <option value="public">LOGO_URL</option>
              <option value="private">HOMEPAGE_URL</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="create-setting-setting-value" class="col-form-label">Value:</label>
            <input
              v-model="setting.value"
              type="text"
              class="form-control"
              id="create-setting-setting-value"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="create-setting-setting-description" class="col-form-label"
              >Description:</label
            >
            <input
              v-model="setting.description"
              type="text"
              class="form-control"
              id="create-setting-setting-description"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="create-setting-access-level" class="col-form-label">Access Level:</label>
            <select
              v-model="setting.access_level"
              class="form-control"
              id="create-setting-access-level"
            >
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { createNewSetting } from "../server_fetch_utils";

export default {
  name: "CreateSettingModal",
  data() {
    return {
      setting: {
        name: "",
        value: "",
        description: "",
        access_level: "public",
      },
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  methods: {
    async submitForm() {
      await createNewSetting(this.setting);
      this.$emit("update:modelValue", false);
    },
  },
  components: {
    Modal,
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

.form-error a {
  color: #820000;
  font-weight: 600;
}

.modal-enclosure .modal-content {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}
</style>
