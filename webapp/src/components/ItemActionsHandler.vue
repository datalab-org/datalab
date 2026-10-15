<template>
  <div
    v-if="isDeletingItems"
    class="position-fixed d-flex justify-content-center align-items-center"
    style="background-color: rgba(255, 255, 255, 0.7); z-index: 1050; inset: 0"
  >
    <div class="card p-3 shadow-sm">
      <div class="text-center">
        <font-awesome-icon
          :icon="['fa', 'sync']"
          class="fa-2x text-primary mb-2"
          :spin="true"
          aria-label="loading"
        />
        <p class="mb-0 mt-1">Deleting {{ pendingItems.length }} item(s)...</p>
      </div>
    </div>
  </div>
  <AddToCollectionModal
    v-model="addToCollectionModalIsOpen"
    :items-selected="pendingItems"
    @items-updated="complete"
  />
  <BatchShareModal
    v-model="batchShareModalIsOpen"
    :items-selected="pendingItems"
    @items-updated="complete"
  />
</template>

<script>
import AddToCollectionModal from "@/components/AddToCollectionModal";
import BatchShareModal from "@/components/BatchShareModal";
import { DialogService } from "@/services/DialogService";
import { ADD_TO_COLLECTION_ACTION, SHARE_ACTION, DELETE_ACTION } from "@/utils/itemActions.js";

import {
  deleteSample,
  deleteCollection,
  deleteStartingMaterial,
  deleteEquipment,
  deleteTag,
} from "@/server_fetch_utils.js";

/**
 * Carries out the action requests `{ action, items, source }` emitted by a table's row and
 * selection controls (see `utils/itemActions.js`): it owns the modals, the confirmation, the
 * API calls and the error handling, and emits `completed` with the request once the action
 * has gone through, so the table can update its selection.
 */
export default {
  name: "ItemActionsHandler",
  components: {
    AddToCollectionModal,
    BatchShareModal,
  },
  props: {
    dataType: {
      type: String,
      required: true,
    },
  },
  emits: ["completed"],
  expose: ["handle"],
  data() {
    return {
      pendingRequest: null,
      addToCollectionModalIsOpen: false,
      batchShareModalIsOpen: false,
      isDeletingItems: false,
    };
  },
  computed: {
    pendingItems() {
      return this.pendingRequest?.items || [];
    },
  },
  methods: {
    handle(request) {
      this.pendingRequest = request;
      if (request.action === ADD_TO_COLLECTION_ACTION.key) {
        this.addToCollectionModalIsOpen = true;
      } else if (request.action === SHARE_ACTION.key) {
        this.batchShareModalIsOpen = true;
      } else if (request.action === DELETE_ACTION.key) {
        this.confirmDeletion();
      }
    },
    complete() {
      this.$emit("completed", this.pendingRequest);
      this.pendingRequest = null;
    },
    async confirmDeletion() {
      const items = this.pendingItems;
      const isTags = this.dataType === "tags";
      const ids = items.map((x) => x.item_id || x.collection_id || x.immutable_id);
      // Tags have no human id; label them by name instead of immutable_id.
      const labels = isTags ? items.map((x) => x.name) : ids;
      let labelText = labels;
      if (labels.length > 10) {
        labelText = labels.slice(0, 10).join(", ") + ", ...";
      }
      const confirmed = await DialogService.confirm({
        title: "Confirm Deletion",
        message: isTags
          ? `Are you sure you want to delete ${items.length} selected tag(s)? They will be removed from any items using them. (${labelText})`
          : `Are you sure you want to delete ${items.length} selected item(s)? (${labelText})`,
        type: "warning",
      });
      if (!confirmed) {
        this.pendingRequest = null;
        return;
      }
      if (await this.deleteItems(ids)) {
        this.complete();
      } else {
        this.pendingRequest = null;
      }
    },
    async deleteItems(ids) {
      const deleteFunctions = {
        samples: (id) => deleteSample(id),
        collections: (id) => deleteCollection(id, { collection_id: id }),
        startingMaterials: (id) => deleteStartingMaterial(id),
        equipment: (id) => deleteEquipment(id),
        tags: (id) => deleteTag(id),
      };
      const deleteFunction = deleteFunctions[this.dataType];
      if (!deleteFunction) return false;

      this.isDeletingItems = true;
      try {
        await Promise.all(ids.map(deleteFunction));
        return true;
      } catch (error) {
        console.error("Error during deletion:", error);
        DialogService.error({
          title: "Deletion Failed",
          message: error.message || error,
        });
        return false;
      } finally {
        this.isDeletingItems = false;
      }
    },
  },
};
</script>
