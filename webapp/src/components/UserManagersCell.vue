<template>
  <vSelect
    v-model="localManagers"
    :options="potentialManagers"
    label="display_name"
    multiple
    placeholder="No managers"
    :clearable="false"
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
    };
  },
  computed: {
    potentialManagers() {
      if (!this.allUsers || !Array.isArray(this.allUsers)) {
        return [];
      }
      return this.allUsers.filter((u) => u.immutable_id !== this.user.immutable_id);
    },
  },
  watch: {
    "user.managers": {
      handler(newVal) {
        if (newVal !== undefined) {
          this.localManagers = [...(newVal || [])];
        }
      },
      deep: true,
    },
  },
  methods: {
    async handleManagersChange(newManagers) {
      if (!newManagers) newManagers = [];

      const originalManagers = [...this.localManagers];
      const managerIds = newManagers.map((m) => m.immutable_id);
      const originalManagerIds = originalManagers.map((m) => m.immutable_id);

      if (JSON.stringify(managerIds.sort()) === JSON.stringify(originalManagerIds.sort())) {
        return;
      }

      const confirmed = await DialogService.confirm({
        title: "Update Managers",
        message: `Are you sure you want to update managers for ${this.user.display_name}?`,
        type: "info",
      });

      if (!confirmed) {
        this.localManagers = originalManagers;
        return;
      }

      try {
        await saveUserManagers(this.user.immutable_id, managerIds);

        const userInArray = this.allUsers.find((u) => u.immutable_id === this.user.immutable_id);
        if (userInArray) {
          userInArray.managers = newManagers;
        }
        this.localManagers = newManagers;
      } catch (err) {
        this.localManagers = originalManagers;
        DialogService.error({
          title: "Error",
          message: "Failed to update user managers.",
        });
      }
    },
  },
};
</script>
