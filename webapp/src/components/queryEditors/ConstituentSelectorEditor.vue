<template>
  <ItemSelect
    v-model="selectedItem"
    :types-to-query="CONSTITUENT_ITEM_TYPES"
    placeholder="Search items..."
  />
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";

// Constituents are matched on `<constituent>.item.item_id`, so the value is an item ID.
const CONSTITUENT_ITEM_TYPES = ["samples", "starting_materials", "cells", "equipment"];

export default {
  name: "ConstituentSelectorEditor",
  components: { ItemSelect },
  props: {
    modelValue: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
  data() {
    return { CONSTITUENT_ITEM_TYPES, pickedItem: null };
  },
  computed: {
    // ItemSelect works with item objects, the rule with the item's ID.
    selectedItem: {
      get() {
        if (!this.modelValue) return null;
        if (this.pickedItem?.item_id === this.modelValue) return this.pickedItem;
        return { item_id: this.modelValue, name: this.modelValue };
      },
      set(item) {
        this.pickedItem = item;
        this.$emit("update:modelValue", item?.item_id || undefined);
      },
    },
  },
};
</script>
