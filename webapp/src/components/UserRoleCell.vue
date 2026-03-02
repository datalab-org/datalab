<template>
  <div class="role-cell-wrapper">
    <vSelect
      v-model="localRole"
      :options="roleOptions"
      :clearable="false"
      :searchable="false"
      @open="onDropdownOpen"
      @close="onDropdownClose"
      @update:model-value="handleRoleChange"
    >
      <template #option="option">
        <RoleBadge :role="option.label" />
      </template>
      <template #selected-option="option">
        <RoleBadge :role="option.label" />
      </template>
    </vSelect>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import vSelect from "vue-select";
import RoleBadge from "@/components/RoleBadge.vue";
import { saveRole } from "@/server_fetch_utils.js";

export default {
  name: "UserRoleCell",
  components: {
    RoleBadge,
    vSelect,
  },
  props: {
    user: {
      type: Object,
      required: true,
    },
    allUsers: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      roleOptions: ["user", "admin", "manager"],
      localRole: this.user?.role || "user",
    };
  },
  watch: {
    "user.role"(newVal) {
      if (newVal !== undefined) {
        this.localRole = newVal;
      }
    },
  },
  methods: {
    onDropdownOpen() {
      const cell = this.$el.closest("td");
      const row = this.$el.closest("tr");
      if (cell) {
        cell.style.overflow = "visible";
        cell.style.zIndex = "1000";
        cell.style.position = "relative";
      }
      if (row) {
        row.style.zIndex = "1000";
      }
    },
    onDropdownClose() {
      const cell = this.$el.closest("td");
      const row = this.$el.closest("tr");
      if (cell) {
        cell.style.overflow = "";
        cell.style.zIndex = "";
        cell.style.position = "";
      }
      if (row) {
        row.style.zIndex = "";
      }
    },
    async handleRoleChange(newRole) {
      const originalRole = this.localRole;

      if (originalRole === "admin" && newRole !== "admin") {
        const confirmed = await DialogService.confirm({
          title: "Change Admin Role",
          message: `Are you sure you want to remove admin privileges from ${this.user.display_name}?`,
          type: "warning",
        });
        if (!confirmed) {
          this.localRole = originalRole;
          return;
        }
      }

      const confirmed = await DialogService.confirm({
        title: "Change User Role",
        message: `Are you sure you want to change ${this.user.display_name}'s role from "${originalRole}" to "${newRole}"?`,
        type: "warning",
      });

      if (confirmed) {
        try {
          await saveRole(this.user.immutable_id, { role: newRole });

          const userInArray = this.allUsers.find((u) => u.immutable_id === this.user.immutable_id);
          if (userInArray) {
            userInArray.role = newRole;
          }
          this.localRole = newRole;
        } catch (err) {
          this.localRole = originalRole;
          DialogService.error({
            title: "Error",
            message: "Failed to update user role.",
          });
        }
      } else {
        this.localRole = originalRole;
      }
    },
  },
};
</script>

<style scoped>
.role-cell-wrapper {
  position: relative;
  z-index: auto;
}

.role-cell-wrapper :deep(.vs--open) {
  z-index: 1001;
}

.role-cell-wrapper :deep(.vs__dropdown-menu) {
  z-index: 1001;
  position: absolute;
}
</style>
