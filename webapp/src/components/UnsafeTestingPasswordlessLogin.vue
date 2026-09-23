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
      <div v-if="users === null && !error" class="text-center text-muted py-3">
        <font-awesome-icon icon="spinner" spin /> Loading test users…
      </div>
      <div
        v-else-if="users !== null && users.length === 0"
        class="text-muted"
        data-testid="testing-passwordless-empty"
      >
        No passwordless test users are configured.
      </div>
      <div v-else-if="users !== null" class="list-group" data-testid="testing-passwordless-users">
        <button
          v-for="user in users"
          :key="user.username"
          type="button"
          class="list-group-item list-group-item-action"
          :disabled="isLoggingIn"
          @click="login(user.username)"
        >
          <div class="d-flex justify-content-between align-items-start">
            <div class="text-left flex-grow-1">
              <Creators :creators="[user]" :size="32" />
              <small class="d-block text-muted">{{ user.username }}</small>
              <div v-if="user.groups?.length" class="d-flex flex-wrap gap-2 mt-2">
                <FormattedGroupName
                  v-for="group in user.groups"
                  :key="group.immutable_id"
                  :group="group"
                  :size="24"
                />
              </div>
              <small v-else class="d-block text-muted">No groups</small>
            </div>
            <RoleBadge :role="user.role" class="ml-2" />
          </div>
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
import Creators from "@/components/Creators.vue";
import FormattedGroupName from "@/components/FormattedGroupName.vue";
import Modal from "@/components/Modal.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import { getTestingPasswordlessUsers, loginTestingPasswordless } from "@/server_fetch_utils.js";

export default {
  components: { Creators, FormattedGroupName, Modal, RoleBadge },
  data() {
    return {
      isOpen: false,
      users: null,
      error: "",
      isLoggingIn: false,
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
      if (this.isLoggingIn) return;

      this.isLoggingIn = true;
      this.error = "";
      try {
        await loginTestingPasswordless(username);
        window.location.reload();
      } catch {
        this.error = "Unable to log in as that test user.";
      } finally {
        this.isLoggingIn = false;
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
