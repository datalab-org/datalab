<template>
  <vSelect
    ref="selectComponent"
    v-model="value"
    :options="collectionOrNewCollection"
    multiple
    label="collection_id"
    :filterable="false"
    @search="debouncedAsyncSearch"
  >
    <template #no-options="{ searching }">
      <span v-if="validationMessage" class="form-error">{{ validationMessage }}</span>
      <span v-else-if="searching"> Collection already selected </span>
      <span v-else class="empty-search"> Search for a collection... </span>
    </template>
    <template #option="{ collection_id, title }">
      <FormattedCollectionName
        v-if="collection_id"
        :collection_id="collection_id"
        :title="title"
        enable-modified-click
        :max-length="formattedItemNameMaxLength"
      />
      <div v-else @click="handleCreateNewCollection">
        {{ title }}
      </div>
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
import { searchCollections, createNewCollection } from "@/server_fetch_utils.js";
import { debounceTime } from "@/resources.js";

export default {
  components: {
    vSelect,
    FormattedCollectionName,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
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
      searchQuery: "",
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
    collectionOrNewCollection() {
      const valueSafe = Array.isArray(this.value) ? this.value : [];

      if (
        this.searchQuery &&
        !this.collections.some((item) => item.collection_id === this.searchQuery) &&
        !valueSafe.some((item) => item.collection_id === this.searchQuery) &&
        !this.IDValidationMessage()
      ) {
        return [
          ...this.collections,
          {
            collection_id: null,
            title: `Create new collection: "${this.searchQuery}"`,
          },
        ];
      }
      return this.collections;
    },
    validationMessage() {
      return this.IDValidationMessage();
    },
  },
  methods: {
    async debouncedAsyncSearch(query, loading) {
      // if (query == "") {
      //   return;
      // }
      this.searchQuery = query;
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
    IDValidationMessage() {
      if (this.searchQuery && !/^[a-zA-Z0-9_-]+$/.test(this.searchQuery)) {
        return "ID can only contain alphanumeric characters, dashes ('-'), and underscores ('_').";
      }
      if (/^[._-]/.test(this.searchQuery) | /[._-]$/.test(this.searchQuery)) {
        return "ID cannot start or end with punctuation";
      }
      if ((this.searchQuery && this.searchQuery.length < 1) || this.searchQuery.length > 40) {
        return "ID must be between 1 and 40 characters.";
      }
      return "";
    },
    async handleCreateNewCollection() {
      if (this.IDValidationMessage()) {
        return;
      } else {
        try {
          let collection_id = this.searchQuery;
          const newCollection = await createNewCollection(this.searchQuery);
          if (newCollection) {
            this.value = [
              ...this.value.filter((item) => item.collection_id !== null),
              {
                collection_id: collection_id,
              },
            ];
          }
        } catch (error) {
          console.error("Error:", error);
          alert(
            "An error occurred while creating the collection. Please check that your desired collection ID is valid.",
          );
        }
      }
    },
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}
</style>
