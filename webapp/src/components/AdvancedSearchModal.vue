<template>
  <div v-if="modelValue" class="modal fade show" tabindex="-1" role="dialog" style="display: block">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Advanced Search</h5>
          <button type="button" class="close" aria-label="Close" @click="closeModal">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="search-query">Search Query</label>
            <input
              id="search-query"
              v-model="searchQuery"
              type="text"
              class="form-control"
              placeholder="Enter your search terms..."
              @keyup.enter="performSearch"
            />
            <small class="form-text text-muted">
              Enter keywords to search across all fields. Results will be fetched from the API.
            </small>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeModal">Cancel</button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="!searchQuery || searchQuery.trim() === ''"
            @click="performSearch"
          >
            <font-awesome-icon icon="search" class="mr-1" />
            Search
          </button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="modelValue" class="modal-backdrop fade show"></div>
</template>

<script>
export default {
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["update:modelValue", "search"],
  data() {
    return {
      searchQuery: "",
    };
  },
  methods: {
    closeModal() {
      this.searchQuery = "";
      this.$emit("update:modelValue", false);
    },
    performSearch() {
      if (this.searchQuery && this.searchQuery.trim() !== "") {
        this.$emit("search", this.searchQuery.trim());
        this.closeModal();
      }
    },
  },
};
</script>
