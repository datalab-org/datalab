<template>
  <form
    class="modal-enclosure"
    data-testid="bulk-change-managers-form"
    @submit.prevent="submitForm"
  >
    <Modal :model-value="modelValue" :disable-submit="!isValid" @update:model-value="handleClose">
      <template #header> Change User Managers </template>

      <template #body>
        <div v-if="modelValue">
          <div class="alert alert-info">
            <small>
              <font-awesome-icon icon="info-circle" class="mr-1" />
              Select managers for the {{ selectedUsers.length }} selected user(s).
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
              <label for="managers-select" class="col-form-label font-weight-bold">Managers:</label>
              <vSelect
                v-model="selectedManagers"
                :options="potentialManagers"
                label="display_name"
                multiple
                placeholder="Select managers..."
                class="managers-select"
                :taggable="false"
                :push-tags="false"
                :create-option="() => null"
                @update:model-value="handleManagersUpdate"
              >
                <template #option="option">
                  <div class="d-flex align-items-center">
                    <UserBubble :creator="option" :size="20" />
                    <span class="ml-2">{{ option.display_name }}</span>
                    <span class="ml-auto"><RoleBadge :role="option.role" /></span>
                  </div>
                </template>
                <template #selected-option="option">
                  <div class="d-flex align-items-center">
                    <UserBubble :creator="option" :size="18" />
                    <span class="ml-2 small">{{ option.display_name }}</span>
                  </div>
                </template>
              </vSelect>
            </div>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import Modal from "@/components/Modal.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import UserBubble from "@/components/UserBubble.vue";
import vSelect from "vue-select";

export default {
  name: "BulkChangeManagersModal",
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
    allUsers: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue", "managers-selected"],
  data() {
    return {
      selectedManagers: [],
    };
  },
  computed: {
    potentialManagers() {
      const selectedUserIds = this.selectedUsers.map((u) => u.immutable_id);
      return this.allUsers.filter(
        (u) =>
          !selectedUserIds.includes(u.immutable_id) && (u.role === "admin" || u.role === "manager"),
      );
    },
    isValid() {
      return (
        this.selectedManagers.length > 0 &&
        this.selectedManagers.every((m) => m && typeof m === "object" && m.immutable_id)
      );
    },
  },
  methods: {
    handleManagersUpdate(value) {
      const validManagers = (value || []).filter(
        (m) =>
          m &&
          typeof m === "object" &&
          m.immutable_id &&
          this.potentialManagers.some((pm) => pm.immutable_id === m.immutable_id),
      );

      if (validManagers.length !== (value || []).length) {
        this.$nextTick(() => {
          this.selectedManagers = validManagers;
        });
      } else {
        this.selectedManagers = validManagers;
      }
    },
    handleSearchBlur() {
      this.selectedManagers = this.selectedManagers.filter(
        (m) => m && typeof m === "object" && m.immutable_id,
      );
    },
    submitForm() {
      const validManagers = this.selectedManagers.filter(
        (m) =>
          m &&
          typeof m === "object" &&
          m.immutable_id &&
          this.potentialManagers.some((pm) => pm.immutable_id === m.immutable_id),
      );

      if (validManagers.length === 0 && this.selectedManagers.length > 0) {
        DialogService.error({
          title: "Invalid Selection",
          message: "No valid managers selected. Please choose from the dropdown list.",
        });
        this.selectedManagers = [];
        return;
      }

      if (validManagers.length !== this.selectedManagers.length) {
        DialogService.error({
          title: "Invalid Selection",
          message: "Some invalid entries were removed. Please verify your selection.",
        });
        this.selectedManagers = validManagers;
        return;
      }

      this.$emit("managers-selected", validManagers);
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
      this.selectedManagers = [];
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

.managers-select {
  width: 100%;
}

.managers-select :deep(.vs__dropdown-menu) {
  z-index: 9999;
}

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}
</style>
