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
        <td align="left">
          <select v-model="user.role" @change="updateUserRole(user._id.$oid, $event.target.value)">
            <option value="user">User</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
          </select>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getUsersList, saveRole } from "@/server_fetch_utils.js";

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
    async updateUserRole(user_id, role) {
      await saveRole(user_id, role);
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
