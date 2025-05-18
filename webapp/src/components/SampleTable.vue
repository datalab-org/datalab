<template>
  <DynamicDataTable
    :columns="sampleColumns"
    :data="samples"
    :data-type="'samples'"
    :global-filter-fields="[
      'item_id',
      'name',
      'refcode',
      'chemform',
      'blocks',
      'characteristic_chemical_formula',
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
          label: "ID",
        },
        { field: "type", header: "Type", filter: true, label: "Type" },
        { field: "name", header: "Sample name", label: "Sample name" },
        {
          field: "chemform",
          header: "Formula",
          body: "ChemicalFormula",
          label: "Formula",
        },
        { field: "date", header: "Date", label: "Date" },
        {
          field: "collections",
          header: "Collections",
          body: "CollectionList",
          filter: true,
          label: "Collections",
        },
        {
          field: "creators",
          header: "Creators",
          body: "Creators",
          filter: true,
          label: "Creators",
        },
        {
          field: "blocks",
          header: "",
          body: "BlocksIconCounter",
          icon: ["fa", "cubes"],
          filter: true,
          label: "Blocks",
        },
        {
          field: "nfiles",
          header: "",
          body: "FilesIconCounter",
          icon: ["fa", "file"],
          label: "Files",
        },
      ],
    };
  },
  computed: {
    samples() {
      if (!this.$store.state.sample_list) {
        return null;
      }
      return this.$store.state.sample_list.map((sample) => {
        return {
          ...sample,
          collectionsList: sample.collections
            .map((collection) => collection.collection_id)
            .join(", "),
          creatorsList: sample.creators.map((creator) => creator.display_name).join(", "),
        };
      });
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
