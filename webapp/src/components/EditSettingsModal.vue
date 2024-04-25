<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)">
      <template v-slot:header> Settings </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="setting-name" class="col-form-label">Name:</label>
            <input
              :value="setting ? setting.name : ''"
              type="text"
              class="form-control"
              id="setting-name"
              readonly
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="setting-value" class="col-form-label">Value:</label>
            <input
              v-model="settingValue"
              type="text"
              class="form-control"
              id="setting-value"
              required
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { API_URL } from "@/resources.js";
import Modal from "@/components/Modal.vue";
import { saveSetting } from "@/server_fetch_utils.js";

export default {
  name: "EditSettingsModal",
  props: {
    modelValue: Boolean,
    setting: Object,
  },
  data() {
    return {
      apiUrl: API_URL,
      settingValue: "",
    };
  },
  emits: ["update:modelValue"],
  computed: {},
  methods: {
    async submitForm() {
      await saveSetting(this.setting._id.$oid, this.settingValue);
      this.$emit("update:modelValue", false);
    },
  },
  components: {
    Modal,
  },
  watch: {
    modelValue: {
      handler(newValue) {
        if (newValue) {
          this.settingValue = this.setting.value;
        }
      },
    },
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}

.btn:disabled {
  cursor: not-allowed;
}
</style>
