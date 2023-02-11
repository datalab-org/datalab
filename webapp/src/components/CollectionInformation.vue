<template>
  <div class="container">
    <div id="collection-information" class="form-row">
      <div class="form-group col-md-2">
        <label for="collection_id" class="mr-2">Collection ID</label>
        <input
          id="collection_id"
          class="form-control-plaintext"
          readonly="true"
          :value="collection_id"
        />
      </div>
      <div class="form-group col-md-7">
        <label for="title" class="mr-2">Title</label>
        <input id="title" class="form-control" v-model="Title" />
      </div>
      <div class="form-group col-md-3">
        <label for="date" class="mr-2">Date Created</label>
        <input type="datetime-local" v-model="DateCreated" class="form-control" />
      </div>
    </div>
    <label id="description-label" class="mr-2">Description</label>
    <TinyMceInline
      aria-labelledby="description-label"
      v-model="CollectionDescription"
    ></TinyMceInline>

    <RelationshipVisualization :collection_id="collection_id" />

    <TableOfContents :informationSections="tableOfContentsSections" />
  </div>
</template>

<script>
import { createComputedSetterForCollectionField } from "@/field_utils.js";
import TinyMceInline from "@/components/TinyMceInline";
import RelationshipVisualization from "@/components/RelationshipVisualization";

export default {
  props: {
    collection_id: String,
  },
  data() {},
  computed: {
    CollectionDescription: createComputedSetterForCollectionField("description"),
    Title: createComputedSetterForCollectionField("title"),
    DateCreated: createComputedSetterForCollectionField("date"),
  },
  components: {
    TinyMceInline,
    RelationshipVisualization,
  },
};
</script>
