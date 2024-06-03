<template>
  <div v-if="isFetchError" class="alert alert-danger">
    Server Error. Collection list not retreived.
  </div>
  <table class="table table-hover table-sm" data-testid="collection-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Title</th>
        <th scope="col">Creators</th>
        <th scope="col"></th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="collection in collections"
        :id="collection.collection_id"
        :key="collection.collection_id"
        @click.exact="goToEditPage(collection.collection_id)"
        @click.meta="openEditPageInNewTab(collection.collection_id)"
        @click.ctrl="openEditPageInNewTab(collection.collection_id)"
      >
        <td align="left">
          <FormattedItemName
            :item_id="collection.collection_id"
            :item-type="collection.type"
            enable-modified-click
          />
        </td>
        <td align="left">{{ collection.title }}</td>
        <td align="center"><Creators :creators="collection.creators" /></td>
        <td align="right">
          <button
            type="button"
            class="close"
            aria-label="delete"
            @click.stop="deleteCollection(collection)"
          >
            <span aria-hidden="true" style="color: grey">&times;</span>
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { getCollectionList, deleteCollection } from "@/server_fetch_utils.js";
import FormattedItemName from "@/components/FormattedItemName";
import Creators from "@/components/Creators";
import { GRAVATAR_STYLE } from "@/resources.js";

export default {
  components: {
    FormattedItemName,
    Creators,
  },
  data() {
    return {
      isFetchError: false,
      gravatar_style: GRAVATAR_STYLE,
    };
  },
  computed: {
    collections() {
      return this.$store.state.collection_list;
    },
  },
  created() {
    this.getCollections();
  },
  methods: {
    goToEditPage(collection_id) {
      this.$router.push(`/collections/${collection_id}`);
    },
    openEditPageInNewTab(collection_id) {
      window.open(`/collections/${collection_id}`, "_blank");
    },
    // should also check response.OK? And retry if
    getCollections() {
      getCollectionList().catch(() => {
        this.isFetchError = true;
      });
    },
    deleteCollection(collection) {
      if (
        confirm(
          `Are you sure you want to delete collection "${collection.collection_id}"?\nThis will not delete any items.`,
        )
      ) {
        deleteCollection(collection.collection_id, collection);
      }
    },
  },
};
</script>

<style scoped>
.avatar {
  border: 2px solid grey;
  border-radius: 50%;
}
.avatar:hover {
  border: 2px solid skyblue;
}
</style>
