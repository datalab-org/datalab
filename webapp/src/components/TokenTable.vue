<template>
  <table class="table table-hover table-sm" data-testid="tokens-table">
    <thead>
      <tr>
        <th scope="col">Item</th>
        <th scope="col">Token Status</th>
        <th scope="col">Refcode</th>
        <th scope="col">Item Type</th>
        <th scope="col">Created By</th>
        <th scope="col">Date Created</th>
        <th scope="col">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-if="isLoading">
        <td colspan="6" class="text-center">
          <div class="spinner-border spinner-border-sm" role="status"></div>
          Loading tokens...
        </td>
      </tr>
      <tr v-else-if="tokens.length === 0">
        <td colspan="6" class="text-center text-muted">No access tokens found</td>
      </tr>
      <tr v-for="token in sortedTokens" v-else :key="token._id">
        <td align="left">
          <FormattedItemName
            v-if="token.item_id"
            :item_id="token.item_id"
            :item-type="token.item_type"
            enable-click
          />
        </td>
        <td align="left">
          <span v-if="token.active" class="badge badge-success text-uppercase"> Active </span>
          <span v-else class="badge badge-danger text-uppercase"> Invalidated </span>
        </td>
        <td align="left">
          <FormattedRefcode
            :refcode="token.refcode"
            :enable-q-r-code="token.item_type !== 'deleted'"
          />
        </td>
        <td align="left">{{ token.item_type || "Unknown" }}</td>
        <td>
          <div v-if="token.created_by_info" class="d-flex align-items-center">
            <UserBubble :creator="token.created_by_info" :size="24" />
            <span class="ms-2">{{ token.created_by_info.display_name }}</span>
          </div>
          <span v-else class="text-muted">Unknown</span>
        </td>
        <td align="left">{{ formatDate(token.created_at) }}</td>
        <td align="left">
          <button
            v-if="token.active"
            class="btn btn-outline-danger btn-sm text-uppercase text-monospace"
            :disabled="invalidatingTokens.has(token._id)"
            @click="confirmInvalidateToken(token)"
          >
            <span v-if="invalidatingTokens.has(token._id)"> Invalidating... </span>
            <span v-else> Invalidate </span>
          </button>
          <button
            v-else
            class="btn btn-outline-secondary btn-sm text-uppercase text-monospace"
            disabled
          >
            Invalidated
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { API_URL } from "@/resources.js";

import { DialogService } from "@/services/DialogService";

import FormattedItemName from "@/components/FormattedItemName.vue";
import FormattedRefcode from "@/components/FormattedRefcode.vue";
import UserBubble from "@/components/UserBubble.vue";

export default {
  name: "TokenTable",
  components: {
    FormattedRefcode,
    FormattedItemName,
    UserBubble,
  },
  data() {
    return {
      tokens: [],
      isLoading: false,
      invalidatingTokens: new Set(),
    };
  },
  computed: {
    sortedTokens() {
      return [...this.tokens].sort((a, b) => {
        if (a.active !== b.active) {
          return a.active ? -1 : 1;
        }
        return new Date(b.created_at) - new Date(a.created_at);
      });
    },
  },

  created() {
    this.loadTokens();
  },

  methods: {
    async loadTokens() {
      this.isLoading = true;

      try {
        const response = await fetch(`${API_URL}/access-tokens`, {
          method: "GET",
          credentials: "include",
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          this.tokens = data.tokens;
        } else {
          console.error("Failed to load tokens:", data.message);
        }
      } catch (error) {
        console.error("Error loading tokens:", error);
      } finally {
        this.isLoading = false;
      }
    },
    async confirmInvalidateToken(token) {
      const confirmed = await DialogService.confirm({
        title: "Invalidate Access Token",
        message: `Are you sure you want to invalidate the access token for <strong>${token.item_id}</strong> (${token.refcode})? <br><br>This action cannot be undone and will immediately block access for anyone using this token.`,
        type: "error",
        confirmButtonText: "Invalidate Token",
        cancelButtonText: "Cancel",
      });

      if (confirmed) {
        await this.invalidateToken(token);
      }
    },
    async invalidateToken(token) {
      this.invalidatingTokens.add(token._id);

      try {
        const response = await fetch(`${API_URL}/items/${token.refcode}/invalidate-access-token`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: "admin-invalidation",
          }),
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
          // Mettre à jour le token dans la liste
          const index = this.tokens.findIndex((t) => t._id === token._id);
          if (index !== -1) {
            this.tokens[index].active = false;
            this.tokens[index].invalidated_at = new Date().toISOString();
          }
        } else {
          alert(`Failed to invalidate token: ${data.detail || data.message}`);
        }
      } catch (error) {
        console.error("Error invalidating token:", error);
        alert(`Error invalidating token: ${error.message}`);
      } finally {
        this.invalidatingTokens.delete(token._id);
      }
    },

    formatDate(dateString) {
      if (!dateString) return "Unknown";
      try {
        return new Date(dateString).toLocaleDateString();
      } catch {
        return "Invalid date";
      }
    },
  },
};
</script>

<style scoped>
td {
  vertical-align: middle;
}

.table-item-id {
  font-size: 1.2em;
  font-weight: normal;
}
</style>
