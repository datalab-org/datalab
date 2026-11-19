<template>
  <form class="modal-enclosure" data-testid="tag-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="!isFormValid"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header>{{ isEditing ? "Edit tag" : "Create new tag" }}</template>

      <template #body>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="tag-scope">Scope:</label>
            <!-- Recreated each time the modal opens, so the available groups are re-fetched.
                 When editing, only administrators can change the scope. -->
            <TagScopeSelect
              v-if="modelValue && (!isEditing || isAdmin)"
              v-model="scopeSelection"
              :current-tag="isEditing ? tag : null"
            />
            <!-- Otherwise, show the existing scope read-only. -->
            <input
              v-else
              id="tag-scope"
              :value="scopeLabel"
              type="text"
              class="form-control"
              disabled
            />
            <small v-if="!isEditing && !isAdmin" class="form-text text-muted">
              Only administrators can create global tags. Group tags can be created by
              administrators and by the managers of the group.
            </small>
            <small
              v-if="scopeChangeWarning"
              class="form-text text-danger"
              data-testid="tag-scope-warning"
            >
              {{ scopeChangeWarning }}
            </small>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="tag-name">Name:</label>
            <input id="tag-name" v-model="name" type="text" class="form-control" required />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="tag-description">Description:</label>
            <textarea
              id="tag-description"
              v-model="description"
              class="form-control"
              rows="2"
            ></textarea>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label>Color:</label>
            <TagColorPicker v-model="color" :preview-label="name || 'preview'" />
          </div>
        </div>
        <div v-if="errorMessage" class="form-error mt-2">{{ errorMessage }}</div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import Modal from "@/components/Modal.vue";
import TagColorPicker from "@/components/TagColorPicker.vue";
import TagScopeSelect from "@/components/TagScopeSelect.vue";
import { createTag, updateTag } from "@/server_fetch_utils.js";
import { DEFAULT_TAG_COLOR } from "@/resources.js";

export default {
  name: "TagFormModal",
  components: {
    Modal,
    TagColorPicker,
    TagScopeSelect,
  },
  props: {
    modelValue: Boolean,
    // When set, the modal edits this tag (a row from GET /tags); otherwise it creates a new one.
    tag: {
      type: Object,
      default: null,
    },
  },
  emits: ["update:modelValue", "tag-created", "tag-updated"],
  data() {
    return {
      name: "",
      description: "",
      color: DEFAULT_TAG_COLOR,
      // New tags default to a user-defined tag.
      scope: "user",
      // The owning group's immutable_id, for group tags only.
      owner: null,
      errorMessage: null,
      submitting: false,
    };
  },
  computed: {
    isEditing() {
      return Boolean(this.tag);
    },
    isAdmin() {
      return this.$store.state.currentUserRole === "admin";
    },
    scopeSelection: {
      get() {
        return { scope: this.scope, owner: this.owner };
      },
      set({ scope, owner }) {
        this.scope = scope;
        this.owner = owner;
      },
    },
    scopeLabel() {
      if (this.scope === "global") {
        return "Global";
      }
      const base = this.scope === "group" ? "Group" : "User-defined";
      // When editing, also name the owning user or group (e.g. for an admin editing
      // another user's tag).
      return this.tag?.owner_name ? `${base}: ${this.tag.owner_name}` : base;
    },
    // Whether an administrator editing the tag has chosen another scope (or group).
    isScopeChanged() {
      if (!this.isEditing) {
        return false;
      }
      return (
        this.scope !== this.tag.scope || (this.scope === "group" && this.owner !== this.tag.owner)
      );
    },
    scopeChangeWarning() {
      if (!this.isScopeChanged) {
        return null;
      }
      let losers = null;
      // Only administrators change the scope here, so an admin moving their own tag keeps
      // their rights on it.
      if (this.tag.scope === "user" && this.tag.owner !== this.$store.state.currentUserID) {
        losers = this.tag.owner_name || "The owner";
      } else if (this.tag.scope === "group") {
        losers = `The managers of ${this.tag.owner_name || "the group"}`;
      }
      const keep = "Items that already have the tag keep it.";
      return losers ? `${losers} will no longer be able to edit or delete this tag. ${keep}` : keep;
    },
    isFormValid() {
      // A group tag also needs its group.
      const hasGroup = this.scope !== "group" || Boolean(this.owner);
      return !this.submitting && Boolean(this.name.trim()) && hasGroup;
    },
  },
  watch: {
    modelValue(isOpen) {
      // (Re)initialise the form whenever the modal opens, from the tag in edit mode.
      if (isOpen) {
        if (this.isEditing) {
          this.populateFromTag();
        } else {
          this.resetForm();
        }
      }
    },
  },
  methods: {
    populateFromTag() {
      this.name = this.tag.name || "";
      this.description = this.tag.description || "";
      this.color = this.tag.color || null;
      // Start from the tag's current scope (only administrators can change it).
      this.scope = this.tag.scope || "global";
      this.owner = this.tag.owner || null;
      this.errorMessage = null;
    },
    resetForm() {
      this.name = "";
      this.description = "";
      this.color = DEFAULT_TAG_COLOR;
      this.scope = "user";
      this.owner = null;
      this.errorMessage = null;
    },
    buildPayload() {
      const payload = {
        name: this.name.trim(),
        description: this.description || null,
        color: this.color || null,
      };
      // On edit, the scope is only sent when an administrator changes it.
      if (!this.isEditing || this.isScopeChanged) {
        payload.scope = this.scope;
        if (this.scope === "group") {
          payload.owner = this.owner;
        }
      }
      return payload;
    },
    async submitForm() {
      if (!this.isFormValid) {
        return;
      }
      this.errorMessage = null;
      this.submitting = true;
      try {
        if (this.isEditing) {
          await updateTag(this.tag.immutable_id, this.buildPayload());
          this.$emit("tag-updated");
        } else {
          await createTag(this.buildPayload());
          this.$emit("tag-created");
        }
        this.$emit("update:modelValue", false);
      } catch (error) {
        const message = typeof error === "string" ? error : error?.message || String(error);
        // A name clash is a 409 the user can fix inline; surface it in the form.
        if (message && message.toLowerCase().includes("already exists")) {
          this.errorMessage = message;
        } else {
          DialogService.error({
            title: this.isEditing ? "Tag Update Failed" : "Tag Creation Failed",
            message: `Error ${this.isEditing ? "updating" : "creating"} tag: ${message}`,
          });
        }
      } finally {
        this.submitting = false;
      }
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
