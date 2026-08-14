<template>
  <div class="container-lg">
    <!-- Sample information -->
    <div class="row">
      <div class="col">
        <div id="sample-information" class="form-row">
          <div class="form-group col-sm-6 pr-2">
            <label for="samp-name">Name</label>
            <input id="samp-name" v-model="Name" class="form-control" />
          </div>
          <div class="form-group col-sm-6">
            <label for="samp-date">Date Created</label>
            <input
              id="samp-date"
              v-model="DateCreated"
              type="datetime-local"
              class="form-control"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-3 col-sm-3 col-3">
            <label for="samp-refcode">Refcode</label>
            <div id="samp-refcode">
              <FormattedRefcode :refcode="Refcode" />
            </div>
          </div>
          <div class="form-group col-md-3 col-sm-3 col-3 pb-3">
            <ToggleableItemStatusFormGroup
              v-model="Status"
              :possible-item-statuses="possibleItemStatuses"
            />
          </div>
          <div class="form-group col-md-6 col-sm-6 col-6 pr-2">
            <ToggleableCollectionFormGroup v-model="Collections" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group col-6 col-md-6 pb-3">
            <ToggleableCreatorsFormGroup v-model="ItemCreators" :refcode="Refcode" />
          </div>
          <div class="form-group col-6 col-md-6 pb-3">
            <ToggleableGroupsFormGroup v-model="ItemGroups" :refcode="Refcode" />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <ItemRelationshipVisualization :item_id="item_id" />
      </div>
    </div>
    <div class="row">
      <div class="col">
        <SubstanceInformation class="mt-3" :item_id="item_id" />
      </div>
    </div>
    <div class="row">
      <div class="col">
        <label id="samp-description-label">Description</label>
        <TiptapInline v-model="SampleDescription" aria-labelledby="samp-description-label" />
      </div>
    </div>

    <TableOfContents :item_id="item_id" :information-sections="tableOfContentsSections" />
    <SynthesisInformation class="mt-3" :item_id="item_id" />

    <div id="sample-stages" class="mt-3">
      <SampleStagesTimeline :stages="sampleStages" @stage-click="scrollToBlock" />
    </div>
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import FormattedRefcode from "@/components/FormattedRefcode";
import ToggleableCollectionFormGroup from "@/components/ToggleableCollectionFormGroup";
import ToggleableCreatorsFormGroup from "@/components/ToggleableCreatorsFormGroup";
import ToggleableItemStatusFormGroup from "@/components/ToggleableItemStatusFormGroup";
import TiptapInline from "@/components/TiptapInline";
import ToggleableGroupsFormGroup from "@/components/ToggleableGroupsFormGroup";
import SynthesisInformation from "@/components/SynthesisInformation";
import SubstanceInformation from "@/components/SubstanceInformation";
import TableOfContents from "@/components/TableOfContents";
import ItemRelationshipVisualization from "@/components/ItemRelationshipVisualization";
import SampleStagesTimeline from "@/components/SampleStagesTimeline";

export default {
  components: {
    TiptapInline,
    SynthesisInformation,
    SubstanceInformation,
    TableOfContents,
    ItemRelationshipVisualization,
    SampleStagesTimeline,
    FormattedRefcode,
    ToggleableCollectionFormGroup,
    ToggleableCreatorsFormGroup,
    ToggleableItemStatusFormGroup,
    ToggleableGroupsFormGroup,
  },
  props: {
    item_id: { type: String, required: true },
    refcode: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      tableOfContentsSections: [
        { title: "Table of Contents", targetID: "table-of-contents" },
        { title: "Sample Information", targetID: "sample-information" },
        { title: "Substance Information", targetID: "substance-information" },
        { title: "Synthesis Information", targetID: "synthesis-information" },
        { title: "Sample Stages", targetID: "sample-stages" },
      ],
    };
  },
  computed: {
    item() {
      return this.$store.state.all_item_data[this.item_id];
    },
    Refcode: createComputedSetterForItemField("refcode"),
    ItemID: createComputedSetterForItemField("item_id"),
    SampleDescription: createComputedSetterForItemField("description"),
    Name: createComputedSetterForItemField("name"),
    DateCreated: createComputedSetterForItemField("date"),
    ItemCreators: createComputedSetterForItemField("creators"),
    ItemGroups: createComputedSetterForItemField("groups"),
    Collections: createComputedSetterForItemField("collections"),
    Status: createComputedSetterForItemField("status"),
    schema() {
      return this.$store.state.schemas[this.item?.type];
    },
    possibleItemStatuses() {
      return this.schema?.attributes?.schema?.definitions?.ItemStatus?.enum;
    },
    sampleStages() {
      const item = this.item || {};
      const blocks = item.blocks_obj || {};
      const displayOrder = item.display_order || Object.keys(blocks);
      const baseTimestamp = item.date ? new Date(item.date).getTime() : Date.now();

      return displayOrder
        .map((blockId, index) => {
          const block = blocks[blockId];

          if (!block) {
            return null;
          }

          const blocktype = block.blocktype || "Block";
          const title = block.title || blocktype;
          const rawTimestamp =
            block.created_at || block.createdAt || block.date_created || block.timestamp;
          const timestamp = rawTimestamp
            ? rawTimestamp
            : new Date(baseTimestamp + index * 10 * 60 * 1000).toISOString();
          const previousBlockId = displayOrder[index - 1];
          const previousBlock = previousBlockId ? blocks[previousBlockId] : null;
          const transitionLabel = previousBlock
            ? `from ${previousBlock.blocktype || "Block"} to ${blocktype}`
            : "initial stage";

          return {
            id: blockId,
            block_id: blockId,
            blocktype,
            full_name: title,
            title,
            name: title,
            timestamp,
            detail: block.freeform_comment || "",
            metadata: block.metadata || null,
            transition_label: transitionLabel,
          };
        })
        .filter(Boolean);
    },
  },
  methods: {
    scrollToBlock(stage) {
      const blockId = stage?.block_id || stage?.id;
      if (!blockId || typeof document === "undefined") {
        return;
      }

      const target = document.getElementById(blockId);
      if (!target) {
        return;
      }

      const headerOffset = 88;
      const top = target.getBoundingClientRect().top + window.scrollY - headerOffset;
      window.scrollTo({ top, behavior: "smooth" });
    },
  },
};
</script>
