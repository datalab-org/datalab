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
            <select
              v-if="canChooseScope"
              id="tag-scope"
              v-model="scope"
              data-testid="tag-scope-select"
              class="form-control"
            >
              <option value="user">Personal (only you can use it)</option>
              <option value="global">Global (available to everyone)</option>
            </select>
            <input
              v-else
              id="tag-scope"
              :value="scopeLabel"
              type="text"
              class="form-control"
              disabled
            />
            <small v-if="!isEditing && !isAdmin" class="form-text text-muted">
              Only administrators can create global tags.
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
import { createTag, updateTag } from "@/server_fetch_utils.js";
import { DEFAULT_TAG_COLOR } from "@/resources.js";

export default {
  name: "TagFormModal",
  components: {
    Modal,
    TagColorPicker,
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
      // New tags default to a personal tag.
      scope: "user",
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
    // Scope can only be chosen by an admin creating a new tag.
    canChooseScope() {
      return !this.isEditing && this.isAdmin;
    },
    scopeLabel() {
      return this.scope === "global" ? "Global" : "Personal";
    },
    isFormValid() {
      return !this.submitting && Boolean(this.name.trim());
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
      // Scope is immutable on edit; show the existing scope.
      this.scope = this.tag.scope || "global";
      this.errorMessage = null;
    },
    resetForm() {
      this.name = "";
      this.description = "";
      this.color = DEFAULT_TAG_COLOR;
      this.scope = "user";
      this.errorMessage = null;
    },
    buildPayload() {
      const payload = {
        name: this.name.trim(),
        description: this.description || null,
        color: this.color || null,
      };
      // Scope cannot be changed on edit.
      if (!this.isEditing) {
        payload.scope = this.scope;
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
