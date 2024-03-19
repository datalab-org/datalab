<template>
  <div class="sidebar">
    <a @click="selectItem('User')">User</a>
    <a @click="selectItem('Collection')">Collection</a>
    <a @click="selectItem('Sample')">Sample</a>
  </div>
  <div class="admin-display">
    <AdminDisplay :selectedItem="selectedItem" />
  </div>
</template>

<script>
import AdminDisplay from "@/components/AdminDisplay.vue";

export default {
  components: { AdminDisplay },
  data() {
    return {
      selectedItem: "User",
    };
  },
  methods: {
    selectItem(item) {
      this.selectedItem = item;
    },
  },
  name: "AdminNavbar",
};
</script>

<style scoped>
.sidebar {
  padding: 1em;
  margin: 0.5em;
  background-color: lightgreen;
  border: 1px solid lightgreen;
  border-radius: 0.5em;
}
.sidebar a {
  display: block;
  margin-bottom: 15px;
  cursor: pointer;
}
.admin-display {
  display: flex;
  width: 100%;
}
</style>
