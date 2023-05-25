<template>
  <label class="mr-2">Collection Members</label>
  <FancyTable
    :headers="headers"
    :items="items"
    :searchValue="searchValue"
    :isReady="isReady"
    :itemsSelected="itemsSelected"
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
      headers: [
        { text: "ID", value: "item_id", sortable: true },
        { text: "type", value: "type", sortable: true },
        { text: "Sample name", value: "name", sortable: true },
        { text: "Formula", value: "chemform", sortable: true },
        { text: "Date", value: "date", sortable: true },
        { text: "Collections", value: "collections", sortable: true },
        { text: "Creators", value: "creators", sortable: true },
        { text: "# of blocks", value: "nblocks", sortable: true },
      ],
    };
  },
  computed: {
    items() {
      return this.$store.state.all_collection_children[this.collection_id];
    },
  },
  methods: {
    getCollectionMembers() {
      getCollection()
        .then((response) => {
          this.$store.commit("setCollectionMembers", {
            collection_id: this.collection_id,
            items: response.data,
          });
        })
        .catch((error) => {
          console.log(error);
          this.isFetchError = true;
        });
    },
  },
  props: {
    collection_id: String,
  },
  components: {
    FancyTable,
  },
  created() {
    this.getCollectionMembers();
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
