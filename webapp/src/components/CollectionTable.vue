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
        :id="collection.collection_id"
        v-for="collection in collections"
        :key="collection.collection_id"
        v-on:click.exact="goToEditPage(collection.collection_id)"
        v-on:click.meta="openEditPageInNewTab(collection.collection_id)"
        v-on:click.ctrl="openEditPageInNewTab(collection.collection_id)"
      >
        <td align="left">
          <FormattedItemName
            :item_id="collection.collection_id"
            :itemType="collection.type"
            enableModifiedClick
          />
        </td>
        <td align="left">{{ collection.title }}</td>
        <td align="center"><Creators :creators="collection.creators" /></td>
        <td align="right">
          <button
            type="button"
            class="close"
            @click.stop="deleteCollection(collection)"
            aria-label="delete"
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
  created() {
    this.getCollections();
  },
  components: {
    FormattedItemName,
    Creators,
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
