<template>
  <Navbar />
  <div class="admin-container">
    <AdminNavbar />
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import AdminNavbar from "@/components/AdminNavbar.vue";

export default {
  components: { Navbar, AdminNavbar },
  data() {
    return {};
  },
};
</script>

<style scoped>
.admin-container {
  display: flex;
}
</style>
