<template>
  <div class="managers-cell-wrapper">
    <vSelect
      v-model="localManagers"
      :options="potentialManagers"
      label="display_name"
      multiple
      placeholder="No managers"
      :clearable="false"
      :taggable="false"
      @open="onDropdownOpen"
      @close="onDropdownClose"
      @update:model-value="handleManagersChange"
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
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import vSelect from "vue-select";
import UserBubble from "@/components/UserBubble.vue";
import RoleBadge from "@/components/RoleBadge.vue";
import { saveUserManagers } from "@/server_fetch_utils.js";

export default {
  name: "UserManagersCell",
  components: {
    vSelect,
    UserBubble,
    RoleBadge,
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
      localManagers: this.user?.managers ? [...this.user.managers] : [],
      savedManagers: this.user?.managers ? [...this.user.managers] : [],
    };
  },
  computed: {
    potentialManagers() {
      if (!this.allUsers || !Array.isArray(this.allUsers)) {
        return [];
      }
      return this.allUsers.filter(
        (u) =>
          u.immutable_id !== this.user.immutable_id && (u.role === "admin" || u.role === "manager"),
      );
    },
  },
  watch: {
    "user.managers": {
      handler(newVal) {
        if (newVal !== undefined) {
          this.localManagers = [...(newVal || [])];
          this.savedManagers = [...(newVal || [])];
        }
      },
      deep: true,
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
    async handleManagersChange(newManagers) {
      console.log("handleManagersChange called", {
        newManagers,
        savedManagers: this.savedManagers,
      });

      if (!newManagers) newManagers = [];

      const managerIds = newManagers.map((m) => m.immutable_id);
      const savedManagerIds = this.savedManagers.map((m) => m.immutable_id);

      if (JSON.stringify(managerIds.sort()) === JSON.stringify(savedManagerIds.sort())) {
        console.log("No change detected, returning");
        return;
      }

      const confirmed = await DialogService.confirm({
        title: "Update Managers",
        message: `Are you sure you want to update managers for ${this.user.display_name}?`,
        type: "info",
      });

      if (!confirmed) {
        console.log("User cancelled");
        this.localManagers = [...this.savedManagers];
        return;
      }

      try {
        console.log("Calling saveUserManagers", { userId: this.user.immutable_id, managerIds });
        const response = await saveUserManagers(this.user.immutable_id, managerIds);
        console.log("saveUserManagers response", response);

        const userInArray = this.allUsers.find((u) => u.immutable_id === this.user.immutable_id);
        if (userInArray) {
          userInArray.managers = newManagers;
        }
        this.localManagers = newManagers;
        this.savedManagers = [...newManagers];

        DialogService.alert({
          title: "Success",
          message: "Managers updated successfully.",
          type: "info",
        });
      } catch (err) {
        console.error("Error saving managers", err);
        this.localManagers = [...this.savedManagers];
        DialogService.error({
          title: "Error",
          message: "Failed to update user managers.",
        });
      }
    },
  },
};
</script>

<style scoped>
.managers-cell-wrapper {
  position: relative;
  z-index: auto;
}

.managers-cell-wrapper :deep(.vs--open) {
  z-index: 1001;
}

.managers-cell-wrapper :deep(.vs__dropdown-menu) {
  z-index: 1001;
  position: absolute;
}
</style>
