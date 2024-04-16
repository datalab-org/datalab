<template>
  <Navbar />
  <div v-if="!user || (user && user.role !== 'admin')" class="error-message">
    <p class="error-text">You do not have permission to access this page.</p>
  </div>
  <div v-else class="admin-container">
    <AdminNavbar :items="items" @item-selected="onItemSelected" />
    <AdminDisplay :selectedItem="selectedItem" />
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import AdminNavbar from "@/components/AdminNavbar.vue";
import AdminDisplay from "@/components/AdminDisplay.vue";
import { getUserInfo } from "@/server_fetch_utils.js";

export default {
  components: {
    Navbar,
    AdminNavbar,
    AdminDisplay,
  },
  data() {
    return {
      // Disable collections and samples for now, until we can add the functionality in a future PR
      items: ["Users"], // , "Collections", "Samples"],
      selectedItem: "Users",
      user: null,
    };
  },
  async mounted() {
    await this.getUser();
  },
  methods: {
    async getUser() {
      const user = await getUserInfo();
      if (user !== null) {
        this.user = user;
      }
    },
    onItemSelected(item) {
      this.selectedItem = item;
    },
  },
};
</script>

<style scoped>
.admin-container {
  display: flex;
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
