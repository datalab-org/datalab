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
  <div v-if="user.role === 'admin'" class="dropdown-item admin-row">
    <router-link to="/admin" class="btn login btn-link admin-link" aria-label="Administration">
      <font-awesome-icon icon="users-cog" /> &nbsp;Administration
      <span v-if="hasUnverifiedUser" class="notification-wrapper"><NotificationDot /></span>
    </router-link>
    <StyledTooltip :delay="300">
      <template #anchor>
        <div class="custom-control custom-switch super-user-toggle" @click.stop>
          <input
            id="superUserModeToggle"
            type="checkbox"
            class="custom-control-input"
            :checked="adminSuperUserMode"
            @change="toggleSuperUserMode"
          />
          <label class="custom-control-label" for="superUserModeToggle"></label>
        </div>
      </template>
      <template #content> Super-user mode: enables read access to all items </template>
    </StyledTooltip>
  </div>
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
import StyledTooltip from "@/components/StyledTooltip.vue";
import { API_URL } from "@/resources.js";

export default {
  components: {
    EditAccountSettingsModal,
    NotificationDot,
    StyledTooltip,
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
      return this.$store.getters.isAdminSuperUserModeActive;
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

.admin-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.admin-row .admin-link {
  padding: 0;
  flex-grow: 1;
  text-decoration: none;
  color: inherit;
}

.admin-row .admin-link:hover {
  text-decoration: none;
}

.super-user-toggle {
  margin-left: 1rem;
  padding-left: 2.25rem;
}

.super-user-toggle .custom-control-label {
  cursor: pointer;
}

/* Brick red styling for super-user mode toggle when checked */
.super-user-toggle .custom-control-input:checked ~ .custom-control-label::before {
  background-color: #a52a2a;
  border-color: #a52a2a;
}

.super-user-toggle .custom-control-input:checked ~ .custom-control-label::after {
  background-color: #fff;
}
</style>
