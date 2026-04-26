<template>
  <div class="groups-cell-wrapper">
    <div v-if="!isEditing" class="groups-display" @click="startEditing">
      <span v-if="!localGroups.length" class="text-muted small">No groups</span>
      <FormattedGroupName
        v-else-if="localGroups.length === 1"
        :group="localGroups[0]"
        :show-name="true"
        :size="24"
      />
      <GroupsIconCounter v-else :groups="localGroups" :size="24" />
    </div>
    <vSelect
      v-else
      ref="groupSelect"
      v-model="localGroups"
      :options="allGroups"
      label="display_name"
      multiple
      placeholder="No groups"
      :clearable="false"
      :taggable="false"
      @open="onDropdownOpen"
      @close="onDropdownClose"
    >
      <template #option="option">
        <span>{{ option.display_name }}</span>
      </template>
      <template #selected-option="option">
        <span class="small">{{ option.display_name }}</span>
      </template>
    </vSelect>
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";
import vSelect from "vue-select";
import FormattedGroupName from "@/components/FormattedGroupName.vue";
import GroupsIconCounter from "@/components/GroupsIconCounter.vue";
import { addUserToGroup, removeUserFromGroup } from "@/server_fetch_utils.js";

export default {
  name: "UserGroupsCell",
  components: { vSelect, FormattedGroupName, GroupsIconCounter },
  props: {
    user: {
      type: Object,
      required: true,
    },
    allGroups: {
      type: Array,
      required: true,
    },
  },
  data() {
    const matchedGroups = this.matchGroupsToOptions(this.user?.groups || []);
    return {
      isEditing: false,
      localGroups: matchedGroups,
      savedGroups: matchedGroups,
    };
  },
  watch: {
    "user.groups": {
      handler(newVal) {
        const matched = this.matchGroupsToOptions(newVal || []);
        this.localGroups = matched;
        this.savedGroups = matched;
      },
      deep: true,
    },
  },
  methods: {
    matchGroupsToOptions(groups) {
      return groups.map(
        (g) => this.allGroups.find((ag) => String(ag.immutable_id) === String(g.immutable_id)) || g,
      );
    },
    async startEditing() {
      this.isEditing = true;
      await this.$nextTick();
      this.$refs.groupSelect?.$refs.search?.focus();
    },
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
    async onDropdownClose() {
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

      await this.saveIfChanged();
      this.isEditing = false;
    },
    async saveIfChanged() {
      const newIds = this.localGroups.map((g) => String(g.immutable_id)).sort();
      const savedIds = this.savedGroups.map((g) => String(g.immutable_id)).sort();

      if (JSON.stringify(newIds) === JSON.stringify(savedIds)) {
        return;
      }

      const confirmed = await DialogService.confirm({
        title: "Update Groups",
        message: `Are you sure you want to update groups for ${this.user.display_name}?`,
        type: "info",
      });

      if (!confirmed) {
        this.localGroups = [...this.savedGroups];
        return;
      }

      const groupsToAdd = this.localGroups.filter(
        (ng) => !this.savedGroups.find((sg) => String(sg.immutable_id) === String(ng.immutable_id)),
      );
      const groupsToRemove = this.savedGroups.filter(
        (sg) => !this.localGroups.find((ng) => String(ng.immutable_id) === String(sg.immutable_id)),
      );

      try {
        await Promise.all([
          ...groupsToAdd.map((g) => addUserToGroup(String(g.immutable_id), this.user.immutable_id)),
          ...groupsToRemove.map((g) =>
            removeUserFromGroup(String(g.immutable_id), this.user.immutable_id),
          ),
        ]);

        this.localGroups = [...this.localGroups];
        this.savedGroups = [...this.localGroups];

        DialogService.alert({
          title: "Success",
          message: "Groups updated successfully.",
          type: "info",
        });
      } catch {
        this.localGroups = [...this.savedGroups];
        DialogService.error({
          title: "Error",
          message: "Failed to update user groups.",
        });
      }
    },
  },
};
</script>

<style scoped>
.groups-cell-wrapper {
  position: relative;
  z-index: auto;
}

.groups-display {
  cursor: pointer;
  min-height: 1.5rem;
  display: inline-flex;
  align-items: center;
}

.groups-cell-wrapper :deep(.vs--open) {
  z-index: 1001;
}

.groups-cell-wrapper :deep(.vs__dropdown-menu) {
  z-index: 1001;
  position: absolute;
}
</style>
