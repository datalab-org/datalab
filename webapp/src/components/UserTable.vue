<template>
  <table class="table table-hover table-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">Name</th>
        <th scope="col">Email</th>
        <th scope="col">Role</th>
        <th scope="col">Verified</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="user in users" :key="user._id">
        <td align="left">{{ user.display_name }}</td>
        <td align="left">{{ user.contact_email }}</td>
        <td align="left">
          <select
            class="dropdown"
            v-model="user.role"
            @change="confirmUpdateUserRole(user._id.$oid, $event.target.value)"
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
          </select>
        </td>
        <td align="left">
          <select v-model="test">
            <option value="verified">Verified</option>
            <option value="unverified">Unverified</option>
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
      original_users: null,
      test: "unverified",
      role: ["user", "manager", "admin"],
      tempRole: null,
    };
  },
  methods: {
    async getUsers() {
      let data = await getUsersList();
      if (data != null) {
        this.users = JSON.parse(JSON.stringify(data));
        this.original_users = JSON.parse(JSON.stringify(data));
      }
    },
    async confirmUpdateUserRole(user_id, new_role) {
      const originalCurrentUser = this.original_users.find((user) => user._id.$oid === user_id);

      if (originalCurrentUser.role === "admin") {
        window.alert("You can't change an admin's role.");
        this.users.find((user) => user._id.$oid === user_id).role = originalCurrentUser.role;
        return;
      }

      if (
        window.confirm(
          `Are you sure you want to change ${originalCurrentUser.display_name}'s role to ${new_role} ?`,
        )
      ) {
        await this.updateUserRole(user_id, new_role);
      } else {
        this.users.find((user) => user._id.$oid === user_id).role = originalCurrentUser.role;
      }
    },
    async updateUserRole(user_id, user_role) {
      await saveRole(user_id, { role: user_role });
      this.original_users = JSON.parse(JSON.stringify(this.users));
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
select {
  padding: 0.1em;
  border: 1px solid #ccc;
  border-radius: 0.25rem;
}
</style>
