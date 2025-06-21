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
        <TinyMceInline
          v-model="CollectionDescription"
          aria-labelledby="description-label"
        ></TinyMceInline>
      </div>
      <div class="col-md-4">
        <CollectionRelationshipVisualization :collection_id="collection_id" />
      </div>
    </div>
    <DynamicDataTable
      :data="children"
      :columns="collectionTableColumns"
      :data-type="'samples'"
      :global-filter-fields="[
        'item_id',
        'name',
        'refcode',
        'chemform',
        'blocks',
        'characteristic_chemical_formula',
      ]"
      :show-buttons="false"
    />
  </div>
</template>

<script>
import { createComputedSetterForCollectionField } from "@/field_utils.js";
import { getCollectionSampleList } from "@/server_fetch_utils";
import TinyMceInline from "@/components/TinyMceInline";
import Creators from "@/components/Creators";
import CollectionRelationshipVisualization from "@/components/CollectionRelationshipVisualization";
import DynamicDataTable from "@/components/DynamicDataTable";

export default {
  components: {
    TinyMceInline,
    Creators,
    CollectionRelationshipVisualization,
    DynamicDataTable,
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
        { field: "name", header: "Sample name", label: "Sample Name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula", label: "Formula" },
        { field: "date", header: "Date", label: "Date" },
        { field: "creators", header: "Creators", body: "Creators", label: "Creators" },
        { field: "nblocks", header: "# of blocks", label: "Blocks" },
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
  },
};
</script>
