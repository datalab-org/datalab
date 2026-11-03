<template>
  <form class="notification-composer" @submit.prevent="submit">
    <Modal
      :model-value="modelValue"
      :disable-submit="!canSubmit"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <template #header>New notification</template>
      <template #body>
        <div v-if="allowSendAll" class="form-group custom-control custom-checkbox">
          <input
            id="notification-send-all"
            v-model="sendAllUsers"
            type="checkbox"
            class="custom-control-input"
          />
          <label class="custom-control-label" for="notification-send-all">
            Send to all active users
          </label>
        </div>

        <div class="form-group">
          <label id="notification-recipients-label">Recipients</label>
          <UserSelect
            v-model="selectedUsers"
            :disabled="sendAllUsers"
            aria-labelledby="notification-recipients-label"
          />
        </div>

        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="notification-title">Title</label>
            <input
              id="notification-title"
              v-model="title"
              class="form-control"
              type="text"
              maxlength="200"
              required
            />
          </div>
          <div class="form-group col-md-4">
            <label for="notification-level">Level</label>
            <select id="notification-level" v-model="level" class="form-control">
              <option v-for="option in levels" :key="option" :value="option">
                {{ capitalize(option) }}
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="notification-summary">Summary</label>
          <textarea
            id="notification-summary"
            v-model="summary"
            class="form-control"
            rows="3"
            maxlength="1000"
          ></textarea>
        </div>

        <div class="form-group mb-0">
          <label for="notification-message">Full message</label>
          <textarea
            id="notification-message"
            v-model="message"
            class="form-control"
            rows="7"
            maxlength="5000"
          ></textarea>
        </div>

        <div v-if="errorMessage" class="alert alert-danger mt-3 mb-0">
          {{ errorMessage }}
        </div>
      </template>
      <template #footer>
        <button type="button" class="btn btn-outline-secondary mr-auto" @click="resetForm">
          Clear
        </button>
        <button type="submit" class="btn btn-info" :disabled="!canSubmit">
          <font-awesome-icon v-if="submitting" icon="spinner" spin class="mr-1" />
          Send
        </button>
        <button type="button" class="btn btn-secondary" @click="$emit('update:modelValue', false)">
          Cancel
        </button>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import UserSelect from "@/components/UserSelect.vue";
import { createNotification } from "@/server_fetch_utils.js";

export default {
  name: "NotificationComposer",
  components: { Modal, UserSelect },
  props: {
    modelValue: { type: Boolean, default: false },
    allowSendAll: { type: Boolean, default: false },
  },
  emits: ["update:modelValue", "sent"],
  data() {
    return {
      selectedUsers: [],
      sendAllUsers: false,
      title: "",
      summary: "",
      message: "",
      level: "normal",
      levels: ["low", "normal", "important", "urgent", "critical"],
      submitting: false,
      errorMessage: "",
    };
  },
  computed: {
    hasRecipients() {
      return (this.allowSendAll && this.sendAllUsers) || this.selectedUsers.length > 0;
    },
    canSubmit() {
      return !this.submitting && this.hasRecipients && Boolean(this.title.trim());
    },
  },
  watch: {
    modelValue(isOpen) {
      if (isOpen) this.errorMessage = "";
    },
    allowSendAll(isAllowed) {
      if (!isAllowed) this.sendAllUsers = false;
    },
  },
  methods: {
    capitalize(value) {
      return value.charAt(0).toUpperCase() + value.slice(1);
    },
    async submit() {
      if (!this.canSubmit) return;

      const payload = {
        title: this.title.trim(),
        level: this.level,
      };
      if (this.allowSendAll && this.sendAllUsers) {
        payload.send_all_users = true;
      } else {
        payload.recipient_ids = this.selectedUsers.map((user) => user.immutable_id);
      }
      if (this.summary.trim()) payload.summary = this.summary.trim();
      if (this.message.trim()) payload.message = this.message.trim();

      this.submitting = true;
      this.errorMessage = "";
      try {
        const response = await createNotification(payload);
        this.$emit("sent", response);
        this.resetForm();
        this.$emit("update:modelValue", false);
      } catch (error) {
        this.errorMessage = `Unable to send notification: ${String(error)}`;
      } finally {
        this.submitting = false;
      }
    },
    resetForm() {
      this.selectedUsers = [];
      this.sendAllUsers = false;
      this.title = "";
      this.summary = "";
      this.message = "";
      this.level = "normal";
      this.errorMessage = "";
    },
  },
};
</script>
