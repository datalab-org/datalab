<template>
  <DynamicDataTable
    :columns="userColumns"
    :data="users"
    data-type="users"
    :global-filter-fields="['display_name', 'role', 'groupsList']"
    :show-buttons="true"
    :all-users="usersList || []"
    @users-data-changed="getUsers"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getUsersList, getAdminGroupsList } from "@/server_fetch_utils.js";

import UserStatusCell from "@/components/UserStatusCell";
import UserRoleCell from "@/components/UserRoleCell";
import UserGroupsCell from "@/components/UserGroupsCell";
import UserManagersCell from "@/components/UserManagersCell";
import UserActionsCell from "@/components/UserActionsCell";
import RoleBadge from "@/components/RoleBadge";
import Creators from "@/components/Creators";

import TextFilter from "@/components/TextFilter";
import MultiSelectFilter from "@/components/MultiSelectFilter";
import SingleSelectFilter from "@/components/SingleSelectFilter";

import { FilterOperator, FilterMatchMode } from "@primevue/core/api";

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
          label: "Status",
          body: {
            component: UserStatusCell,
            props: (row) => ({ status: row.account_status }),
          },
          filter: {
            component: SingleSelectFilter,
            componentProps: {
              placeholder: "Any",
              showClear: true,
              optionComponent: UserStatusCell,
              optionProps: (opt) => ({ status: opt }),
              valueComponent: UserStatusCell,
              valueProps: (val) => ({ status: val }),
            },
            match: (value, filterValue) => {
              if (!filterValue) return true;
              return value === filterValue;
            },
            operator: FilterOperator.OR,
            options: () => ["active", "unverified", "deactivated"],
          },
        },
        {
          field: "display_name",
          header: "Display Name",
          label: "Display Name",
          filter: {
            component: TextFilter,
            componentProps: { placeholder: "Search by name" },
            matchMode: FilterMatchMode.CONTAINS,
            operator: FilterOperator.AND,
          },
        },
        {
          field: "role",
          header: "Role",
          label: "Role",
          body: {
            component: UserRoleCell,
            props: (row) => ({ user: row, allUsers: row.allUsers || [] }),
          },
          filter: {
            component: SingleSelectFilter,
            componentProps: {
              placeholder: "Any",
              showClear: true,
              optionComponent: RoleBadge,
              optionProps: (opt) => ({ role: opt }),
              valueComponent: RoleBadge,
              valueProps: (val) => ({ role: val }),
            },
            match: (value, filterValue) => {
              if (!filterValue) return true;
              return value === filterValue;
            },
            operator: FilterOperator.OR,
            options: () => ["user", "admin", "manager"],
          },
        },
        {
          field: "groups",
          header: "Groups",
          label: "Groups",
          body: {
            component: UserGroupsCell,
            props: (row) => ({ user: row, allGroups: row.allGroups || [] }),
          },
          filter: {
            component: MultiSelectFilter,
            componentProps: {
              optionLabel: "display_name",
              placeholder: "Any",
              optionComponent: Creators,
              optionProps: (opt) => ({ groups: [opt], creators: [], showNames: true }),
              valueComponent: Creators,
              valueProps: (val) => ({ groups: [val], creators: [], showNames: false }),
            },
            match: (value, filterValue) => {
              if (!filterValue || (Array.isArray(filterValue) && filterValue.length === 0))
                return true;
              if (!value || !Array.isArray(value)) return false;
              if (Array.isArray(filterValue)) {
                return filterValue.some((f) =>
                  value.some((group) => String(group.immutable_id) === String(f.immutable_id)),
                );
              }
              return value.some(
                (group) => String(group.immutable_id) === String(filterValue.immutable_id),
              );
            },
            operator: FilterOperator.AND,
            options: (data) => {
              const allGroups = data.flatMap((user) => user.groups || []);
              const uniqueGroupsMap = new Map();
              allGroups.forEach((group) => {
                if (group && group.immutable_id) {
                  uniqueGroupsMap.set(group.immutable_id, { ...group });
                }
              });
              return Array.from(uniqueGroupsMap.values());
            },
          },
        },
        {
          field: "managers",
          header: "Managers",
          body: {
            component: UserManagersCell,
            props: (row) => ({ user: row, allUsers: row.allUsers || [] }),
          },
        },
        {
          field: "actions",
          header: "Actions",
          sortable: false,
          body: {
            component: UserActionsCell,
            props: (row) => ({ user: row, allUsers: row.allUsers || [] }),
          },
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
        allGroups: this.$store.state.groups_list || [],
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
        const byId = Object.fromEntries(data.map((u) => [u.immutable_id, u]));
        this.usersList = data.map((user) => ({
          ...user,
          managers: (user.managers || [])
            .map((m) => byId[typeof m === "string" ? m : m.immutable_id])
            .filter(Boolean),
        }));
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
