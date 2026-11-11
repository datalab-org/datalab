<template>
  <div
    v-if="measuredAt || createdAt"
    class="block-provenance small text-muted d-flex flex-wrap align-items-center"
    data-testid="block-provenance"
  >
    <span v-if="measuredAt" class="d-inline-flex align-items-center" :title="measuredAtTooltip">
      <font-awesome-icon :icon="['fas', 'clock']" fixed-width class="mr-1" />
      Measured {{ formatAbsolute(measuredAt) }}
      <span class="source-label ml-1">({{ measuredAtSourceLabel }})</span>
    </span>

    <span v-if="measuredAt && createdAt" class="mx-2">·</span>

    <span v-if="createdAt" class="d-inline-flex align-items-center">
      <font-awesome-icon v-if="!measuredAt" :icon="['fas', 'clock']" fixed-width class="mr-1" />
      Added
      <Creators
        v-if="creators.length"
        :creators="creators"
        :size="16"
        :show-names="true"
        class="mx-1"
      />
      <span :title="formatAbsolute(createdAt)">{{ formatRelativeDate(createdAt) }}</span>
    </span>
  </div>
</template>

<script>
/**
 * BlockProvenance - shows when a block's measurement was made, and who added the
 * block and when.
 *
 * Fields consumed from the block payload (all optional and read-only here):
 *   - `metadata.measured_at`: the measurement time, read from the data file by the
 *     block (or overridden by the user via the metadata viewer, #2083)
 *   - `created_at`, `creators`: from the block's server-side document; absent for
 *     legacy blocks embedded in their item
 */
import Creators from "@/components/Creators";
import { formatRelativeDate, parseUTCDate } from "@/field_utils.js";

export default {
  components: { Creators },
  props: {
    item_id: { type: String, required: true },
    block_id: { type: String, required: true },
  },
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]?.blocks_obj?.[this.block_id] || {};
    },
    measuredAt() {
      return this.block.metadata?.measured_at;
    },
    createdAt() {
      return this.block.created_at;
    },
    creators() {
      return this.block.creators || [];
    },
    measuredAtField() {
      // Provenance of the value, if the block resolves its metadata with sources (#2083)
      return this.block.metadata_fields?.measured_at;
    },
    measuredAtSourceLabel() {
      if (this.measuredAtField?.source === "user") return "set manually";
      return "from data file";
    },
    measuredAtTooltip() {
      const field = this.measuredAtField;
      if (field?.source === "user" && field.set_by_name) {
        return `Set by ${field.set_by_name}${
          field.set_at ? " " + this.formatAbsolute(field.set_at) : ""
        }`;
      }
      return "";
    },
  },
  methods: {
    formatRelativeDate,
    formatAbsolute(value) {
      return parseUTCDate(value).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    },
  },
};
</script>

<style scoped>
.block-provenance {
  padding: 0.25rem 0 0.25rem 1rem;
  row-gap: 0.25rem;
}

.source-label {
  font-style: italic;
}
</style>
