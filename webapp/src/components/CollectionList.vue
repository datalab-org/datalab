<template>
  <div>
    <FormattedCollectionName
      v-for="collection in collections"
      :key="collection.collection_id"
      :collection_id="collection.collection_id"
      enable-click
      enable-modified-click
    />
  </div>
</template>

<script>
import FormattedCollectionName from "@/components/FormattedCollectionName.vue";

export default {
  components: {
    FormattedCollectionName,
  },
  props: {
    collections: {
      type: Array,
    },
  },
  data() {
    return {};
  },
};
</script>
