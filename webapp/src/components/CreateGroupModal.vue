<template>
  <form class="modal-enclosure" data-testid="create-group-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="!isFormValid"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header> Create new group </template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="group-id" class="col-form-label">Group ID:</label>
            <input
              id="group-id"
              v-model="group_id"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': showValidation && (isValidGroupId || !group_id) }"
              required
            />
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div v-if="isValidGroupId" class="form-error" v-html="isValidGroupId"></div>
            <div v-if="showValidation && !group_id" class="invalid-feedback">
              Group ID is required.
            </div>
          </div>
          <div class="form-group col-md-6">
            <label for="display-name" class="col-form-label">Display Name:</label>
            <input
              id="display-name"
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
            <label for="description">Description:</label>
            <textarea
              id="description"
              v-model="description"
              class="form-control"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="groupAdminsLabel">Group Admins:</label>
            <UserSelect v-model="group_admins" aria-labelledby="groupAdminsLabel" multiple />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="groupMembersLabel">Group Members:</label>
            <UserSelect v-model="group_members" aria-labelledby="groupMembersLabel" multiple />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import UserSelect from "@/components/UserSelect.vue";
import { createGroup, addUserToGroup } from "@/server_fetch_utils.js";
import { validateEntryID } from "@/field_utils.js";

export default {
  name: "CreateGroupModal",
  components: {
    Modal,
    UserSelect,
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue", "group-created"],
  data() {
    return {
      group_id: "",
      display_name: "",
      description: "",
      group_admins: [],
      group_members: [],
      takenGroupIds: [],
      showValidation: false,
    };
  },
  computed: {
    existingGroupIds() {
      return this.$store.state.groups_list
        ? this.$store.state.groups_list.map((x) => x.group_id)
        : [];
    },
    isValidGroupId() {
      if (!this.group_id) {
        return "";
      }
      return validateEntryID(this.group_id, this.takenGroupIds, this.existingGroupIds);
    },
    isFormValid() {
      return this.group_id && this.display_name && !this.isValidGroupId;
    },
  },
  methods: {
    async submitForm() {
      this.showValidation = true;

      if (!this.isFormValid) {
        return;
      }

      try {
        const groupData = {
          group_id: this.group_id,
          display_name: this.display_name,
          description: this.description,
          group_admins: this.group_admins
            .map((admin) => {
              const userId = admin.user_id || admin._id || admin.immutable_id;
              return userId;
            })
            .filter((id) => id !== undefined),
        };

        const response = await createGroup(groupData);
        if (response.status === "success") {
          const group_immutable_id = response.group_immutable_id;

          if (this.group_members.length > 0) {
            for (const member of this.group_members) {
              await addUserToGroup(group_immutable_id, member.immutable_id);
            }
          }

          this.$emit("group-created");
          this.resetForm();
          this.$emit("update:modelValue", false);
        }
      } catch (error) {
        console.error("Error creating group:", error);
        let is_group_id_error = false;
        try {
          if (error.includes("group_id_validation_error") || error.includes("already exists")) {
            this.takenGroupIds.push(this.group_id);
            is_group_id_error = true;
          }
        } catch (e) {
          console.log("error parsing error message", e);
        } finally {
          if (!is_group_id_error) {
            alert("Error with creating new group: " + error);
          }
        }
      }
    },
    resetForm() {
      this.group_id = "";
      this.display_name = "";
      this.description = "";
      this.group_admins = [];
      this.group_members = [];
      this.takenGroupIds = [];
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
