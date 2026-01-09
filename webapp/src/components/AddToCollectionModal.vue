<template>
  <form class="modal-enclosure" data-testid="add-to-collection-form" @submit.prevent="submitForm">
    <Modal
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', $event)"
      @submit="submitForm"
    >
      <template #header> Add to collections </template>
      <template #body>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="items-selected" class="col-form-label">Items Selected:</label>
            <div id="items-selected" class="dynamic-input">
              <FormattedItemName
                v-for="(item, index) in itemsSelected"
                :key="index"
                :item_id="item.item_id"
                :item-type="item.type"
                enable-click
              />
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="addToCollectionLabel">Insert into collection:</label>
            <CollectionSelect
              id="collection-select"
              v-model="addToCollection"
              aria-labelledby="addToCollectionLabel"
              multiple
            />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import FormattedItemName from "@/components/FormattedItemName";
import CollectionSelect from "@/components/CollectionSelect.vue";

import {
  addItemsToCollection,
  getSampleList,
  getStartingMaterialList,
  getEquipmentList,
} from "@/server_fetch_utils";

export default {
  name: "AddToCollectionsModal",
  components: {
    Modal,
    FormattedItemName,
    CollectionSelect,
  },
  props: {
    modelValue: Boolean,
    itemsSelected: {
      type: Array,
      required: true,
    },
  },
  emits: ["update:modelValue", "itemsUpdated"],
  data() {
    return {
      addToCollection: [],
    };
  },
  methods: {
    async submitForm() {
      try {
        const collectionIds = this.addToCollection.map((collection) => collection.collection_id);
        const refcodes = this.itemsSelected.map((item) => item.refcode);

        for (const collectionId of collectionIds) {
          await addItemsToCollection(collectionId, refcodes);
        }
        this.$emit("itemsUpdated");
        if (this.itemsSelected.some((item) => item.type === "samples")) {
          getSampleList();
        } else if (this.itemsSelected.some((item) => item.type === "startingMaterials")) {
          getStartingMaterialList();
        } else if (this.itemsSelected.some((item) => item.type === "equipment")) {
          getEquipmentList();
        }
        console.log("Items added successfully.");
        this.$emit("update:modelValue", false);
      } catch (error) {
        console.error("Error adding items to collections:", error);
      }
    },
  },
};
</script>

<style scoped>
.dynamic-input {
  display: flex;
  flex-wrap: wrap;
  border: 1px solid #ced4da;
  padding: 0.375rem 0.75rem;
  border-radius: 0.25rem;
  max-width: 100%;
  box-sizing: border-box;
  gap: 0.2em;
}
</style>
