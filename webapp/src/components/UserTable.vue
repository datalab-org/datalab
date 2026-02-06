<template>
  <DynamicDataTable
    :columns="userColumns"
    :data="users"
    data-type="users"
    :global-filter-fields="['display_name', 'role', 'groupsList']"
    :show-buttons="true"
    @users-data-changed="getUsers"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getUsersList, getAdminGroupsList } from "@/server_fetch_utils.js";

export default {
  name: "UserTable",
  components: { DynamicDataTable },
  data() {
    return {
      usersList: null,
      userColumns: [
        {
          field: "account_status",
          header: "Status",
          body: "UserStatusCell",
          label: "Status",
          filter: true,
        },
        {
          field: "display_name",
          header: "Display Name",
          label: "Display Name",
          filter: true,
        },
        {
          field: "role",
          header: "Role",
          body: "UserRoleCell",
          bodyConfig: { allUsers: "allUsers" },
          label: "Role",
          filter: true,
        },
        {
          field: "groups",
          header: "Groups",
          body: "Creators",
          bodyConfig: { groups: "groups", creators: [] },
          label: "Groups",
          filter: true,
        },
        {
          field: "managers",
          header: "Managers",
          body: "UserManagersCell",
          bodyConfig: { allUsers: "allUsers" },
        },
        {
          field: "actions",
          header: "Actions",
          body: "UserActionsCell",
          bodyConfig: { allUsers: "allUsers" },
        },
      ],
    };
  },
  computed: {
    users() {
      if (!this.usersList) {
        return null;
      }
      return this.usersList.map((user) => ({
        ...user,
        allUsers: this.usersList,
        groupsList: (user.groups || []).map((g) => g.display_name).join(", "),
      }));
    },
  },
  created() {
    this.getUsers();
    this.getGroups();
  },
  methods: {
    async getUsers() {
      const data = await getUsersList();
      if (data != null) {
        const byId = {};
        data.forEach((u) => {
          byId[u.immutable_id] = u;
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

        this.usersList = data;
      }
    },
    async getGroups() {
      const groups = await getAdminGroupsList();
      if (groups && !groups.message) {
        this.$store.commit("setGroupsList", groups);
      }
    },
  },
};
</script>
