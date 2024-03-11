<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)">
      <template v-slot:header> Account settings </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="account-name" class="col-form-label">Name:</label>
            <input
              v-model="currentUser"
              type="text"
              class="form-control"
              id="account-name"
              required
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <a
              v-if="currentUserGithub !== null"
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              ><font-awesome-icon :icon="['fab', 'github']" /> Logged with GitHub</a
            >
            <a
              v-else
              type="button"
              class="dropdown-item btn login btn-link btn-default"
              aria-label="Login via GitHub"
              :href="this.apiUrl + '/login/github'"
              ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
            >
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <a
              v-if="currentUserOrchid !== null"
              type="button"
              class="disabled dropdown-item btn login btn-link btn-default"
              ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Logged with
              ORCID</a
            >
            <a
              v-else
              type="button"
              class="disabled dropdown-item btn login btn-link btn-default"
              aria-label="Login via ORCID"
              :href="this.apiUrl + '/login/orcid'"
              ><font-awesome-icon class="orcid-icon" :icon="['fab', 'orcid']" /> Login via ORCID</a
            >
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import { getUserInfo, saveUser } from "@/server_fetch_utils.js";
import { API_URL } from "@/resources.js";
export default {
  name: "EditAccountSettingsModal",
  data() {
    return {
      originalUserName: "",
      currentUser: "",
      currentUserInfos: "",
      currentUserGithub: "",
      currentUserOrchid: "",
      apiUrl: API_URL,
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  methods: {
    async submitForm() {
      await saveUser(this.currentUserInfos.immutable_id, this.currentUser).then(() => {
        this.$emit("update:modelValue", false);
        this.originalUserName = this.currentUser;
      });
    },
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.currentUserInfos = user;
        this.currentUser = user.display_name;

        const githubIdentity = user.identities.find(
          (identity) => identity.identity_type === "github",
        );
        this.currentUserGithub = githubIdentity ? githubIdentity : null;

        const orchidIdentity = user.identities.find(
          (identity) => identity.identity_type === "orchid",
        );
        this.currentUserOrchid = orchidIdentity ? orchidIdentity : null;
      }
    },
    resetForm() {
      this.currentUser = this.originalUserName;
      this.$emit("update:modelValue", false);
    },
  },
  mounted() {
    this.getUser();
  },
  components: {
    Modal,
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
