<template>
  <form @submit.prevent="submitForm" class="modal-enclosure" data-testid="create-equipment-form">
    <Modal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)">
      <template v-slot:header> Add to collections </template>
      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="items-selected" class="col-form-label">Items Selected:</label>
            <div id="items-selected" class="dynamic-input">
              <FormattedItemName
                v-for="(item, index) in itemsSelected"
                :key="index"
                :item_id="item.item_id"
                :itemType="item.type"
                enableClick
              />
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label for="collection-select">(Optional) Insert into collection:</label>
            <CollectionSelect
              id="collection-select"
              aria-labelledby="startInCollection"
              multiple
              v-model="startInCollection"
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

import { saveItem } from "@/server_fetch_utils";

export default {
  name: "AddToCollectionsModal",
  props: {
    modelValue: Boolean,
    itemsSelected: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      startInCollection: [], // Ensure startInCollection is initialized
    };
  },
  emits: ["update:modelValue"],
  methods: {
    async submitForm() {
      for (const item of this.itemsSelected) {
        try {
          await saveItem(item.item_id);
          console.log(`Item ${item.item_id} saved successfully.`);
        } catch (error) {
          console.error(`Error saving item ${item.item_id}:`, error);
        }
      }
    },
  },
  components: {
    Modal,
    FormattedItemName,
    CollectionSelect,
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
