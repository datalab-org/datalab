<template>
  <form class="modal-enclosure" data-testid="create-equipment-form" @submit.prevent="submitForm">
    <Modal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
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
            <label for="collection-select">Insert into collection:</label>
            <CollectionSelect
              id="collection-select"
              v-model="startInCollection"
              aria-labelledby="startInCollection"
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

import { addItemsToCollection } from "@/server_fetch_utils";

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
      startInCollection: [],
    };
  },
  methods: {
    async submitForm() {
      try {
        const collectionIds = this.startInCollection.map((collection) => collection.immutable_id);
        const refcodes = this.itemsSelected.map((item) => item.refcode);

        for (const collectionId of collectionIds) {
          await addItemsToCollection(collectionId, refcodes);
        }
        this.$emit("itemsUpdated");

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
