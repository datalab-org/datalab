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
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="editGroupMembersLabel">Group Members:</label>
            <UserSelect v-model="group_members" aria-labelledby="editGroupMembersLabel" multiple />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import UserSelect from "@/components/UserSelect.vue";
import {
  updateGroup,
  addUserToGroup,
  removeUserFromGroup,
  getAdminGroupsList,
} from "@/server_fetch_utils.js";

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
      group_members: [],
      originalMembers: [],
      showValidation: false,
      allUsers: [],
    };
  },
  computed: {
    isFormValid() {
      return this.display_name && this.display_name.trim() !== "";
    },
  },
  watch: {
    group: {
      immediate: true,
      handler(newGroup) {
        if (newGroup) {
          this.group_id = newGroup.group_id;
          this.display_name = newGroup.display_name;
          this.description = newGroup.description;

          this.group_admins = newGroup.group_admins || [];
          this.group_members = newGroup.members || [];

          this.originalGroup = { ...newGroup };
          this.originalAdmins = [...this.group_admins];
          this.originalMembers = [...this.group_members];
        }
      },
    },
  },
  async created() {
    try {
      this.allUsers = await getAdminGroupsList();
    } catch (error) {
      console.error("Could not load users:", error);
      this.allUsers = [];
    }
  },
  methods: {
    async submitForm() {
      this.showValidation = true;
      if (!this.isFormValid) return;

      const groupData = {
        display_name: this.display_name,
        description: this.description,
        group_admins: this.group_admins.map((admin) => admin.immutable_id),
      };

      try {
        await updateGroup(this.originalGroup.immutable_id, groupData);

        await this.updateGroupMembers();

        this.$emit("group-updated");
        this.$emit("update:modelValue", false);
      } catch (error) {
        alert("Error updating group: " + error.message);
      }
    },
    async updateGroupMembers() {
      const currentMemberIds = this.group_members.map((m) => m.immutable_id || m);
      const originalMemberIds = this.originalMembers.map((m) => m.immutable_id || m);

      const toAdd = currentMemberIds.filter((id) => !originalMemberIds.includes(id));

      const toRemove = originalMemberIds.filter((id) => !currentMemberIds.includes(id));

      for (const userId of toAdd) {
        try {
          await addUserToGroup(this.originalGroup.immutable_id, userId);
        } catch (error) {
          console.error("Error adding user to group:", error);
        }
      }

      for (const userId of toRemove) {
        try {
          await removeUserFromGroup(this.originalGroup.immutable_id, userId);
        } catch (error) {
          console.error("Error removing user from group:", error);
        }
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
