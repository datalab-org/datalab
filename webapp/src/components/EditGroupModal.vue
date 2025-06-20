<template>
  <form class="modal-enclosure" data-testid="edit-group-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="!isFormValid"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header> Edit Group: {{ originalGroup?.display_name }} </template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="edit-group-group_id" class="col-form-label">Group ID:</label>
            <input
              id="edit-group-group_id"
              v-model="group_id"
              type="text"
              class="form-control"
              disabled
              title="Group ID cannot be modified"
            />
            <small class="form-text text-muted">Group ID cannot be modified</small>
          </div>
          <div class="form-group col-md-6">
            <label for="edit-display-name" class="col-form-label">Display Name:</label>
            <input
              id="edit-display-name"
              v-model="display_name"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': showValidation && !display_name }"
              required
            />
            <div v-if="showValidation && !display_name" class="invalid-feedback">
              Display Name is required.
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="edit-description">Description:</label>
            <textarea
              id="edit-description"
              v-model="description"
              class="form-control"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="editGroupAdminsLabel">Group Admins:</label>
            <UserSelect v-model="group_admins" aria-labelledby="editGroupAdminsLabel" multiple />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import UserSelect from "@/components/UserSelect.vue";
import { updateGroup, getUsersList } from "@/server_fetch_utils.js";

export default {
  name: "EditGroupModal",
  components: {
    Modal,
    UserSelect,
  },
  props: {
    modelValue: Boolean,
    group: {
      type: Object,
      default: null,
    },
  },
  emits: ["update:modelValue", "group-updated"],
  data() {
    return {
      group_id: "",
      display_name: "",
      description: "",
      group_admins: [],
      originalGroup: null,
      originalAdmins: [],
      showValidation: false,
      allUsers: [],
    };
  },
  computed: {
    isFormValid() {
      return this.display_name.trim() !== "";
    },
  },
  watch: {
    async group(newGroup) {
      if (newGroup) {
        await this.loadGroupData(newGroup);
      }
    },
    async modelValue(newValue) {
      if (newValue && this.group) {
        await this.loadGroupData(this.group);
      }
    },
  },
  async created() {
    try {
      this.allUsers = await getUsersList();
    } catch (error) {
      console.error("Could not load users:", error);
      this.allUsers = [];
    }
  },
  methods: {
    async loadGroupData(group) {
      this.originalGroup = { ...group };
      this.group_id = group.group_id;
      this.display_name = group.display_name;
      this.description = group.description || "";

      this.group_admins = this.loadUsersFromIds(group.group_admins || []);
      this.originalAdmins = [...this.group_admins];
    },

    loadUsersFromIds(userIds) {
      return userIds
        .map((userId) => {
          return this.allUsers.find(
            (user) =>
              (user._id && user._id === userId) ||
              (user.user_id && user.user_id === userId) ||
              (user.immutable_id && user.immutable_id === userId),
          );
        })
        .filter((user) => user !== undefined);
    },

    async submitForm() {
      this.showValidation = true;

      if (!this.isFormValid) {
        return;
      }

      try {
        console.log("Selected group_admins for update:", this.group_admins);

        const groupData = {
          display_name: this.display_name,
          description: this.description,
          group_admins: this.group_admins
            .map((admin) => {
              const userId = admin.user_id || admin._id || admin.immutable_id;
              console.log("Admin object for update:", admin, "Using ID:", userId);
              return userId;
            })
            .filter((id) => id !== undefined),
        };

        console.log("Updating group with data:", groupData);

        await updateGroup(this.originalGroup.immutable_id, groupData);

        this.$emit("group-updated");
        this.resetForm();
        this.$emit("update:modelValue", false);
      } catch (error) {
        console.error("Error updating group:", error);
        alert("Error updating group: " + error);
      }
    },

    resetForm() {
      this.group_id = "";
      this.display_name = "";
      this.description = "";
      this.group_admins = [];
      this.originalGroup = null;
      this.originalAdmins = [];
      this.showValidation = false;
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
</style>
