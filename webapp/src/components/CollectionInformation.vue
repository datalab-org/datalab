<template>
  <div class="container">
    <div id="collection-information" class="form-row">
      <div class="form-group col-md-2">
        <label for="item_id" class="mr-2">Collection ID</label>
        <input id="item_id" class="form-control-plaintext" v-model="CollectionID" />
      </div>
      <div class="form-group col-md-4">
        <label for="name" class="mr-2">Title</label>
        <input id="name" class="form-control" v-model="Title" />
      </div>
      <div class="col-md-1">
        <label id="creators" class="mr-2">Creators</label>
        <Creators :creators="CollectionCreators" :size="36" />
      </div>
    </div>
    <label id="description-label" class="mr-2">Description</label>
    <TinyMceInline
      aria-labelledby="description-label"
      v-model="CollectionDescription"
    ></TinyMceInline>

    <CollectionRelationshipVisualization :collection_id="collection_id" />
    <FancyCollectionSampleTable :collection_id="collection_id" />
  </div>
</template>

<script>
import { createComputedSetterForCollectionField } from "@/field_utils.js";
import FancyCollectionSampleTable from "@/components/FancyCollectionSampleTable";
import TinyMceInline from "@/components/TinyMceInline";
import Creators from "@/components/Creators";
import CollectionRelationshipVisualization from "@/components/CollectionRelationshipVisualization";

export default {
  props: {
    collection_id: String,
  },
  computed: {
    CollectionID: createComputedSetterForCollectionField("collection_id"),
    CollectionDescription: createComputedSetterForCollectionField("description"),
    Title: createComputedSetterForCollectionField("title"),
    Name: createComputedSetterForCollectionField("name"),
    CollectionCreators: createComputedSetterForCollectionField("creators"),
  },
  components: {
    TinyMceInline,
    FancyCollectionSampleTable,
    Creators,
    CollectionRelationshipVisualization,
  },
};
</script>
