<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="filteredUsers"
    multiple
    :min="minimumOptions"
    label="immutable_id"
    :filterable="false"
    @search="debouncedAsyncSearch"
  >
    <template #no-options="{ searching }">
      <span v-if="searching"> Sorry, no matches found. </span>
      <span v-else class="empty-search"> Search for a user by name, email, ORCID or GitHub </span>
    </template>
    <template #option="user">
      <Creators :show-bubble="true" :creators="[user]" />
    </template>
    <template #selected-option="user">
      <Creators :show-bubble="true" :creators="[user]" />
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import { searchUsers } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";
import Creators from "@/components/Creators.vue";

export default {
  components: {
    vSelect,
    Creators,
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
      users: [],
      isSearchFetchError: false,
    };
  },
  computed: {
    // computed setter to pass v-model through  component:
    value: {
      get() {
        return this.modelValue;
      },
      set(newValue) {
        this.$emit("update:modelValue", newValue);
      },
    },
    filteredUsers() {
      const selectedUserIds = this.modelValue.map((user) => user.immutable_id);
      return this.users.filter((user) => !selectedUserIds.includes(user.immutable_id));
    },
  },
  methods: {
    async debouncedAsyncSearch(query, loading) {
      loading(true);
      clearTimeout(this.debounceTimeout); // reset the timer
      // start the timer
      this.debounceTimeout = setTimeout(async () => {
        await searchUsers(query, 100)
          .then((users) => {
            this.users = users;
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
