import store from "@/store/index.js";
//import { debounce } from 'lodash';

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
        block_data: { [block_field]: value === "" ? null : value },
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
      //set: debounce(function(value) {
      console.log(`comp setter called for '${item_field}' with value: '${value}'`);
      store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { [item_field]: value === "" ? null : value },
      });
      //}, 500),
    },
  };
}

export function createComputedSetterForCollectionField(collection_field) {
  return {
    get() {
      if (this.collection_id in store.state.all_collection_data) {
        return store.state.all_collection_data[this.collection_id][collection_field];
      }
    },
    set(value) {
      //set: debounce( function(value) {
      console.log(`collection comp setter called for '${collection_field}' with value: '${value}'`);
      store.commit("updateCollectionData", {
        collection_id: this.collection_id,
        block_data: { [collection_field]: value },
      });
      //}, 500),
    },
  };
}
