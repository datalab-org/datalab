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
          <div class="form-group col-md-8">
            <label for="account-groups" class="col-form-label">Groups:</label>
            <div>
              <div v-for="group in user.groups" :key="group" class="dropdown-item">
                <FormattedGroupName :group="group" />
              </div>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="connected-accounts" class="col-form-label">Connected accounts:</label>
            <a
              v-if="user.identities.some((identity) => identity.identity_type === 'github')"
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              :href="
                'https://github.com/' +
                user.identities.find((identity) => identity.identity_type === 'github').name
              "
            >
              <font-awesome-icon :icon="['fab', 'github']" />
              {{ user.identities.find((identity) => identity.identity_type === "github").name }}
            </a>

            <a
              v-else-if="showGitHub"
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Login via GitHub"
              :href="apiUrl + '/login/github'"
              ><font-awesome-icon :icon="['fab', 'github']" /> Connect your GitHub account</a
            >
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <a
              v-if="user.identities.some((identity) => identity.identity_type === 'orcid')"
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              :href="
                'https://orcid.org/' +
                user.identities.find((identity) => identity.identity_type === 'orcid').name
              "
            >
              <font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" />
              {{ user.identities.find((identity) => identity.identity_type === "orcid").name }}
            </a>
            <a
              v-else-if="showORCID"
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Connect ORCID account"
              :href="apiUrl + '/login/orcid'"
              ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Connect your
              ORCID</a
            >
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label class="col-form-label">API Keys:</label>
            <APIKeyHelp />

            <ul v-if="apiKeys.length" class="list-group mb-2">
              <li class="list-group-item d-flex align-items-center api-key-header">
                <span class="api-key-name">Label</span>
                <span class="api-key-middle text-center mx-2">Key</span>
                <span class="api-key-date text-right">Creation date</span>
                <span class="api-key-revoke-spacer ml-3"></span>
              </li>
              <li
                v-for="key in apiKeys"
                :key="key._id"
                class="list-group-item d-flex align-items-center api-key-row"
              >
                <strong class="api-key-name" :title="key.name">{{ key.name }}</strong>

                <div class="api-key-middle d-flex justify-content-center mx-2">
                  <div v-if="key.show" class="input-group input-group-sm api-key-input-group">
                    <StyledInput
                      v-model="apiKey"
                      :readonly="true"
                      :help-message="apiKeyHelpMessage"
                      class="form-control form-control-sm"
                    />
                    <span class="input-group-append">
                      <button
                        class="btn btn-sm btn-outline-secondary"
                        type="button"
                        @click="copyToClipboard"
                      >
                        <font-awesome-icon icon="copy" />
                      </button>
                    </span>
                  </div>
                  <code v-else class="api-key-digest">{{ key.digest }}</code>
                </div>

                <span class="small text-muted text-nowrap text-right api-key-date">
                  {{ key.created_at ? humanDate(key.created_at) : "Unknown" }}
                </span>

                <button
                  class="btn btn-sm btn-outline-danger ml-3 api-key-revoke"
                  type="button"
                  @click="deleteKey(key._id)"
                >
                  Revoke
                </button>
              </li>
            </ul>
            <div v-else class="text-muted mb-2">You have no API keys yet.</div>

            <div class="input-group new-key-input-group">
              <input
                v-model="newKeyName"
                type="text"
                class="form-control"
                :class="{ 'is-invalid': newKeyNameError }"
                placeholder="Add new key with label (e.g., laptop, CI)"
                aria-label="Add new key with label"
                @input="newKeyNameError = false"
              />
              <div class="input-group-append">
                <button
                  class="btn"
                  :class="newKeyNameError ? 'btn-outline-danger' : 'btn-default'"
                  type="button"
                  title="Generate new key"
                  aria-label="Generate new key"
                  @click="requestAPIKey"
                >
                  <font-awesome-icon icon="plus" />
                </button>
              </div>
            </div>
            <div v-if="newKeyNameError" class="form-error small mt-1">A new key needs a label.</div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label class="col-form-label">Your Activity:</label>
            <UserActivityGraph
              v-if="user && user.immutable_id"
              :key="user.immutable_id"
              :user-id="user.immutable_id"
              :compact="true"
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import { format } from "date-fns";

import { DialogService } from "@/services/DialogService";

import { API_URL } from "@/resources.js";
import Modal from "@/components/Modal.vue";
import UserBubble from "@/components/UserBubble.vue";
import UserActivityGraph from "@/components/UserActivityGraph.vue";
import FormattedGroupName from "@/components/FormattedGroupName.vue";

import {
  getUserInfo,
  saveUser,
  requestNewAPIKey,
  getAPIKeys,
  deleteAPIKey,
} from "@/server_fetch_utils.js";
import StyledInput from "./StyledInput.vue";
import APIKeyHelp from "@/components/APIKeyHelp.vue";

import { invalidateCurrentUserCache } from "@/server_fetch_utils.js";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

export default {
  name: "EditAccountSettingsModal",
  components: {
    APIKeyHelp,
    FontAwesomeIcon,
    Modal,
    StyledInput,
    UserBubble,
    UserActivityGraph,
    FormattedGroupName,
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
      apiKeys: [],
      apiKey: null,
      newKeyName: "",
      newKeyNameError: false,
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
    this.loadAPIKeys();
  },
  methods: {
    async submitForm() {
      await saveUser(this.user.immutable_id, this.user);
      invalidateCurrentUserCache();
      this.$store.commit("setDisplayName", this.user.display_name);
      this.$emit("update:modelValue", false);
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
    async loadAPIKeys() {
      this.apiKeys = await getAPIKeys();
    },
    async requestAPIKey(event) {
      event.preventDefault();
      if (!this.newKeyName || /^\s*$/.test(this.newKeyName)) {
        this.newKeyNameError = true;
        return;
      }
      const confirmed = await DialogService.confirm({
        title: "Generate New API Key",
        message: `Generate a new API key named "${this.newKeyName}"?`,
        type: "warning",
      });
      if (confirmed) {
        const result = await requestNewAPIKey(this.newKeyName);
        this.apiKey = result.key;
        this.newKeyName = "";
        await this.loadAPIKeys();
        this.apiKeys[this.apiKeys.length - 1].show = true;
        await DialogService.alert({
          title: "API Key Generated",
          message:
            'A new API key has been generated. Please note that when you close the "Account Settings" window, the key will not be displayed again.',
          type: "success",
        });
      }
    },
    async deleteKey(id) {
      const confirmed = await DialogService.confirm({
        title: "Delete API Key",
        message: "Are you sure you want to delete this API key? This cannot be undone.",
        type: "warning",
      });
      if (confirmed) {
        const success = await deleteAPIKey(id);
        if (success) {
          await this.loadAPIKeys();
        }
      }
    },
    copyToClipboard() {
      navigator.clipboard.writeText(this.apiKey);
    },
    humanDate(isodatetime) {
      return format(new Date(isodatetime), "d MMM yyyy");
    },
    resetForm() {
      this.apiKeyDisplayed = false;
      this.apiKey = null;
      this.newKeyName = "";
      this.newKeyNameError = false;
      this.$emit("update:modelValue", false);
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

.btn:disabled {
  cursor: not-allowed;
}

.api-key-name {
  flex: 0 0 8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.api-key-digest {
  font-size: 75%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.api-key-middle {
  flex: 1 1 auto;
  min-width: 0;
}

.api-key-date {
  flex: 0 0 7rem;
}

.api-key-revoke,
.api-key-revoke-spacer {
  flex: 0 0 4.5rem;
}

.api-key-header {
  padding-top: 0.6rem;
  padding-bottom: 0.6rem;
  background-color: #f8f9fa;
  color: #6c757d;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.api-key-row {
  padding-top: 0.35rem;
  padding-bottom: 0.35rem;
}

.new-key-input-group {
  max-width: 26rem;
}

.api-key-input-group {
  flex: 0 1 auto;
  width: auto;
  min-width: 0;
}

.api-key-input-group :deep(input) {
  width: 12rem;
}
</style>
