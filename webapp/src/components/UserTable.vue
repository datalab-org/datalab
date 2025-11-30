<template>
  <table class="table table-hover table-sm table-responsive-sm" data-testid="user-table">
    <thead>
      <tr>
        <th scope="col">Name</th>
        <th scope="col">Email</th>
        <th scope="col">Role</th>
        <th scope="col">Managers</th>
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
          <vSelect
            v-model="user.role"
            :options="roleOptions"
            :clearable="false"
            :searchable="false"
            class="form-control p-0 border-0"
            @update:model-value="(value) => confirmUpdateUserRole(user.immutable_id, value)"
          >
            <template #option="option">
              <RoleBadge :role="option.label" />
            </template>
            <template #selected-option="option">
              <RoleBadge :role="option.label" />
            </template>
          </vSelect>
        </td>
        <td align="left">
          <vSelect
            v-model="user.managers"
            :options="potentialManagersMap[user.immutable_id]"
            label="display_name"
            multiple
            placeholder="No managers"
            :clearable="false"
            class="w-100"
            @update:model-value="(value) => handleManagersChange(user.immutable_id, value)"
          >
            <template #option="option">
              <div class="d-flex align-items-center">
                <UserBubble :creator="option" :size="20" />
                <span class="ml-2">{{ option.display_name }}</span>
                <span class="ml-auto"><RoleBadge :role="option.role" /></span>
              </div>
            </template>

            <template #selected-option="option">
              <div class="d-flex align-items-center">
                <UserBubble :creator="option" :size="18" />
                <span class="ml-2 small">{{ option.display_name }}</span>
              </div>
            </template>
          </vSelect>
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
import { DialogService } from "@/services/DialogService";
import vSelect from "vue-select";
import UserBubble from "@/components/UserBubble.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import { getUsersList, saveRole, saveUser, saveUserManagers } from "@/server_fetch_utils.js";

export default {
  components: {
    RoleBadge,
    vSelect,
    UserBubble,
  },

  data() {
    return {
      users: null,
      original_users: null,
      tempRole: null,
      roleOptions: ["user", "admin", "manager"],
    };
  },
  computed: {
    potentialManagersMap() {
      if (!this.users) return {};
      const map = {};
      this.users.forEach((u) => {
        map[u.immutable_id] = this.users.filter((user) => user.immutable_id !== u.immutable_id);
      });
      return map;
    },
  },
  created() {
    this.getUsers();
  },
  methods: {
    async getUsers() {
      let data = await getUsersList();
      if (data != null) {
        const byId = {};
        data.forEach((u) => {
          const id = u.immutable_id;
          byId[id] = u;
        });

        data.forEach((user) => {
          if (!user.managers) {
            user.managers = [];
          }

          user.managers = user.managers
            .map((m) => {
              const mid = typeof m === "string" ? m : m.immutable_id;
              return byId[mid];
            })
            .filter(Boolean);
        });

        this.users = JSON.parse(JSON.stringify(data));
        this.original_users = JSON.parse(JSON.stringify(data));
      }
    },
    getPotentialManagers(userId) {
      if (!this.users) return [];

      const potentials = this.users.filter((u) => {
        const isEligible = u.immutable_id !== userId;
        return isEligible;
      });

      return potentials.sort((a, b) => (a.display_name || "").localeCompare(b.display_name || ""));
    },

    async confirmUpdateUserRole(user_id, new_role) {
      const originalCurrentUser = this.original_users.find((user) => user.immutable_id === user_id);

      if (!originalCurrentUser) {
        DialogService.error({
          title: "Error",
          message: "Original user not found (id mismatch).",
        });
        const uiUser = this.users.find((u) => u.immutable_id === user_id);
        if (uiUser) uiUser.role = uiUser.role || "user";
        return;
      }

      if (originalCurrentUser.role === "admin" && new_role !== "admin") {
        const confirmed = await DialogService.confirm({
          title: "Change Admin Role",
          message: `Are you sure you want to remove admin privileges from ${originalCurrentUser.display_name}?`,
          type: "warning",
        });
        if (!confirmed) {
          this.users.find((user) => user.immutable_id === user_id).role = originalCurrentUser.role;
          return;
        }
      }

      const confirmed = await DialogService.confirm({
        title: "Change User Role",
        message: `Are you sure you want to change ${originalCurrentUser.display_name}'s role from "${originalCurrentUser.role}" to "${new_role}"?`,
        type: "warning",
      });

      if (confirmed) {
        try {
          await this.updateUserRole(user_id, new_role);
        } catch (err) {
          this.users.find((user) => user.immutable_id === user_id).role = originalCurrentUser.role;
        }
      } else {
        this.users.find((user) => user.immutable_id === user_id).role = originalCurrentUser.role;
      }
    },

    async handleManagersChange(userId, managers) {
      if (!managers) managers = [];

      const managerIds = managers.map((m) => m.immutable_id);

      const userIndex = this.users.findIndex((u) => u.immutable_id === userId);
      const originalIndex = this.original_users.findIndex((u) => u.immutable_id === userId);

      if (userIndex === -1 || originalIndex === -1) {
        DialogService.error({
          title: "Error",
          message: "User not found.",
        });
        return;
      }

      const originalUser = this.original_users[originalIndex];
      const originalManagerIds = (originalUser?.managers || []).map((m) => m.immutable_id);

      if (JSON.stringify(managerIds.sort()) === JSON.stringify(originalManagerIds.sort())) return;

      const confirmed = await DialogService.confirm({
        title: "Update Managers",
        message: `Are you sure you want to update managers for ${this.users[userIndex].display_name}?`,
        type: "info",
      });

      if (!confirmed) {
        this.users[userIndex].managers = [...originalUser.managers];
        return;
      }

      try {
        await saveUserManagers(userId, managerIds);

        const newManagers = this.potentialManagersMap[userId].filter((u) =>
          managerIds.includes(u.immutable_id),
        );

        this.users[userIndex].managers = newManagers;
        this.original_users[originalIndex].managers = [...newManagers];
      } catch (err) {
        this.users[userIndex].managers = [...originalUser.managers];

        DialogService.error({
          title: "Error",
          message: err,
        });
      }
    },
    async confirmUpdateUserStatus(user_id, new_status) {
      const originalCurrentUser = this.original_users.find((user) => user.immutable_id === user_id);

      if (!originalCurrentUser) {
        DialogService.error({
          title: "Error",
          message: "Original user not found (id mismatch).",
        });
        return;
      }

      const confirmed = await DialogService.confirm({
        title: "Change User Status",
        message: `Are you sure you want to change ${originalCurrentUser.display_name}'s status from "${originalCurrentUser.account_status}" to "${new_status}"?`,
        type: "warning",
      });
      if (confirmed) {
        this.users.find((user) => user.immutable_id == user_id).account_status = new_status;
        try {
          await this.updateUserStatus(user_id, new_status);
        } catch (err) {
          this.users.find((user) => user.immutable_id === user_id).account_status =
            originalCurrentUser.account_status;
        }
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
  font-family: var(--font-monospace);
}
</style>
