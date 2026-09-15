<template>
  <!-- The table sets up its columns (and their filters) once, when created, so wait for the
       server info that decides whether the tags column is shown. -->
  <DynamicDataTable
    v-if="serverInfoLoaded"
    :columns="sampleColumns"
    :data="samples"
    :data-type="'samples'"
    :global-filter-fields="sampleGlobalFilterFields"
  />
</template>

<script>
import DynamicDataTable from "@/components/DynamicDataTable";
import { getInfo, getSampleList, getTags } from "@/server_fetch_utils.js";

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
  TAGS_COLUMN,
  BLOCKS_COLUMN,
  FILES_COLUMN,
  LAST_MODIFIED_COLUMN,
} from "@/utils/tableColumns";

export default {
  components: { DynamicDataTable },
  data() {
    return {
      baseSampleColumns: [
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
    serverInfoLoaded() {
      return this.$store.state.serverInfo !== null;
    },
    enableTags() {
      // Tag column only if enabled globally.
      return this.$store.state.serverInfo?.features?.tags ?? false;
    },
    sampleColumns() {
      const columns = [...this.baseSampleColumns];
      if (this.enableTags) {
        const insertBeforeBlocks = columns.findIndex((column) => column.field === "blocks");
        columns.splice(insertBeforeBlocks, 0, TAGS_COLUMN);
      }
      return columns;
    },
    sampleGlobalFilterFields() {
      const fields = [
        "item_id",
        "name",
        "refcode",
        "chemform",
        "creatorsList",
        "blocks",
        "characteristic_chemical_formula",
      ];
      if (this.enableTags) {
        fields.push("tagsList");
      }
      return fields;
    },
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
          tagsList: (sample.tags || [])
            .map((tag) => tag.name)
            .filter(Boolean)
            .join(", "),
        };
      });
    },
  },
  watch: {
    enableTags: {
      // The tags filter offers the whole global tag list, so fetch it once tags are enabled.
      immediate: true,
      handler(enabled) {
        if (enabled && this.$store.state.tag_list === null) {
          getTags();
        }
      },
    },
  },
  created() {
    if (!this.serverInfoLoaded) {
      getInfo();
    }
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
