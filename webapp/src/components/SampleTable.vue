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
import { getSampleList, getSchema } from "@/server_fetch_utils.js";

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
        { field: "collections", header: "Collections", body: "CollectionList" },
        { field: "creators", header: "Creators", body: "Creators" },
        { field: "nblocks", header: "# of blocks" },
      ],
      sampleSchema: null,
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
  async mounted() {
    this.getSamples();
    await this.getSampleSchema();
  },
  methods: {
    getSamples() {
      getSampleList();
    },
    async getSampleSchema() {
      try {
        this.sampleSchema = await getSchema("sample");
        console.log("#%#%#%#%#%#%#%");
        console.log("Sample Schema:", this.sampleSchema);
        console.log("#%#%#%#%#%#%#%");
      } catch (error) {
        console.error("Failed to fetch sample schema:", error);
      }
    },
  },
};
</script>
