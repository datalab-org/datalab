<template>
  <vSelect
    v-model="value"
    :options="items"
    @search="debouncedAsyncSearch"
    label="name"
    :filterable="false"
  >
    <template #no-options="{ searching }">
      <span v-if="searching"> Sorry, no matches found. </span>
      <span v-else class="empty-search"> Type a search term... </span>
    </template>
    <template v-slot:option="{ type, item_id, name, chemform }">
      <span class="badge badge-light mr-2" :style="{ backgroundColor: getBadgeColor(type) }">
        {{ item_id }}
      </span>
      {{ name }}
      <template v-if="chemform && chemform != ' '">
        [ <ChemicalFormula :formula="chemform" /> ]
      </template>
    </template>
    <template v-slot:selected-option="{ type, item_id, name }">
      <span class="badge badge-light mr-2" :style="{ backgroundColor: getBadgeColor(type) }">{{
        item_id
      }}</span>
      {{ name }}
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import ChemicalFormula from "@/components/ChemicalFormula.vue";

import { searchItems } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";

export default {
  props: ["modelValue"],
  emits: ["update:modelValue"],
  data() {
    return {
      debounceTimeout: null,
      items: [],
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
  },
  methods: {
    getBadgeColor(itemType) {
      return itemTypes[itemType]?.lightColor || "LightGrey";
    },
    getBadgeName(itemType) {
      return (itemTypes[itemType]?.navbarName || "").toLowerCase();
    },
    async debouncedAsyncSearch(query, loading) {
      if (query == "") {
        return;
      }
      loading(true);
      const debounceTime = 250; // time after user stops typing before request is sent
      clearTimeout(this.debounceTimeout); // reset the timer
      // start the timer
      this.debounceTimeout = setTimeout(async () => {
        await searchItems(query, 100, ["samples", "starting_materials"])
          .then((items) => {
            this.items = items;
          })
          .catch((error) => {
            console.error("Fetch error");
            console.error(error);
            this.isSearchFetchError = true;
          });
        loading(false);
      }, debounceTime);
    },
  },
  components: {
    vSelect,
    ChemicalFormula,
  },
};
</script>
