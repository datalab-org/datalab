<template>
  <!-- See https://github.com/sagalbot/vue-select/issues/1399 for why filterBy is included-->
  <vSelect
    v-model="value"
    :options="items"
    @search="debouncedAsyncSearch"
    label="name"
    :filterable="false"
    ref="selectComponent"
    :createOption="createOption"
    :filterBy="() => true"
  >
    <template #no-options="{ searching }">
      <span v-if="searching"> Sorry, no matches found. </span>
      <span v-else class="empty-search"> Type a search term... </span>
    </template>
    <template v-slot:option="{ type, item_id, name, chemform }">
      <FormattedItemName
        :item_id="item_id"
        :itemType="type"
        :name="name"
        :chemform="chemform"
        enableModifiedClick
        :maxLength="formattedItemNameMaxLength"
      />
    </template>
    <template v-slot:selected-option="{ type, item_id, name }">
      <FormattedItemName
        :item_id="item_id"
        :itemType="type"
        :name="name"
        enableModifiedClick
        :maxLength="formattedItemNameMaxLength"
      />
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import FormattedItemName from "@/components/FormattedItemName.vue";
import { searchItems } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";

export default {
  props: {
    modelValue: {},
    formattedItemNameMaxLength: {
      type: Number,
      default: NaN,
    },
    typesToQuery: {
      type: Array,
      default: () => ["samples", "starting_materials", "cells"],
    },
  },
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
    async debouncedAsyncSearch(query, loading) {
      // if (query == "") {
      //   return;
      // }
      loading(true);
      clearTimeout(this.debounceTimeout); // reset the timer
      // start the timer
      this.debounceTimeout = setTimeout(async () => {
        await searchItems(query, 100, this.typesToQuery)
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
    createOption(newOption) {
      return {
        chemform: "",
        item_id: "",
        name: newOption,
        type: "none",
      };
    },
  },
  components: {
    vSelect,
    FormattedItemName,
  },
};
</script>
