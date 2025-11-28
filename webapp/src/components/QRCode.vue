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

  <div v-if="!isPublicMode" class="mt-3">
    <div class="alert alert-info">
      <strong v-if="hasExistingToken">Public QR Code Exists:</strong>
      <strong v-else>Generate Public QR Code:</strong>
      <br />
      <span v-if="hasExistingToken">
        A public QR code already exists for this item. You can generate a new token. Both tokens
        will remain valid until manually revoked by an administrator.
      </span>
      <span v-else>
        This QR code requires authentication to access. You can generate a public QR code that
        allows access without login.
      </span>
    </div>

    <button
      class="btn btn-warning w-100"
      :disabled="isGenerating"
      @click.prevent="generatePublicQRCode()"
    >
      <span v-if="isGenerating">
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Generating...
      </span>
      <span v-else-if="hasExistingToken"> <i class="fas fa-plus me-2"></i>Generate New Token </span>
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

    <button
      class="btn btn-danger w-100"
      :disabled="isInvalidating"
      @click.stop.prevent="invalidateToken"
    >
      <span v-if="isInvalidating">
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        Deleting...
      </span>
      <span v-else> <i class="fas fa-trash me-1"></i>Delete Token </span>
    </button>
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

import { DialogService } from "@/services/DialogService";

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
      return this.tokenInfo && this.publicToken === "existing-token";
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
        this.isLoading = false;
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
            this.publicToken = "existing-token";
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
      setTimeout(async () => {
        const confirmationMessage = this.hasExistingToken
          ? "This will generate a new public QR code. The old token will remain valid until manually revoked by an administrator. Are you sure you want to proceed?"
          : "This will create a QR code that can be accessed by anyone without authentication. Are you sure you want to proceed?";

        const confirmed = await DialogService.confirm({
          title: this.hasExistingToken ? "Generate New Public QR Code" : "Generate Public QR Code",
          message: confirmationMessage,
          type: "warning",
          confirmButtonText: this.hasExistingToken
            ? "Generate New Token"
            : "Generate Public QR Code",
          cancelButtonText: "Cancel",
        });

        if (!confirmed) {
          return;
        }

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
          } else {
            throw new Error(data.message || "Failed to generate access token");
          }
        } catch (error) {
          console.error("Error generating public QR code:", error);
          this.errorMessage = `Failed to generate public QR code: ${error.message}`;
        } finally {
          this.isGenerating = false;
        }
      }, 100);
    },
    async invalidateToken() {
      const confirmed = await DialogService.confirm({
        title: "Delete Public QR Code",
        message:
          "This will permanently invalidate the public QR code. Anyone with the current link will no longer be able to access this item. Are you sure?",
        type: "warning",
        confirmButtonText: "Delete Token",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

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
        } else if (response.status === 403) {
          throw new Error("Only administrators can delete public tokens.");
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
  },
};
</script>

<style scoped>
.qrcode-text-label {
  font-family: var(--font-monospace);
  font-size: 1.8rem;
}
</style>
