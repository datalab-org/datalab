<template>
  <table class="table table-hover table-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">Name</th>
        <th scope="col">Email</th>
        <th scope="col">Role</th>
        <th scope="col">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="user in users" :key="user.immutable_id">
        <td align="left">
          {{ user.display_name }}
          <span v-if="user.account_status === 'active'" class="badge badge-success text-uppercase">
            Active
          </span>
          <span
            v-else-if="user.account_status === 'unverified'"
            class="badge badge-warning text-uppercase"
          >
            Unverified
          </span>
          <span
            v-else-if="user.account_status === 'deactivated'"
            class="badge badge-danger text-uppercase"
          >
            Deactivated
          </span>
        </td>
        <td align="left">{{ user.contact_email }}</td>
        <td align="left">
          <select
            v-model="user.role"
            class="dropdown"
            @change="confirmUpdateUserRole(user.immutable_id, $event.target.value)"
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
          </select>
        </td>
        <td align="left">
          <button
            v-if="user.account_status === 'active'"
            class="btn btn-outline-danger btn-sm text-uppercase text-monospace"
            @click="confirmUpdateUserStatus(user.immutable_id, 'deactivated')"
          >
            Deactivate
          </button>
          <button
            v-else-if="user.account_status === 'unverified'"
            class="btn btn-outline-success btn-sm text-uppercase text-monospace"
            @click="confirmUpdateUserStatus(user.immutable_id, 'active')"
          >
            Activate
          </button>
          <button
            v-else-if="user.account_status === 'deactivated'"
            class="btn btn-outline-success btn-sm text-uppercase text-monospace"
            @click="confirmUpdateUserStatus(user.immutable_id, 'active')"
          >
            Activate
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getUsersList, saveRole, saveUser } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      users: null,
      original_users: null,
      tempRole: null,
    };
  },
  created() {
    this.getUsers();
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
      const originalCurrentUser = this.original_users.find((user) => user.immutable_id === user_id);

      if (originalCurrentUser.role === "admin") {
        window.alert("You can't change an admin's role.");
        this.users.find((user) => user.immutable_id === user_id).role = originalCurrentUser.role;
        return;
      }

      if (
        window.confirm(
          `Are you sure you want to change ${originalCurrentUser.display_name}'s role to ${new_role} ?`,
        )
      ) {
        await this.updateUserRole(user_id, new_role);
      } else {
        this.users.find((user) => user.immutable_id === user_id).role = originalCurrentUser.role;
      }
    },
    async confirmUpdateUserStatus(user_id, new_status) {
      const originalCurrentUser = this.original_users.find((user) => user.immutable_id === user_id);

      if (
        window.confirm(
          `Are you sure you want to change ${originalCurrentUser.display_name}'s status from "${originalCurrentUser.account_status}" to "${new_status}" ?`,
        )
      ) {
        this.users.find((user) => user.immutable_id == user_id).account_status = new_status;
        await this.updateUserStatus(user_id, new_status);
      } else {
        this.users.find((user) => user.immutable_id === user_id).account_status =
          originalCurrentUser.account_status;
      }
    },
    async updateUserRole(user_id, user_role) {
      await saveRole(user_id, { role: user_role });
      this.original_users = JSON.parse(JSON.stringify(this.users));
    },
    async updateUserStatus(user_id, status) {
      await saveUser(user_id, { account_status: status });
      this.original_users = JSON.parse(JSON.stringify(this.users));
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
select {
  border: 1px solid #ccc;
  border-radius: 0.25rem;
}

.badge {
  margin-left: 1em;
  font-family: "Andalé Mono", monospace;
}
</style>
