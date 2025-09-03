<template>
  <div class="text-center">
    <QRCodeVue3
      :key="currentQRCodeUrl"
      :value="currentQRCodeUrl"
      :width="width"
      :height="width"
      :qr-options="{ typeNumber: 0, mode: 'Byte', errorCorrectionLevel: 'Q' }"
      :image-options="{ hideBackgroundDots: false, imageSize: 0, margin: 0 }"
      :dots-options="{
        type: 'square',
        color: 'black',
      }"
      :background-options="{ color: '#ffffff' }"
      :corners-square-options="{ type: 'square', color: 'black' }"
      :corners-dot-options="{ type: 'square', color: 'black' }"
      file-ext="png"
    />

    <div
      id="qrcode-text-label"
      :style="{ width: width }"
      class="qrcode-text-label mx-auto text-center center-text"
    >
      {{ refcode }}
    </div>

    <div class="mt-2">
      <span v-if="!isPublicMode" class="badge bg-primary">Private QR Code</span>
      <span v-else class="badge bg-warning text-dark">Public QR Code</span>
    </div>
  </div>

  <div v-if="isLoading" class="text-center mt-3">
    <div class="spinner-border spinner-border-sm" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <small class="d-block mt-1">Checking existing tokens...</small>
  </div>

  <div v-else-if="!isPublicMode" class="mt-3">
    <div class="alert alert-info">
      <strong>Generate Public QR Code:</strong><br />
      This QR code requires authentication to access. You can generate a public QR code that allows
      access without login.
    </div>

    <button
      class="btn btn-warning w-100"
      :disabled="isGenerating"
      @click.prevent="hasExistingToken ? switchToPublic() : generatePublicQRCode()"
    >
      <span v-if="isGenerating">
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Generating...
      </span>
      <span v-else-if="hasExistingToken"> <i class="fas fa-eye me-2"></i>View Public QR Code </span>
      <span v-else> <i class="fas fa-unlock me-2"></i>Generate Public QR Code </span>
    </button>
  </div>

  <div v-else class="mt-3">
    <div class="alert alert-warning">
      <strong><i class="fas fa-exclamation-triangle me-2"></i>Public QR Code Active</strong><br />
      This QR code can be accessed by anyone with the link. No authentication required.
      <div class="mt-2">
        <small><strong>Created:</strong> {{ formattedCreationDate }}</small>
      </div>
    </div>

    <div class="d-flex justify-content-center">
      <button class="btn btn-sm btn-outline-primary mr-2" @click="switchToPrivate">
        <i class="fas fa-eye me-1"></i>View Private QRCode
      </button>
      <button
        class="btn btn-sm btn-outline-danger"
        :disabled="isInvalidating"
        @click="invalidateToken"
      >
        <i class="fas fa-trash me-1"></i>Delete Token
      </button>
    </div>
  </div>

  <div v-if="errorMessage" class="alert alert-danger mt-3">
    <i class="fas fa-exclamation-triangle me-2"></i>{{ errorMessage }}
  </div>

  <div v-if="!federatedQR" class="alert alert-info mt-3">
    QR_CODE_RESOLVER_URL is not set to the federation resolver URL for this deployment.<br />
    Links embedded within QR codes generated here will only work if this <i>datalab</i> instance
    remains at the same URL.<br /><br />

    Visit <a :href="federationQRCodeUrl">{{ federationQRCodeUrl }}</a> to learn about persistent URL
    resolution in <i>datalab</i>.
  </div>
</template>

<script>
import QRCodeVue3 from "qrcode-vue3";
import { FEDERATION_QR_CODE_RESOLVER_URL, QR_CODE_RESOLVER_URL, API_URL } from "@/resources.js";

export default {
  name: "QRCode",
  components: {
    QRCodeVue3,
  },
  props: {
    refcode: {
      type: String,
      required: true,
    },
    width: {
      type: Number,
      default: 200,
    },
  },
  emits: ["public-token-generated", "public-token-invalidated"],
  data() {
    return {
      federationQRCodeUrl: FEDERATION_QR_CODE_RESOLVER_URL,
      isPublicMode: false,
      publicToken: null,
      tokenInfo: null,
      isLoading: false,
      isGenerating: false,
      isInvalidating: false,
      errorMessage: null,
    };
  },
  computed: {
    federatedQR() {
      return FEDERATION_QR_CODE_RESOLVER_URL == QR_CODE_RESOLVER_URL;
    },
    privateQRCodeUrl() {
      if (QR_CODE_RESOLVER_URL == null) {
        return API_URL + "/items/" + this.refcode + "?redirect-to-ui=true";
      }
      return QR_CODE_RESOLVER_URL + "/" + this.refcode;
    },
    publicQRCodeUrl() {
      if (!this.publicToken) return this.privateQRCodeUrl;

      if (QR_CODE_RESOLVER_URL == null) {
        return `${API_URL}/items/${this.refcode}?redirect-to-ui=true&at=${this.publicToken}`;
      }
      return `${QR_CODE_RESOLVER_URL}/${this.refcode}?at=${this.publicToken}`;
    },
    currentQRCodeUrl() {
      const url = this.isPublicMode ? this.publicQRCodeUrl : this.privateQRCodeUrl;
      return url;
    },
    formattedCreationDate() {
      if (!this.tokenInfo?.created_at) return "Unknown";

      try {
        const date = new Date(this.tokenInfo.created_at);
        return date.toLocaleDateString() + " at " + date.toLocaleTimeString();
      } catch {
        return "Unknown";
      }
    },
    hasExistingToken() {
      return this.publicToken === "existing-token";
    },
  },
  mounted() {
    this.checkExistingToken();
  },
  beforeUnmount() {
    this.errorMessage = null;
  },
  methods: {
    async checkExistingToken() {
      this.isLoading = true;
      this.errorMessage = null;

      const urlParams = new URLSearchParams(window.location.search);
      const accessToken = urlParams.get("at");
      if (accessToken) {
        return;
      }

      try {
        const response = await fetch(`${API_URL}/items/${this.refcode}/access-token-info`, {
          method: "GET",
          credentials: "include",
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          if (data.has_token) {
            this.tokenInfo = data.token_info;
            this.isPublicMode = true;
            this.publicToken = data.token_info.token;
          }
        } else if (response.status === 404) {
          console.debug("No access to item or item not found");
        } else {
          console.warn("Error checking token:", data.message);
        }
      } catch (error) {
        console.error("Error checking existing token:", error);
      } finally {
        this.isLoading = false;
      }
    },

    async generatePublicQRCode() {
      this.isGenerating = true;

      try {
        const response = await fetch(`${API_URL}/items/${this.refcode}/issue-access-token`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          this.publicToken = data.token;
          this.isPublicMode = true;
          this.tokenInfo = {
            created_at: new Date().toISOString(),
            created_by: this.$store.state.currentUserID,
          };
          this.$emit("public-token-generated", {
            refcode: this.refcode,
            token: data.token,
          });
        } else if (response.status === 409) {
          this.errorMessage =
            "A public QR code already exists for this item. Please refresh the page to see it.";
          this.checkExistingToken();
        } else {
          throw new Error(data.message || "Failed to generate access token");
        }
      } catch (error) {
        console.error("Error generating public QR code:", error);
        this.errorMessage = `Failed to generate public QR code: ${error.message}`;
      } finally {
        this.isGenerating = false;
      }
    },

    async invalidateToken() {
      this.isInvalidating = true;
      this.errorMessage = null;

      try {
        const response = await fetch(`${API_URL}/items/${this.refcode}/invalidate-access-token`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          this.publicToken = null;
          this.tokenInfo = null;
          this.isPublicMode = false;
          this.showInvalidateConfirm = false;
          this.$emit("public-token-invalidated", { refcode: this.refcode });
        } else {
          throw new Error(data.detail || data.message || "Failed to invalidate token");
        }
      } catch (error) {
        console.error("Error invalidating token:", error);
        this.errorMessage = `Failed to invalidate token: ${error.message}`;
      } finally {
        this.isInvalidating = false;
      }
    },

    switchToPrivate() {
      this.isPublicMode = false;
      this.errorMessage = null;
    },
    switchToPublic() {
      this.isPublicMode = true;
      this.errorMessage = null;
    },
  },
};
</script>

<style scoped>
.qrcode-text-label {
  font-family: var(--font-monospace);
  font-size: 1.8rem;
}
</style>
