<template>
  <a
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Account settings"
    @click="editAccountSettingIsOpen = true"
  >
    <font-awesome-icon icon="cog" /> &nbsp;&nbsp;Account settings
    <span v-if="isUnverified" class="notification-wrapper"><NotificationDot /></span>
  </a>
  <span v-if="user.role === 'admin'">
    <router-link to="/admin" class="dropdown-item btn login btn-link" aria-label="Administration">
      <font-awesome-icon icon="users-cog" /> &nbsp;Administration
      <span v-if="hasUnverifiedUser" class="notification-wrapper"><NotificationDot /></span>
    </router-link>
  </span>
  <span v-if="user.role === 'admin'" class="dropdown-item super-user-toggle">
    <div class="form-check form-switch">
      <input
        id="superUserModeToggle"
        class="form-check-input"
        type="checkbox"
        role="switch"
        :checked="adminSuperUserMode"
        @change="toggleSuperUserMode"
      />
      <label class="form-check-label" for="superUserModeToggle">Super-user mode</label>
    </div>
  </span>
  <a
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Logout"
    :href="apiUrl + '/logout'"
    ><font-awesome-icon icon="sign-out-alt" /> &nbsp;&nbsp;Logout</a
  >
  <EditAccountSettingsModal v-model="editAccountSettingIsOpen" />
</template>

<script>
import EditAccountSettingsModal from "@/components/EditAccountSettingsModal.vue";
import NotificationDot from "@/components/NotificationDot.vue";
import { API_URL } from "@/resources.js";

export default {
  components: {
    EditAccountSettingsModal,
    NotificationDot,
  },
  props: {
    modelValue: Boolean,
    user: { type: Object, required: true },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      editAccountSettingIsOpen: false,
      apiUrl: API_URL,
    };
  },
  computed: {
    isUnverified() {
      return this.$store.getters.getCurrentUserIsUnverified;
    },
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
    adminSuperUserMode() {
      return this.$store.state.adminSuperUserMode;
    },
  },
  watch: {
    editAccountSettingIsOpen: function (val) {
      if (!val) {
        this.$emit("update:modelValue", false);
      }
    },
  },
  methods: {
    toggleSuperUserMode(event) {
      this.$store.commit("setAdminSuperUserMode", event.target.checked);
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.btn:disabled {
  cursor: not-allowed;
}

.user-display-name {
  font-weight: bold;
}

.notification-wrapper {
  position: relative;
  display: inline-block;
  margin-left: 0.25rem;
  vertical-align: middle;
}

.super-user-toggle {
  padding: 0.5rem 1rem;
}

.super-user-toggle .form-check-label {
  cursor: pointer;
}
</style>
