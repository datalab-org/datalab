<template>
  <form class="modal-enclosure" data-testid="bulk-change-role-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="!selectedRole"
      @update:model-value="handleClose"
    >
      <template #header> Change User Roles </template>

      <template #body>
        <div v-if="modelValue">
          <div class="alert alert-info">
            <small>
              <font-awesome-icon icon="info-circle" class="mr-1" />
              Select a new role for the {{ selectedUsers.length }} selected user(s).
            </small>
          </div>

          <div class="form-row">
            <div class="form-group col-md-12">
              <label for="selected-users" class="col-form-label font-weight-bold"
                >Users Selected ({{ selectedUsers.length }}):</label
              >
              <div id="selected-users" class="selected-users-list">
                <div
                  v-for="(user, index) in selectedUsers"
                  :key="index"
                  class="user-item d-flex align-items-center mb-2"
                >
                  <UserBubble :creator="user" :size="32" />
                  <span class="ml-2">{{ user.display_name }}</span>
                  <span class="ml-auto">
                    <RoleBadge :role="user.role" />
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group col-md-12">
              <label for="role-select" class="col-form-label font-weight-bold">New Role:</label>
              <vSelect
                v-model="selectedRole"
                :options="roleOptions"
                :clearable="false"
                :searchable="false"
                placeholder="Select a role..."
                class="role-select"
                :class="{ 'is-invalid': showValidation && !selectedRole }"
              >
                <template #option="option">
                  <RoleBadge :role="option.label" />
                </template>
                <template #selected-option="option">
                  <RoleBadge :role="option.label" />
                </template>
              </vSelect>
              <div v-if="showValidation && !selectedRole" class="invalid-feedback d-block">
                Please select a role.
              </div>
            </div>
          </div>

          <div v-if="selectedRole === 'admin'" class="alert alert-warning">
            <small>
              <font-awesome-icon icon="exclamation-triangle" class="mr-1" />
              <strong>Warning:</strong> You are about to grant admin privileges to
              {{ selectedUsers.length }} user(s). Admins have full access to all system features.
            </small>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import UserBubble from "@/components/UserBubble.vue";
import vSelect from "vue-select";

export default {
  name: "BulkChangeRoleModal",
  components: {
    Modal,
    RoleBadge,
    UserBubble,
    vSelect,
  },
  props: {
    modelValue: Boolean,
    selectedUsers: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue", "role-selected"],
  data() {
    return {
      selectedRole: null,
      roleOptions: ["user", "admin", "manager"],
      showValidation: false,
    };
  },
  methods: {
    submitForm() {
      this.showValidation = true;

      if (!this.selectedRole) {
        return;
      }

      this.$emit("role-selected", this.selectedRole);

      this.resetForm();
      this.$emit("update:modelValue", false);
    },
    handleClose(value) {
      if (!value) {
        this.resetForm();
      }
      this.$emit("update:modelValue", value);
    },
    resetForm() {
      this.selectedRole = null;
      this.showValidation = false;
    },
  },
};
</script>

<style scoped>
.selected-users-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 1rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.user-item {
  padding: 0.5rem;
  background-color: white;
  border-radius: 0.25rem;
  border: 1px solid #e9ecef;
}

.role-select {
  width: 100%;
}

.role-select :deep(.vs__dropdown-menu) {
  z-index: 9999;
}

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}

.invalid-feedback.d-block {
  display: block !important;
}
</style>
