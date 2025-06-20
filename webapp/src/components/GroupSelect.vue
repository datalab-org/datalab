<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="filteredGroups"
    multiple
    :min="minimumOptions"
    label="display_name"
    :reduce="(group) => group"
    :filterable="false"
    @search="debouncedAsyncSearch"
  >
    <template #no-options="{ searching }">
      <span v-if="searching"> Sorry, no matches found. </span>
      <span v-else class="empty-search"> Search for a group by name or ID </span>
    </template>
    <template #option="group">
      <div class="d-flex align-items-center">
        <strong>{{ group.display_name }}</strong>
        <small class="text-muted ml-2">({{ group.group_id }})</small>
      </div>
    </template>
    <template #selected-option="group">
      <div class="d-flex align-items-center">
        <strong>{{ group.display_name }}</strong>
        <small class="text-muted ml-2">({{ group.group_id }})</small>
      </div>
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import { getGroupsList } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";

export default {
  components: {
    vSelect,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
    minimumOptions: {
      type: Number,
      default: 0,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      debounceTimeout: null,
      groups: [],
      isSearchFetchError: false,
    };
  },
  computed: {
    value: {
      get() {
        return this.modelValue;
      },
      set(newValue) {
        this.$emit("update:modelValue", newValue);
      },
    },
    filteredGroups() {
      const selectedGroupIds = this.modelValue.map((group) => group.immutable_id);
      return this.groups.filter((group) => !selectedGroupIds.includes(group.immutable_id));
    },
  },
  async created() {
    await this.loadGroups();
  },
  methods: {
    async loadGroups() {
      try {
        this.groups = await getGroupsList();
      } catch (error) {
        console.error("Error loading groups:", error);
        this.groups = [];
      }
    },
    async debouncedAsyncSearch(query, loading) {
      loading(true);
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(async () => {
        if (query && query.length > 0) {
          const allGroups = await getGroupsList();
          this.groups = allGroups.filter(
            (group) =>
              group.display_name.toLowerCase().includes(query.toLowerCase()) ||
              group.group_id.toLowerCase().includes(query.toLowerCase()),
          );
        } else {
          await this.loadGroups();
        }
        loading(false);
      }, debounceTime);
    },
  },
};
</script>
