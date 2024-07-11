<template>
  <div class="row justify-content-center pt-3">
    <GetEmailModal v-model="emailModalIsOpen" />
    <template v-if="user != null">
      <div class="dropdown">
        <button
          id="userDropdown"
          class="btn btn-default dropdown-toggle"
          type="button"
          aria-haspopup="true"
          aria-expanded="false"
          data-toggle="dropdown"
          @click="isUserDropdownVisible = !isUserDropdownVisible"
        >
          <UserBubbleLogin :creator="user" :size="24" />&nbsp;
          <span class="user-display-name">{{ userDisplayName }}</span
          >&nbsp;
        </button>
        <div
          v-show="isUserDropdownVisible"
          class="dropdown-menu"
          style="display: block"
          aria-labelledby="UserDropdown"
        >
          <a
            type="button"
            class="dropdown-item btn login btn-link btn-default"
            aria-label="Account settings"
            @click="
              editAccountSettingIsOpen = true;
              isUserDropdownVisible = false;
            "
            ><font-awesome-icon icon="cog" /> &nbsp;&nbsp;Account settings
            <span v-if="isUnverified"><NotificationDot /></span>
          </a>
          <span v-if="user.role === 'admin'">
            <router-link
              to="/admin"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Administration"
            >
              <font-awesome-icon icon="users-cog" /> &nbsp;Administration
              <span v-if="hasUnverifiedUser"><NotificationDot /></span>
            </router-link>
          </span>
          <a
            type="button"
            class="dropdown-item btn login btn-link btn-default"
            aria-label="Logout"
            :href="apiUrl + '/logout'"
            ><font-awesome-icon icon="sign-out-alt" /> &nbsp;&nbsp;Logout</a
          >
        </div>
      </div>
      <EditAccountSettingsModal v-model="editAccountSettingIsOpen" />
    </template>
    <template v-else>
      <div class="dropdown">
        <button
          id="loginDropdown"
          class="btn btn-default dropdown-toggle"
          type="button"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          @click="isLoginDropdownVisible = !isLoginDropdownVisible"
        >
          <font-awesome-icon icon="sign-in-alt" />&nbsp;Login/Register
        </button>
        <div
          v-show="isLoginDropdownVisible"
          class="dropdown-menu"
          style="display: block"
          aria-labelledby="loginButton"
        >
          <a
            type="button"
            class="dropdown-item btn login btn-link btn-default"
            aria-label="Login via GitHub"
            :href="apiUrl + '/login/github'"
            ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
          >
          <a
            type="button"
            class="dropdown-item btn login btn-link btn-default"
            aria-label="Login via ORCID"
            :href="apiUrl + '/login/orcid'"
            ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID</a
          >
          <button
            type="button"
            class="dropdown-item btn login btn-link btn-default"
            aria-label="Login via email"
            @click="emailModalIsOpen = true"
          >
            <font-awesome-icon :icon="['fa', 'envelope']" /> Login via email
          </button>
        </div>
      </div>
    </template>
  </div>

  <div v-if="isUnverified" class="container mt-4 mb-0 alert alert-warning text-center">
    Your account is currently unverified, and you will be unable to make or edit entries. Please
    contact an administrator.
  </div>
</template>

<script>
import { API_URL } from "@/resources.js";
import UserBubbleLogin from "@/components/UserBubbleLogin.vue";
import NotificationDot from "@/components/NotificationDot.vue";
import { getUserInfo } from "@/server_fetch_utils.js";
import GetEmailModal from "@/components/GetEmailModal.vue";
import EditAccountSettingsModal from "@/components/EditAccountSettingsModal.vue";

export default {
  components: {
    UserBubbleLogin,
    GetEmailModal,
    EditAccountSettingsModal,
    NotificationDot,
  },
  props: {
    modelValue: Boolean,
  },
  data() {
    return {
      isLoginDropdownVisible: false,
      isUserDropdownVisible: false,
      emailModalIsOpen: false,
      apiUrl: API_URL,
      user: null,
      editAccountSettingIsOpen: false,
    };
  },
  computed: {
    userDisplayName() {
      return this.$store.getters.getCurrentUserDisplayName;
    },
    isUnverified() {
      return this.$store.getters.getCurrentUserIsUnverified;
    },
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
  },
  watch: {
    modelValue(newValue) {
      if (newValue) {
        this.openModal();
      } else {
        this.closeModal();
      }
    },
  },
  mounted() {
    this.getUser();
  },
  methods: {
    async getUser() {
      // Need to reload the page if this is a magic-link login
      let token = this.$route.query.token;
      if (token != null) {
        window.location.href = this.apiUrl + "/login/email?token=" + token;
      }

      this.user = await getUserInfo();
      if (this.user != null) {
        this.$store.commit(
          "setIsUnverified",
          this.user.account_status == "unverified" ? true : false,
        );
      }
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

.orcid-icon {
  color: #a6ce39;
}
</style>
