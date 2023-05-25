<template>
  <label class="mr-2">Collection Members</label>
  <FancyTable
    :items="items"
    :searchValue="searchValue"
    :isReady="isReady"
    :itemsSelected="itemsSelected"
    :tableType="tableType"
  />
</template>

<script>
import FancyTable from "@/components/FancyTable";

export default {
  data() {
    return {
      isFetchError: false,
      itemsSelected: [],
      isReady: true,
      searchValue: "",
      tableType: "items",
    };
  },
  computed: {
    items() {
      return this.$store.state.all_collection_children[this.collection_id];
    },
  },
  props: {
    collection_id: String,
  },
  components: {
    FancyTable,
  },
};
</script>

<style scoped>
.nav-link {
  cursor: pointer;
}

.contents-item {
  cursor: pointer;
}

.contents-blocktype {
  font-style: italic;
  color: gray;
  margin-right: 1rem;
}

.contents-blocktitle {
  color: #004175;
}

#contents-ol {
  margin-bottom: 0rem;
  padding-left: 1rem;
}
</style>
