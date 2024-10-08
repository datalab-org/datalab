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

/**
 * Validates an ID against various criteria and checks if it's already in use.
 *
 * @param {string} id - The ID to validate.
 * @param {string[]} [takenIds=[]] - Array of already taken item IDs.
 * @param {string[]} [existingIds=[]] - Array of IDs already known to exist.
 *
 * @returns {string} An empty string if the ID is valid and not in use, otherwise an error message.
 *                   If the ID is in use, it returns a string error message with an HTML link to edit the ID.
 *
 * @throws {TypeError} If id is not a string when it's not null.
 *
 * @example
 * // Returns an empty string for a valid ID
 * validateEntryID("valid_id_123");
 *
 * @example
 * // Returns an error message for an invalid ID
 * validateEntryID("invalid id with spaces");
 *
 * @example
 * // Returns a message with a link if the ID is already in use
 * validateEntryID("taken_id", ["taken_id"]);
 */
export function validateEntryID(id, takenIds = [], existingIds = []) {
  if (id == null) {
    return "";
  }

  if (takenIds.includes(id) || existingIds.includes(id)) {
    return `<a href='edit/${id}'>${id}</a> already in use.`;
  }

  if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
    return "ID can only contain alphanumeric characters, dashes ('-'), and underscores ('_').";
  }
  if (/^[._-]/.test(id) | /[._-]$/.test(id)) {
    return "ID cannot start or end with punctuation";
  }
  if (id.length < 1 || id.length > 40) {
    return "ID must be between 1 and 40 characters.";
  }
  return "";
}
