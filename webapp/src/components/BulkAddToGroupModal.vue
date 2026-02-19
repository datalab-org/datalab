<template>
  <form class="modal-enclosure" data-testid="bulk-add-to-group-form" @submit.prevent="submitForm">
    <Modal :model-value="modelValue" :disable-submit="!isValid" @update:model-value="handleClose">
      <template #header> Add Users to Group </template>

      <template #body>
        <div v-if="modelValue">
          <div class="alert alert-info">
            <small>
              <font-awesome-icon icon="info-circle" class="mr-1" />
              Select a group to add the {{ selectedUsers.length }} selected user(s) to.
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
              <label for="group-select" class="col-form-label font-weight-bold">Group:</label>
              <GroupSelect
                v-model="selectedGroups"
                :minimum-options="1"
                aria-labelledby="group-select"
              />
              <div
                v-if="showValidation && selectedGroups.length === 0"
                class="invalid-feedback d-block"
              >
                Please select a group.
              </div>
            </div>
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
import GroupSelect from "@/components/GroupSelect.vue";
import { DialogService } from "@/services/DialogService";

export default {
  name: "BulkAddToGroupModal",
  components: {
    Modal,
    RoleBadge,
    UserBubble,
    GroupSelect,
  },
  props: {
    modelValue: Boolean,
    selectedUsers: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue", "group-selected"],
  data() {
    return {
      selectedGroups: [],
      showValidation: false,
    };
  },
  computed: {
    isValid() {
      return this.selectedGroups.length > 0;
    },
  },
  methods: {
    submitForm() {
      this.showValidation = true;

      if (!this.isValid) {
        DialogService.error({
          title: "Invalid Selection",
          message: "Please select at least one group.",
        });
        return;
      }

      this.$emit("group-selected", this.selectedGroups);
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
      this.selectedGroups = [];
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

.modal-enclosure :deep(.modal-content) {
  max-height: 90vh;
  overflow: auto;
  scroll-behavior: smooth;
}

.invalid-feedback.d-block {
  display: block !important;
}
</style>
