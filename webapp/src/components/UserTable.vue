<template>
  <table class="table table-hover table-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Name</th>
        <th scope="col">Role</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="user in users" :key="user._id">
        <td align="left">{{ user._id.$oid }}</td>
        <td align="left">{{ user.display_name }}</td>
        <td align="left">{{ user.role }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getUsersList } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      users: null,
    };
  },
  methods: {
    async getUsers() {
      let data = await getUsersList();
      if (data != null) {
        this.users = data;
      }
    },
  },
  created() {
    this.getUsers();
  },
};
</script>

<style scoped>
.table-item-id {
  font-size: 1.2em;
  font-weight: normal;
}
</style>
