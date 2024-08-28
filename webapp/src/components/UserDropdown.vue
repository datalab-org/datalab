<template>
  <a
    type="button"
    class="dropdown-item btn login btn-link"
    aria-label="Account settings"
    @click="editAccountSettingIsOpen = true"
    ><font-awesome-icon icon="cog" /> &nbsp;&nbsp;Account settings
    <span v-if="isUnverified"><NotificationDot /></span>
  </a>
  <span v-if="user.role === 'admin'">
    <router-link to="/admin" class="dropdown-item btn login btn-link" aria-label="Administration">
      <font-awesome-icon icon="users-cog" /> &nbsp;Administration
      <span v-if="hasUnverifiedUser"><NotificationDot /></span>
    </router-link>
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
</style>
