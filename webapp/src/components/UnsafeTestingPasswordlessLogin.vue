<template>
  <Modal v-model="isOpen" :is-large="false">
    <template #header>
      <font-awesome-icon icon="exclamation-triangle" class="text-danger" />
      Unsafe passwordless test login
    </template>
    <template #body>
      <div class="alert alert-danger" data-testid="testing-passwordless-warning">
        No authentication is performed. Anyone with access to this instance can impersonate any user
        listed below. Never enable this login mechanism in production.
      </div>
      <div v-if="error" class="alert alert-warning" data-testid="testing-passwordless-error">
        {{ error }}
      </div>
      <div v-else-if="users === null" class="text-center text-muted py-3">
        <font-awesome-icon icon="spinner" spin /> Loading test users…
      </div>
      <div
        v-else-if="users.length === 0"
        class="text-muted"
        data-testid="testing-passwordless-empty"
      >
        No passwordless test users are configured.
      </div>
      <div v-else class="list-group" data-testid="testing-passwordless-users">
        <button
          v-for="user in users"
          :key="user.username"
          type="button"
          class="list-group-item list-group-item-action"
          @click="login(user.username)"
        >
          <span class="d-flex justify-content-between align-items-center">
            <span class="text-left">
              <strong>{{ user.display_name || user.username }}</strong>
              <small class="d-block text-muted">{{ user.username }}</small>
            </span>
            <span class="d-flex align-items-center">
              <RoleBadge :role="user.role" class="mr-2" />
              <span
                class="d-flex align-items-center"
                :title="`Account status: ${user.account_status}`"
                :aria-label="`Account status: ${user.account_status}`"
              >
                <UserStatusCell :status="user.account_status" />
              </span>
            </span>
          </span>
        </button>
      </div>
    </template>
    <template #footer>
      <button
        type="button"
        class="btn btn-secondary"
        data-testid="testing-passwordless-close"
        @click="isOpen = false"
      >
        Close
      </button>
    </template>
  </Modal>
  <button
    type="button"
    class="dropdown-item btn login btn-link unsafe-testing-login"
    aria-label="Open unsafe passwordless test login"
    data-testid="testing-passwordless-open"
    @click="open"
  >
    <font-awesome-icon icon="exclamation-triangle" /> Unsafe passwordless test login
  </button>
</template>

<script>
import Modal from "@/components/Modal.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import UserStatusCell from "@/components/UserStatusCell.vue";
import { getTestingPasswordlessUsers, loginTestingPasswordless } from "@/server_fetch_utils.js";

export default {
  components: { Modal, RoleBadge, UserStatusCell },
  data() {
    return {
      isOpen: false,
      users: null,
      error: "",
    };
  },
  methods: {
    async open() {
      this.isOpen = true;
      this.users = null;
      this.error = "";
      try {
        this.users = await getTestingPasswordlessUsers();
      } catch {
        this.error = "Unable to load passwordless test users.";
      }
    },
    async login(username) {
      try {
        await loginTestingPasswordless(username);
        window.location.reload();
      } catch {
        this.error = "Unable to log in as that test user.";
      }
    },
  },
};
</script>

<style scoped>
.unsafe-testing-login {
  color: #b00020;
  white-space: normal;
}
</style>
