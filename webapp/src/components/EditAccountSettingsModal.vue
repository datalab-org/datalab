<template>
  <form class="modal-enclosure" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      :disable-submit="
        Boolean(displayNameValidationMessage) || Boolean(contactEmailValidationMessage)
      "
      @update:model-value="resetForm"
    >
      <template #header> Account settings </template>

      <template #body>
        <div class="mx-auto align-center text-center p-4">
          <UserBubble :creator="user" :size="128" />&nbsp;
        </div>
        <div class="form-row">
          <div class="form-group col-md-8 mx-auto text-justify">
            You can add an avatar by registering your <i>datalab</i> contact email at
            <a href="https://gravatar.com" target="_blank">gravatar.com</a>.
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="account-name" class="col-form-label">Name:</label>
            <input
              id="account-name"
              v-model="user.display_name"
              type="text"
              class="form-control"
              required
            />
            <div class="form-error">{{ displayNameValidationMessage }}</div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="account-email" class="col-form-label">Contact email:</label>
            <input
              id="account-email"
              v-model="user.contact_email"
              type="text"
              class="form-control"
              placeholder="Please enter your email"
            />
            <div class="form-error">{{ contactEmailValidationMessage }}</div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="connected-accounts" class="col-form-label">Connected accounts:</label>
            <div v-if="user.identities.some((identity) => identity.identity_type === 'github')">
              <div type="button" class="dropdown-item identity-section">
                <a
                  class="identity-link"
                  :href="
                    'https://github.com/' +
                    user.identities.find((identity) => identity.identity_type === 'github').name
                  "
                >
                  <font-awesome-icon :icon="['fab', 'github']" />
                  {{ user.identities.find((identity) => identity.identity_type === "github").name }}
                </a>
                <font-awesome-icon
                  class="identity-disconnect-btn"
                  :icon="['fas', 'times']"
                  @click="disconnectIdentity()"
                />
              </div>
            </div>
            <div v-else-if="showGitHub">
              <a
                type="button"
                class="dropdown-item btn login btn-link btn-default"
                aria-label="Login via GitHub"
                :href="apiUrl + '/login/github'"
                ><font-awesome-icon :icon="['fab', 'github']" /> Connect your GitHub account</a
              >
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <div v-if="user.identities.some((identity) => identity.identity_type === 'orcid')">
              <div type="button" class="dropdown-item btn login btn-link btn-default">
                <a
                  class="identity-link"
                  :href="
                    'https://orcid.org/' +
                    user.identities.find((identity) => identity.identity_type === 'orcid').name
                  "
                >
                  <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" />
                  {{ user.identities.find((identity) => identity.identity_type === "orcid").name }}
                </a>
                <font-awesome-icon
                  class="identity-disconnect-btn"
                  :icon="['fas', 'times']"
                  @click="disconnectIdentity()"
                />
              </div>
            </div>
            <div v-else-if="showORCID">
              <a
                type="button"
                class="dropdown-item btn login btn-link btn-default"
                aria-label="Connect ORCID account"
                :href="apiUrl + '/login/orcid'"
              >
                <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Connect your ORCID
              </a>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="api-key" class="col-form-label">API Key:</label>
            <div v-if="apiKeyDisplayed" class="input-group">
              <StyledInput
                v-model="apiKey"
                :readonly="true"
                :help-message="apiKeyHelpMessage"
                class="form-control"
              />
              <div class="input-group-append">
                <button class="btn btn-outline-secondary" type="button" @click="copyToClipboard">
                  <font-awesome-icon icon="copy" />
                </button>
              </div>
            </div>
            <div class="input-group">
              <button class="btn btn-default mt-2" @click="requestAPIKey">
                Regenerate API Key
              </button>
            </div>
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { API_URL } from "@/resources.js";
import Modal from "@/components/Modal.vue";
import UserBubble from "@/components/UserBubble.vue";
import {
  getUserInfo,
  saveUser,
  requestNewAPIKey,
  disconnectIdentityFromUser,
} from "@/server_fetch_utils.js";
import StyledInput from "./StyledInput.vue";

export default {
  name: "EditAccountSettingsModal",
  components: {
    Modal,
    StyledInput,
    UserBubble,
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  data() {
    return {
      user: {
        display_name: "",
        contact_email: "",
        identities: [],
      },
      apiUrl: API_URL,
      apiKeyDisplayed: false,
      apiKey: null,
      apiKeyHelpMessage:
        'You can use your API key via the datalab-api Python package, or pass it as an HTTP header "DATALAB-API-KEY" with the tool of your choice (e.g., curl).',
    };
  },
  computed: {
    showGitHub() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.github ?? false;
    },
    showORCID() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.orcid ?? false;
    },
    displayNameValidationMessage() {
      if (!this.user.display_name || /^\s*$/.test(this.user.display_name)) {
        return "Name is required.";
      } else if (this.user.display_name.length > 150) {
        return "Name should be no more than 150 characters.";
      } else {
        return "";
      }
    },
    contactEmailValidationMessage() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (this.user.contact_email && !emailRegex.test(this.user.contact_email)) {
        return "Invalid email format.";
      }
      return "";
    },
  },
  mounted() {
    this.getUser();
  },
  methods: {
    async submitForm() {
      await saveUser(this.user.immutable_id, this.user);
      this.$store.commit("setDisplayName", this.user.display_name);
      this.$emit("update:modelValue", false);
    },
    async disconnectIdentity(identityType, identifier) {
      await disconnectIdentityFromUser(this.user.immutable_id, identityType, identifier);
    },
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.user = user;
      } else {
        this.user = {
          display_name: "",
          contact_email: "",
          identities: [],
          role: "user",
        };
      }
    },
    async requestAPIKey(event) {
      event.preventDefault();
      if (
        window.confirm(
          "Requesting a new API key will remove your old one. Are you sure you want to proceed?",
        )
      ) {
        const newKey = await requestNewAPIKey();
        this.apiKey = newKey;
        this.apiKeyDisplayed = true;
        window.alert(
          `A new API key has been generated. Please note that when you close the "Account Settings" window, the key will not be displayed again. `,
        );
      }
    },
    copyToClipboard() {
      navigator.clipboard.writeText(this.apiKey);
    },
    resetForm() {
      this.apiKeyDisplayed = false;
      this.apiKey = null;
      this.$emit("update:modelValue", false);
    },
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

.identity-section:hover {
  background-color: inherit;
}

.identity-link {
  color: black;
}

.identity-disconnect-btn {
  padding-left: 10px;
  color: darkgrey;
}

.identity-disconnect-btn:hover {
  color: black;
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

.btn:disabled {
  cursor: not-allowed;
}
</style>
