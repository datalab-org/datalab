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
      'creatorsList',
      'blocks',
      'characteristic_chemical_formula',
    ]"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getSampleList } from "@/server_fetch_utils.js";

import {
  ITEM_ID_COLUMN,
  TYPE_COLUMN,
  STATUS_COLUMN,
  NAME_COLUMN,
  CHEMFORM_COLUMN,
  DATE_COLUMN,
  DATE_RANGE_FILTER,
  COLLECTIONS_COLUMN,
  CREATORS_AND_GROUPS_COLUMN,
  BLOCKS_COLUMN,
  FILES_COLUMN,
  LAST_MODIFIED_COLUMN,
} from "@/utils/tableColumns";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      sampleColumns: [
        {
          ...ITEM_ID_COLUMN,
          body: {
            ...ITEM_ID_COLUMN.body,
            props: (row) => ({
              ...ITEM_ID_COLUMN.body.props(row),
              itemType: row.type !== undefined ? row.type : "samples",
            }),
          },
        },
        TYPE_COLUMN,
        STATUS_COLUMN,
        { ...NAME_COLUMN, label: "Sample name" },
        CHEMFORM_COLUMN,
        { ...DATE_COLUMN, filter: DATE_RANGE_FILTER },
        COLLECTIONS_COLUMN,
        CREATORS_AND_GROUPS_COLUMN,
        BLOCKS_COLUMN,
        FILES_COLUMN,
        LAST_MODIFIED_COLUMN,
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
          creatorsAndGroups: [
            ...(sample.creators || []).map((c) => ({ ...c, type: "creator" })),
            ...(sample.groups || []).map((g) => ({ ...g, type: "group" })),
          ],
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
