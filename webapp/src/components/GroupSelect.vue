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
        <FormattedGroupName :group="group" />
      </div>
    </template>
    <template #selected-option="group">
      <div class="d-flex align-items-center">
        <FormattedGroupName :group="group" />
      </div>
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import { searchGroups } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";
import FormattedGroupName from "@/components/FormattedGroupName.vue";

export default {
  components: {
    vSelect,
    FormattedGroupName,
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
  methods: {
    async debouncedAsyncSearch(query, loading) {
      loading(true);
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(async () => {
        await searchGroups(query, 100)
          .then((groups) => {
            // check if the searched groups are already listed in the value
            // if so, remove it from the list of options
            if (this.value) {
              const valueIds = this.value.map((item) => item.group_id);
              groups = groups.filter((item) => !valueIds.includes(item.group_id));
            }
            this.groups = groups;
          })
          .catch(() => {
            this.isSearchFetchError = true;
          });
        loading(false);
      }, debounceTime);
    },
  },
};
</script>
