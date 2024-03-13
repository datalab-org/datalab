<template>
  <form @submit.prevent="submitForm" class="modal-enclosure">
    <Modal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)">
      <template v-slot:header> Account settings </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="account-name" class="col-form-label">Name:</label>
            <input
              v-model="user.display_name"
              type="text"
              class="form-control"
              id="account-name"
              required
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
            <label for="account-name" class="col-form-label">Contact email:</label>
            <input
              v-model="user.contact_email"
              type="text"
              class="form-control"
              id="account-name"
              placeholder="Please enter your email"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-6">
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
              ><font-awesome-icon :icon="['fab', 'github']" /> Login via GitHub</a
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
              <font-awesome-icon :icon="['fab', 'github']" />
              {{ user.identities.find((identity) => identity.identity_type === "orcid").name }}
            </a>
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
import { API_URL } from "@/resources.js";
import Modal from "@/components/Modal.vue";
import { getUserInfo, saveUser } from "@/server_fetch_utils.js";
export default {
  name: "EditAccountSettingsModal",
  data() {
    return {
      user: {
        display_name: null,
        contact_email: null,
        identities: [],
      },
      apiUrl: API_URL,
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  methods: {
    async submitForm() {
      await saveUser(this.user.immutable_id, this.user).then(() => {
        this.$store.commit("setDisplayName", this.user.display_name);
        this.$emit("update:modelValue", false);
      });
    },
    async getUser() {
      let user = await getUserInfo();
      if (user != null) {
        this.user = user;
      }
    },
    resetForm() {
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
