<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="collections"
    multiple
    label="collection_id"
    :filterable="false"
    @search="debouncedAsyncSearch"
  >
    <template #no-options="{ searching }">
      <span v-if="searching"> Sorry, no matches found. </span>
      <span v-else class="empty-search"> Search for a collection... </span>
    </template>
    <template #option="{ collection_id, title }">
      <FormattedCollectionName
        :collection_id="collection_id"
        :title="title"
        enable-modified-click
        :max-length="formattedItemNameMaxLength"
      />
    </template>
    <template #selected-option="{ collection_id }">
      <FormattedCollectionName
        :collection_id="collection_id"
        enable-modified-click
        :max-length="formattedItemNameMaxLength"
      />
    </template>
  </vSelect>
</template>

<script>
import vSelect from "vue-select";
import FormattedCollectionName from "@/components/FormattedCollectionName.vue";
import { searchCollections } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";

export default {
  components: {
    vSelect,
    FormattedCollectionName,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    formattedItemNameMaxLength: {
      type: Number,
      default: NaN,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      debounceTimeout: null,
      collections: [],
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
        await searchCollections(query, 100)
          .then((collections) => {
            // check if the searched collections are already listed in the value
            // if so, remove it from the list of options
            if (this.value) {
              const valueIds = this.value.map((item) => item.collection_id);
              collections = collections.filter((item) => !valueIds.includes(item.collection_id));
            }
            this.collections = collections;
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
};
</script>
