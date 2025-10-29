<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <div id="collection-information">
          <div class="form-row">
            <div class="form-group col">
              <label for="name" class="mr">Title</label>
              <input
                id="name"
                v-model="Title"
                placeholder="Add a title"
                class="form-control"
                style="border: none"
              />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group col">
              <label id="creators" class="mr-2">Creators</label>
              <div>
                <Creators :creators="CollectionCreators" aria-labelledby="creators" />
              </div>
            </div>
          </div>
        </div>

        <label id="description-label" class="mr-2">Description</label>
        <TiptapInline
          v-model="CollectionDescription"
          aria-labelledby="description-label"
        ></TiptapInline>
        <div class="form-row">
          <div class="form-group col">
            <ExportButton :collection-id="collection_id" />
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <CollectionRelationshipVisualization :collection_id="collection_id" />
      </div>
    </div>
    <DynamicDataTable
      :data="children"
      :columns="collectionTableColumns"
      :data-type="'collectionItems'"
      :global-filter-fields="[
        'item_id',
        'status',
        'name',
        'refcode',
        'blocks',
        'chemform',
        'characteristic_chemical_formula',
      ]"
      :show-buttons="true"
      :collection-id="collection_id"
      @remove-selected-items-from-collection="handleItemsRemovedFromCollection"
    />
  </div>
</template>

<script>
import { createComputedSetterForCollectionField } from "@/field_utils.js";
import { getCollectionSampleList } from "@/server_fetch_utils";
import TiptapInline from "@/components/TiptapInline";
import Creators from "@/components/Creators";
import CollectionRelationshipVisualization from "@/components/CollectionRelationshipVisualization";
import DynamicDataTable from "@/components/DynamicDataTable";
import FormattedItemStatus from "@/components/FormattedItemStatus.vue";
import ExportButton from "@/components/ExportButton";

export default {
  components: {
    TiptapInline,
    Creators,
    CollectionRelationshipVisualization,
    DynamicDataTable,
    FormattedItemStatus,
    ExportButton,
  },
  props: {
    collection_id: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      collectionTableColumns: [
        {
          field: "item_id",
          header: "ID",
          body: "FormattedItemName",
          filter: true,
          label: "ID",
        },
        { field: "type", header: "Type", filter: true, label: "Type" },
        { field: "status", header: "Status", body: "FormattedItemStatus", filter: true },
        { field: "name", header: "Sample name", label: "Sample Name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula", label: "Formula" },
        { field: "date", header: "Date", label: "Date", filter: true },
        {
          field: "creators",
          header: "Creators",
          body: "Creators",
          label: "Creators",
          filter: true,
        },
        {
          field: "blocks",
          header: "",
          body: "BlocksIconCounter",
          icon: ["fa", "cubes"],
          label: "Blocks",
          filter: true,
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
    CollectionID: createComputedSetterForCollectionField("collection_id"),
    CollectionDescription: createComputedSetterForCollectionField("description"),
    Title: createComputedSetterForCollectionField("title"),
    Name: createComputedSetterForCollectionField("name"),
    CollectionCreators: createComputedSetterForCollectionField("creators"),
    children() {
      return this.$store.state.all_collection_children[this.collection_id] || [];
    },
  },
  created() {
    this.getCollectionChildren();
  },
  methods: {
    getCollectionChildren() {
      getCollectionSampleList(this.collection_id)
        .then(() => {
          this.tableIsReady = true;
        })
        .catch(() => {
          this.fetchError = true;
        });
    },
    handleItemsRemovedFromCollection() {
      this.getCollectionChildren();
    },
  },
};
</script>
