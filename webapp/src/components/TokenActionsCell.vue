<template>
  <span class="mx-auto" style="text-align: center">
    <button
      v-if="token.active"
      class="btn btn-outline-danger token-action-button"
      :disabled="isInvalidating"
      @click="handleInvalidate"
    >
      <span v-if="isInvalidating">Invalidating...</span>
      <span v-else>Invalidate</span>
    </button>
    <button v-else class="btn btn-outline-secondary token-action-button" disabled>
      Invalidated
    </button>
  </span>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import { invalidateToken } from "@/server_fetch_utils.js";

export default {
  name: "TokenActionsCell",
  props: {
    token: {
      type: Object,
      required: true,
    },
    allTokens: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      isInvalidating: false,
    };
  },
  methods: {
    async handleInvalidate() {
      const confirmed = await DialogService.confirm({
        title: "Invalidate Access Token",
        message: `Are you sure you want to invalidate the access token for <strong>${this.token.item_id}</strong> (${this.token.refcode})?<br><br>This action cannot be undone and will immediately block access for anyone using this token.`,
        type: "error",
        confirmButtonText: "Invalidate Token",
        cancelButtonText: "Cancel",
      });

      if (!confirmed) {
        return;
      }

      this.isInvalidating = true;

      try {
        await invalidateToken(this.token.refcode);

        const tokenInArray = this.allTokens.find((t) => t._id === this.token._id);
        if (tokenInArray) {
          tokenInArray.active = false;
          tokenInArray.invalidated_at = new Date().toISOString();
        }
      } catch (error) {
        console.error("Error invalidating token:", error);
        await DialogService.error({
          title: "Error",
          message: `Error invalidating token: ${error.message}`,
        });
      } finally {
        this.isInvalidating = false;
      }
    },
  },
};
</script>

<style scoped>
.token-action-button {
  font-family: var(--font-monospace);
  text-transform: uppercase;
  font-size: 0.8em;
  padding: 0.15rem 0.3rem;
  border: 2px solid;
}
</style>
