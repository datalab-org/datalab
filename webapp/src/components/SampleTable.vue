<template>
  <DynamicDataTable
    :columns="sampleColumns"
    :data="samples"
    :data-type="'samples'"
    :global-filter-fields="[
      'item_id',
      'type',
      'name',
      'chemform',
      'collectionsList',
      'creatorsList',
      'nblocks',
    ]"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getSampleList } from "@/server_fetch_utils.js";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      sampleColumns: [
        {
          field: "item_id",
          header: "ID",
          body: "FormattedItemName",
          filter: true,
        },
        { field: "type", header: "Type", filter: true },
        { field: "name", header: "Sample name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula" },
        { field: "date", header: "Date" },
        { field: "collections", header: "Collections", body: "CollectionList", filter: true },
        { field: "creators", header: "Creators", body: "Creators", filter: true },
        { field: "nblocks", header: "", body: "BlocksIconCounter", icon: ["fa", "cubes"] },
        { field: "nfiles", header: "", body: "FilesIconCounter", icon: ["fa", "file"] },
      ],
    };
  },
  computed: {
    samples() {
      return this.$store.state.sample_list.map((sample) => ({
        ...sample,
        collectionsList: sample.collections.join(", "),
        creatorsList: sample.creators.map((creator) => creator.display_name).join(", "),
      }));
    },
  },
  mounted() {
    this.getSamples();
  },
  methods: {
    getSamples() {
      getSampleList();
    },
  },
};
</script>
