import store from "@/store/index.js";

// Amazingly (and perhaps dangerously) the this context used here is the this from
// the component which this function is called for.
// For this function to work, the this context needs to have item_id and block_id
export function createComputedSetterForBlockField(block_field) {
  return {
    get() {
      if (this.item_id in store.state.all_item_data) {
        return store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id][block_field];
      } else {
        return "";
      }
    },
    set(value) {
      store.commit("updateBlockData", {
        item_id: this.item_id,
        block_id: this.block_id,
        block_data: { [block_field]: value ? value : null },
      });
    },
  };
}

export function createComputedSetterForItemField(item_field) {
  return {
    get() {
      if (this.item_id in store.state.all_item_data) {
        return store.state.all_item_data[this.item_id][item_field];
      }
    },
    set(value) {
      console.log("comp setter called with value:");
      console.log(value);
      store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { [item_field]: value ? value : null },
      });
    },
  };
}
