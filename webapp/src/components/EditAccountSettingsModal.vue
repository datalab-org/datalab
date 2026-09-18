<template>
  <form class="modal-enclosure" @submit.prevent="submitForm">
    <Modal :model-value="modelValue" @update:model-value="resetForm">
      <template #header> Account settings </template>

      <template #body>
        <div class="account-layout">
          <div class="account-sidebar">
            <UserBubble
              :creator="user"
              :size="128"
              href="https://gravatar.com"
              link-label="Manage your avatar on gravatar.com"
            >
              <template #tooltip>
                <template v-if="hasGravatar">Change your avatar at gravatar.com</template>
                <template v-else>
                  Add an avatar by registering your contact email at gravatar.com
                </template>
              </template>
            </UserBubble>
            <div class="account-name mt-3">{{ savedUser.display_name }}</div>
            <div v-if="savedUser.contact_email" class="small text-muted">
              {{ savedUser.contact_email }}
            </div>
            <div
              v-if="displayNameLooksLikeEmail"
              class="alert alert-info small p-2 mt-3 mb-0 text-left"
            >
              Your name looks like an email address.
              <a href="#" @click.prevent="editDisplayName">Set your display name</a>
              on your profile.
            </div>
          </div>

          <ul class="nav nav-tabs mb-3" role="tablist" aria-label="Account settings sections">
            <li v-for="tab in tabs" :key="tab.id" class="nav-item" role="presentation">
              <button
                :id="`account-tab-${tab.id}`"
                ref="tabButtons"
                class="nav-link"
                :class="{ active: activeTab === tab.id }"
                type="button"
                role="tab"
                :aria-selected="activeTab === tab.id"
                :aria-controls="`account-panel-${tab.id}`"
                :tabindex="activeTab === tab.id ? 0 : -1"
                @click="activeTab = tab.id"
                @keydown.left.prevent="moveTabFocus(-1)"
                @keydown.right.prevent="moveTabFocus(1)"
                @keydown.home.prevent="moveTabFocus(0, true)"
                @keydown.end.prevent="moveTabFocus(tabs.length - 1, true)"
              >
                {{ tab.label }}
              </button>
            </li>
          </ul>

          <div class="account-panes scroll-shadows">
            <div
              v-show="activeTab === 'profile'"
              id="account-panel-profile"
              role="tabpanel"
              aria-labelledby="account-tab-profile"
              tabindex="0"
              class="account-tab"
            >
              <div class="form-row">
                <div class="col profile-fields">
                  <div class="form-group">
                    <label for="account-name">Display name</label>
                    <input
                      id="account-name"
                      v-model="user.display_name"
                      type="text"
                      class="form-control"
                      required
                    />
                    <div class="form-error small">{{ displayNameValidationMessage }}</div>
                  </div>
                  <div class="form-group">
                    <label for="account-email">Contact email</label>
                    <select
                      v-if="!addingEmail"
                      id="account-email"
                      class="form-control"
                      :value="user.contact_email || ''"
                      @change="selectContactEmail($event.target.value)"
                    >
                      <option value="">No contact email</option>
                      <option
                        v-for="option in contactEmailOptions"
                        :key="option.email"
                        :value="option.email"
                      >
                        {{ option.email }}{{ option.verified ? "" : " (unverified)" }}
                      </option>
                      <option :value="ADD_EMAIL_OPTION">Add a new email address…</option>
                    </select>
                    <div v-else class="input-group">
                      <input
                        id="account-email"
                        ref="newEmailInput"
                        v-model="user.contact_email"
                        type="email"
                        class="form-control"
                        placeholder="New email address"
                      />
                      <div class="input-group-append">
                        <button
                          class="btn btn-outline-secondary"
                          type="button"
                          @click="cancelAddEmail"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                    <div v-if="addingEmail" class="small text-muted mt-1">
                      <template v-if="emailVerificationEnabled">
                        A verification email will be sent to this address when you submit.
                      </template>
                      <template v-else>
                        This address will be saved unverified, as email verification is not enabled
                        on this server.
                      </template>
                    </div>
                    <div class="form-error small">{{ contactEmailValidationMessage }}</div>
                    <div
                      v-if="contactEmailUnverified && !addingEmail && !emailVerificationEnabled"
                      class="alert alert-secondary d-flex align-items-start mt-2 mb-0"
                      role="status"
                    >
                      <font-awesome-icon icon="info-circle" class="mr-2 mt-1" />
                      <div>
                        <strong>Your contact email is not verified.</strong>
                        <div class="small">
                          Email verification is not enabled on this <i>datalab</i> server, so no
                          verification emails will be sent until an administrator configures it.
                        </div>
                      </div>
                    </div>
                    <div
                      v-else-if="contactEmailUnverified && !addingEmail"
                      class="alert alert-warning d-flex align-items-start mt-2 mb-0"
                      role="alert"
                    >
                      <font-awesome-icon icon="exclamation-triangle" class="mr-2 mt-1" />
                      <div>
                        <strong>Your contact email is not verified.</strong>
                        <div class="small">
                          Use the link in the verification email sent to
                          {{ savedUser.contact_email }}, or choose a verified address above.
                          Submitting this form will send a new verification email.
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="form-group">
                    <label class="d-block">Connected accounts</label>
                    <ConnectedAccounts :identities="user.identities || []" section="accounts" />
                  </div>
                  <div class="form-group">
                    <label class="d-block">Email addresses</label>
                    <ConnectedAccounts
                      :identities="user.identities || []"
                      section="emails"
                      :primary-email="savedUser.contact_email"
                    />
                  </div>
                  <div class="form-group mb-0">
                    <button
                      class="btn btn-link p-0 groups-toggle"
                      type="button"
                      :aria-expanded="groupsExpanded"
                      :disabled="!userGroups.length"
                      @click="toggleGroups"
                    >
                      <font-awesome-icon
                        v-if="userGroups.length"
                        icon="chevron-right"
                        :rotation="groupsExpanded ? 90 : undefined"
                        class="mr-1 groups-chevron"
                      />
                      Groups ({{ userGroups.length }})
                    </button>
                    <ul v-if="groupsExpanded" ref="groupsList" class="list-unstyled mt-1 mb-0 pl-3">
                      <li
                        v-for="group in userGroups"
                        :key="group.immutable_id ?? group.group_id"
                        class="py-1"
                      >
                        <FormattedGroupName :group="group" />
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div
              v-show="activeTab === 'api-keys'"
              id="account-panel-api-keys"
              role="tabpanel"
              aria-labelledby="account-tab-api-keys"
              tabindex="0"
              class="account-tab api-keys-tab"
            >
              <APIKeyHelp />

              <ul v-if="apiKeys.length" class="list-group mb-2 api-key-list scroll-shadows">
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
              <div class="small text-muted mb-2">
                Keys are only shown once, when they are created.
              </div>

              <div class="input-group new-key-input-group">
                <input
                  v-model="newKeyName"
                  type="text"
                  class="form-control"
                  :class="{ 'is-invalid': newKeyNameError }"
                  placeholder="Add new key with label (e.g., laptop, CI)"
                  aria-label="Add new key with label"
                  @input="newKeyNameError = false"
                  @keydown.enter.prevent="requestAPIKey"
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
              <div v-if="newKeyNameError" class="form-error small mt-1 api-key-error">
                A new key needs a label.
              </div>
            </div>

            <div
              v-show="activeTab === 'activity'"
              id="account-panel-activity"
              role="tabpanel"
              aria-labelledby="account-tab-activity"
              tabindex="0"
              class="account-tab account-activity"
            >
              <UserActivityGraph
                v-if="user && user.immutable_id"
                :key="user.immutable_id"
                :user-id="user.immutable_id"
                :compact="true"
                :show-summary="true"
              />
            </div>
          </div>
        </div>
      </template>

      <template #footer>
        <input
          v-if="activeTab === 'profile'"
          type="submit"
          class="btn btn-info"
          :disabled="submitDisabled"
          :title="submitDisabled && !hasChanges ? 'No changes to save' : undefined"
          value="Save"
        />
        <button type="button" class="btn btn-secondary" @click="resetForm">Close</button>
      </template>
    </Modal>
  </form>
</template>

<script>
import { format } from "date-fns";

import { DialogService } from "@/services/DialogService";

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
import ConnectedAccounts from "@/components/ConnectedAccounts.vue";

import { invalidateCurrentUserCache } from "@/server_fetch_utils.js";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

export default {
  name: "EditAccountSettingsModal",
  components: {
    APIKeyHelp,
    ConnectedAccounts,
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
      savedUser: {},
      hasGravatar: null,
      apiKeys: [],
      apiKey: null,
      newKeyName: "",
      newKeyNameError: false,
      activeTab: "profile",
      groupsExpanded: false,
      addingEmail: false,
      previousContactEmail: null,
      ADD_EMAIL_OPTION: "__add_email__",
      tabs: [
        { id: "profile", label: "Profile" },
        { id: "api-keys", label: "API keys" },
        { id: "activity", label: "Activity" },
      ],
      apiKeyHelpMessage:
        'You can use your API key via the datalab-api Python package, or pass it as an HTTP header "DATALAB-API-KEY" with the tool of your choice (e.g., curl).',
    };
  },
  computed: {
    userGroups() {
      return this.user.groups ?? [];
    },
    displayNameLooksLikeEmail() {
      return Boolean(this.savedUser.display_name?.includes("@"));
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
    contactEmailOptions() {
      // Unique email identities (verified if any copy is), plus the saved contact email if missing
      const options = new Map();
      for (const identity of this.user.identities || []) {
        if (identity.identity_type !== "email") continue;
        const key = identity.identifier.toLowerCase();
        options.set(key, {
          email: identity.identifier,
          verified: Boolean(identity.verified || options.get(key)?.verified),
        });
      }
      const saved = this.savedUser.contact_email;
      if (saved && !options.has(saved.toLowerCase())) {
        options.set(saved.toLowerCase(), { email: saved, verified: false });
      }
      return [...options.values()];
    },
    emailVerificationEnabled() {
      return this.$store.state.serverInfo?.features?.auth_mechanisms?.email ?? false;
    },
    hasChanges() {
      return ["display_name", "contact_email"].some(
        (field) => (this.user[field] || null) !== (this.savedUser[field] || null),
      );
    },
    submitDisabled() {
      if (this.displayNameValidationMessage || this.contactEmailValidationMessage) return true;
      if (this.addingEmail) return !this.user.contact_email;
      // Saving an unchanged but unverified email is how a new verification email is requested
      return !this.hasChanges && !(this.contactEmailUnverified && this.emailVerificationEnabled);
    },
    contactEmailUnverified() {
      const saved = this.savedUser.contact_email?.toLowerCase();
      return Boolean(
        saved &&
        !this.contactEmailOptions.some(
          (option) => option.email.toLowerCase() === saved && option.verified,
        ),
      );
    },
    contactEmailValidationMessage() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (this.user.contact_email && !emailRegex.test(this.user.contact_email)) {
        return "Invalid email format.";
      }
      return "";
    },
  },
  watch: {
    "user.gravatar_hash": {
      handler: "checkGravatar",
      immediate: true,
    },
  },
  mounted() {
    this.getUser();
    this.loadAPIKeys();
  },
  methods: {
    async submitForm() {
      // Only send changed fields, plus an unverified contact email so its verification is re-sent
      const changes = {};
      for (const field of ["display_name", "contact_email"]) {
        if ((this.user[field] || null) !== (this.savedUser[field] || null)) {
          changes[field] = this.user[field];
        }
      }
      if (
        this.emailVerificationEnabled &&
        this.contactEmailUnverified &&
        this.user.contact_email === this.savedUser.contact_email
      ) {
        changes.contact_email = this.user.contact_email;
      }
      this.addingEmail = false;
      if (Object.keys(changes).length) {
        await saveUser(this.user.immutable_id, changes);
        this.savedUser = { ...this.savedUser, ...changes };
        invalidateCurrentUserCache();
        // Reload to pick up any new email identity and avatar hash
        await this.getUser();
      }
      this.$store.commit("setDisplayName", this.user.display_name);
      this.$emit("update:modelValue", false);
    },
    editDisplayName() {
      this.activeTab = "profile";
      this.$nextTick(() => document.getElementById("account-name")?.focus());
    },
    checkGravatar(hash) {
      // Gravatar returns a 404 (rather than a generated default) when d=404 and no avatar is set
      this.hasGravatar = null;
      if (!hash) {
        this.hasGravatar = false;
        return;
      }
      const img = new Image();
      img.onload = () => {
        if (this.user.gravatar_hash === hash) this.hasGravatar = true;
      };
      img.onerror = () => {
        if (this.user.gravatar_hash === hash) this.hasGravatar = false;
      };
      img.src = `https://www.gravatar.com/avatar/${hash}?d=404&s=1`;
    },
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.user = user;
        this.savedUser = {
          display_name: user.display_name,
          contact_email: user.contact_email,
        };
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
      const keys = await getAPIKeys();
      // Newest first; keys without a creation date (e.g., legacy keys) go last
      this.apiKeys = [...keys].sort(
        (a, b) =>
          (b.created_at ? new Date(b.created_at) : 0) - (a.created_at ? new Date(a.created_at) : 0),
      );
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
        const digest = `${result.key.slice(0, 4)}...${result.key.slice(-4)}`;
        const newKey = this.apiKeys.find((key) => key.digest === digest) ?? this.apiKeys[0];
        if (newKey) newKey.show = true;
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
    toggleGroups() {
      this.groupsExpanded = !this.groupsExpanded;
      if (this.groupsExpanded) {
        this.$nextTick(() =>
          this.$refs.groupsList?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
        );
      }
    },
    moveTabFocus(target, absolute = false) {
      const current = this.tabs.findIndex((tab) => tab.id === this.activeTab);
      const index = absolute ? target : (current + target + this.tabs.length) % this.tabs.length;
      this.activeTab = this.tabs[index].id;
      this.$nextTick(() => this.$refs.tabButtons?.[index]?.focus());
    },
    selectContactEmail(value) {
      if (value === this.ADD_EMAIL_OPTION) {
        this.previousContactEmail = this.user.contact_email;
        this.user.contact_email = "";
        this.addingEmail = true;
        this.$nextTick(() => this.$refs.newEmailInput?.focus());
      } else {
        this.user.contact_email = value || null;
      }
    },
    cancelAddEmail() {
      this.user.contact_email = this.previousContactEmail;
      this.addingEmail = false;
    },
    resetForm() {
      if (this.addingEmail) this.cancelAddEmail();
      this.apiKeyDisplayed = false;
      this.apiKey = null;
      // A generated key is only available once, so stop showing its (now empty) input
      this.apiKeys.forEach((key) => {
        key.show = false;
      });
      this.newKeyName = "";
      this.newKeyNameError = false;
      this.activeTab = "profile";
      this.groupsExpanded = false;
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

.nav-tabs .nav-link {
  color: #0056b3;
  font-weight: 600;
  background-color: transparent;
}

.nav-tabs .nav-link.active {
  color: #003d82;
}

.account-tab {
  min-height: 18rem;
}

.groups-toggle {
  color: inherit;
  font-weight: 400;
  text-decoration: none;
}

.groups-toggle:disabled {
  cursor: default;
  opacity: 1;
}

.groups-chevron {
  font-size: 0.7em;
}

.account-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-areas:
    "sidebar"
    "tabs"
    "panes";
}

.account-sidebar {
  grid-area: sidebar;
  margin-bottom: 1rem;
  padding: 1.25rem 1rem;
  text-align: center;
  overflow-wrap: anywhere;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  align-self: start;
}

.account-sidebar :deep(.avatar) {
  border: 4px solid white;
  box-shadow:
    0 0 0 1px #dee2e6,
    0 6px 16px rgba(0, 0, 0, 0.12);
  transition: box-shadow 0.2s ease;
}

.account-sidebar :deep(.avatar:hover) {
  border: 4px solid white;
  box-shadow:
    0 0 0 2px #80bdff,
    0 6px 16px rgba(0, 0, 0, 0.16);
}

.account-name {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.3;
}

.account-layout > .nav-tabs {
  grid-area: tabs;
}

.account-panes {
  grid-area: panes;
  min-width: 0;
}

/* Soft shadows at the top/bottom edges of a scrollable area when more content is hidden */
.scroll-shadows {
  background:
    linear-gradient(white 30%, rgba(255, 255, 255, 0)) center top,
    linear-gradient(rgba(255, 255, 255, 0), white 70%) center bottom,
    radial-gradient(farthest-side at 50% 0, rgba(0, 0, 0, 0.15), rgba(0, 0, 0, 0)) center top,
    radial-gradient(farthest-side at 50% 100%, rgba(0, 0, 0, 0.15), rgba(0, 0, 0, 0)) center bottom;
  background-repeat: no-repeat;
  background-size:
    100% 40px,
    100% 40px,
    100% 12px,
    100% 12px;
  background-attachment: local, local, scroll, scroll;
}

@media (min-width: 992px) {
  .modal-enclosure :deep(.modal-dialog) {
    max-width: 960px;
  }

  .account-layout {
    grid-template-columns: 13rem minmax(0, 1fr);
    grid-template-rows: auto min(25rem, 60vh);
    grid-template-areas:
      ". tabs"
      "sidebar panes";
    column-gap: 1.5rem;
  }

  .account-sidebar {
    align-self: stretch;
    margin-bottom: 0;
    overflow-y: auto;
  }

  .account-panes {
    overflow-y: auto;
    padding-right: 0.5rem;
  }

  .account-tab {
    min-height: 0;
  }

  /* Only the key rows scroll; the help toggle, table header and add-key input stay visible */
  .api-keys-tab {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .api-keys-tab > * {
    flex-shrink: 0;
  }

  .api-keys-tab > .api-key-list {
    flex: 0 1 auto;
    min-height: 0;
    overflow-y: auto;
  }

  .api-keys-tab :deep(.api-key-help .card) {
    max-height: 12rem;
    overflow-y: auto;
  }
}

.profile-fields {
  max-width: 32rem;
}

.account-activity :deep(.activity-graph-container) {
  margin: 0;
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
  flex: 0 0 3.75rem;
}

.api-key-revoke {
  padding: 0.125rem 0.375rem;
  font-size: 0.8rem;
}

.api-key-header {
  position: sticky;
  top: 0;
  z-index: 1;
  /* Opaque equivalent of Bootstrap's translucent border, so rows don't show through when scrolled */
  border-color: #dfdfdf;
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
  background-color: transparent;
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
