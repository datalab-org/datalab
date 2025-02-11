<template>
  <Navbar />

  <div class="container mt-4">
    <div class="row">
      <div class="col-md-6">
        <h3>Current Search</h3>
        <ItemSelect
          v-model="searchValue"
          :ngram="false"
          placeholder="Search with current implementation..."
        />
      </div>

      <div class="col-md-6">
        <h3>Ngram Search</h3>
        <ItemSelect
          v-model="searchValue"
          :ngram="true"
          placeholder="Search with ngram implementation..."
        />
      </div>
    </div>
  </div>
</template>

<script>
import Navbar from "@/components/Navbar";
import ItemSelect from "@/components/ItemSelect.vue";

export default {
  components: {
    Navbar,
    ItemSelect,
  },
  data() {
    return {
      searchValue: "",
    };
  },
};
</script>

<style scoped></style>
