<template>
  <div>
    <select
      v-if="scopeOptions.length > 1"
      id="tag-scope"
      v-model="scope"
      data-testid="tag-scope-select"
      class="form-control"
    >
      <option v-for="option in scopeOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <!-- With a single available scope there is nothing to choose: show it read-only. -->
    <input
      v-else
      id="tag-scope"
      :value="scopeOptions[0]?.shortLabel ?? ''"
      type="text"
      class="form-control"
      disabled
    />
    <select
      v-if="scope === 'group'"
      id="tag-group"
      v-model="owner"
      data-testid="tag-group-select"
      class="form-control mt-2"
      aria-label="Group"
      required
    >
      <option disabled :value="null">Select a group...</option>
      <option v-for="group in groups" :key="group.immutable_id" :value="group.immutable_id">
        {{ group.display_name }}
      </option>
    </select>
  </div>
</template>

<script>
import { getManageableTagGroups } from "@/server_fetch_utils.js";

// Chooses the scope of a tag, and its group for group-scoped tags.
//
// For a new tag, the available scopes depend on the current user: everyone can create
// user-defined tags, administrators can create global tags, and administrators and group
// managers can create group tags for the groups returned by `GET /tags/manageable-groups`.
//
// For an existing tag (`currentTag`, used by administrators to change a tag's scope), the
// user-defined scope is only offered when it is the tag's current scope, since tags cannot
// be moved to it.
export default {
  name: "TagScopeSelect",
  props: {
    // `{ scope, owner }`: `owner` is the group's immutable_id for group tags, otherwise null.
    modelValue: {
      type: Object,
      default: () => ({ scope: "user", owner: null }),
    },
    // The tag being edited (a row from GET /tags), or null for a new tag.
    currentTag: {
      type: Object,
      default: null,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      groups: [],
    };
  },
  computed: {
    isAdmin() {
      return this.$store.state.currentUserRole === "admin";
    },
    scopeOptions() {
      const options = [];
      if (!this.currentTag) {
        options.push({
          value: "user",
          label: "User-defined (only you can use it)",
          shortLabel: "User-defined",
        });
      } else if (this.currentTag.scope === "user") {
        const owner = this.currentTag.owner_name || "its owner";
        options.push({
          value: "user",
          label: `User-defined: ${owner} (current)`,
          shortLabel: `User-defined: ${owner}`,
        });
      }
      if (this.groups.length > 0) {
        options.push({
          value: "group",
          label: "Group (members of the group can use it)",
          shortLabel: "Group",
        });
      }
      if (this.isAdmin) {
        options.push({
          value: "global",
          label: "Global (available to everyone)",
          shortLabel: "Global",
        });
      }
      return options;
    },
    scope: {
      get() {
        return this.modelValue.scope;
      },
      set(scope) {
        let owner = null;
        if (this.currentTag && scope === this.currentTag.scope) {
          // Back to the tag's current scope: restore its current owner.
          owner = this.currentTag.owner ?? null;
        } else if (scope === "group" && this.groups.length === 1) {
          // Preselect the group when there is only one to choose from.
          owner = this.groups[0].immutable_id;
        }
        this.$emit("update:modelValue", { scope, owner });
      },
    },
    owner: {
      get() {
        return this.modelValue.owner;
      },
      set(owner) {
        this.$emit("update:modelValue", { scope: this.modelValue.scope, owner });
      },
    },
  },
  created() {
    this.loadGroups();
  },
  methods: {
    async loadGroups() {
      try {
        this.groups = (await getManageableTagGroups()) || [];
      } catch (error) {
        // Without the list, group tags are simply not offered.
        console.error("Error fetching the groups available for group tags:", error);
        this.groups = [];
      }
    },
  },
};
</script>
