<template>
  <Navbar />
  <h1 class="sr-only">Administration</h1>
  <div v-if="!isUserLoaded" class="admin-loading" role="status">Loading administration…</div>
  <div v-else-if="!canAccessAdminPage" class="error-message">
    <p class="error-text">You do not have permission to access this page.</p>
  </div>
  <div v-else class="admin-container d-flex flex-column flex-md-row">
    <SidebarNavigation
      title="Admin Menu"
      data-testid="admin-table"
      :items="items"
      :selected-item="selectedItem"
      @item-selected="onItemSelected"
    />
    <AdminDisplay :selected-item="selectedItem" />
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import SidebarNavigation from "@/components/SidebarNavigation.vue";
import AdminDisplay from "@/components/AdminDisplay.vue";
import { getUserInfo } from "@/server_fetch_utils.js";

export default {
  components: {
    Navbar,
    SidebarNavigation,
    AdminDisplay,
  },
  data() {
    return {
      items: ["Users", "Groups", "Access Tokens"],
      selectedItem: "Users",
      user: null,
      isUserLoaded: false,
    };
  },
  computed: {
    canAccessAdminPage() {
      return this.user?.role === "admin";
    },
  },
  created() {
    this.getUser();
  },
  methods: {
    async getUser() {
      this.user = await getUserInfo();
      this.isUserLoaded = true;
    },
    onItemSelected(item) {
      this.selectedItem = item;
    },
  },
};
</script>

<style scoped>
.admin-container {
  min-width: 0;
}

.admin-loading {
  padding: 1em;
  text-align: center;
}

.error-message {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1em;
  margin: 1em;
  background-color: #ffe6e6;
  border: 1px solid #ff9999;
  border-radius: 5px;
}
.error-text {
  margin: 0;
}
</style>
