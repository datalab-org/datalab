<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="resetForm"
      :disableSubmit="
        Boolean(displayNameValidationMessage) || Boolean(contactEmailValidationMessage)
      "
    >
      <template v-slot:header> Account settings </template>

      <template v-slot:body>
        <div class="mx-auto align-center text-center p-4">
          <UserBubble :creator="this.user" :size="128" />&nbsp;
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
              v-model="user.display_name"
              type="text"
              class="form-control"
              id="account-name"
              required
            />
            <div class="form-error" v-html="displayNameValidationMessage"></div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="account-email" class="col-form-label">Contact email:</label>
            <input
              v-model="user.contact_email"
              type="text"
              class="form-control"
              id="account-email"
              placeholder="Please enter your email"
            />
            <div class="form-error" v-html="contactEmailValidationMessage"></div>
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
              v-else
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Login via GitHub"
              :href="this.apiUrl + '/login/github'"
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
              v-else
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Connect ORCID account"
              :href="this.apiUrl + '/login/orcid'"
              ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Connect your
              ORCID</a
            >
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="api-key" class="col-form-label">API Key:</label>
            <div v-if="apiKeyDisplayed" class="input-group">
              <StyledInput
                v-model="apiKey"
                :readonly="true"
                :helpMessage="apiKeyHelpMessage"
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
import { getUserInfo, saveUser, requestNewAPIKey } from "@/server_fetch_utils.js";
import StyledInput from "./StyledInput.vue";

export default {
  name: "EditAccountSettingsModal",
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
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  computed: {
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
  methods: {
    async submitForm() {
      await saveUser(this.user.immutable_id, this.user);
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
  mounted() {
    this.getUser();
  },
  components: {
    Modal,
    StyledInput,
    UserBubble,
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
</style>
