<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <div id="collection-information" class="form-row">
          <div class="col-md-2">
            <label id="creators" class="mr-2">Creators</label>
            <div>
              <Creators :creators="CollectionCreators" :size="36" />
            </div>
          </div>
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
