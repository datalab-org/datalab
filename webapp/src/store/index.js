import { createStore } from "vuex";
import { blockTypes } from "@/resources.js";
// import { createLogger } from "vuex";
// import { set } from 'vue'

export default createStore({
  state: {
    all_item_data: {}, // keys: item_ids, vals: objects containing all data
    all_block_data: {},
    all_item_children: {},
    all_item_parents: {},
    blockTypes: {},
    sample_list: [],
    starting_material_list: [],
    saved_status: {},
    updating: {},
    updatingDelayed: {},
    remoteDirectoryTree: {},
    remoteDirectoryTreeSecondsSinceLastUpdate: null,
    files: {},
    itemGraphData: null,
    remoteDirectoryTreeIsLoading: false,
    fileSelectModalIsOpen: false,
  },
  mutations: {
    setSampleList(state, sampleSummaries) {
      // sampleSummaries is an array of json objects summarizing the available samples
      state.sample_list = sampleSummaries;
    },
    setBlockTypes(state, fetchedBlockTypes) {
      // list of block types implemented in this API, alongside their metadata
      state.blockTypes = {};
      for (var b in fetchedBlockTypes) {
        state.blockTypes[b.id] = b.attributes;
      }

      // loop over JS block types from resources.js and add them to the store if they are missing
      for (var block in blockTypes) {
        if (!(block in fetchedBlockTypes)) {
          state.blockTypes[block] = blockTypes[b];
        } else {
          state.blockTypes[block].component = blockTypes[b].component;
        }
      }
    },
    setStartingMaterialList(state, startingMaterialSummaries) {
      // startingMaterialSummaries is an array of json objects summarizing the available samples
      state.starting_material_list = startingMaterialSummaries;
    },
    appendToSampleList(state, sampleSummary) {
      // sampleSummary is a json object summarizing the new sample
      state.sample_list.push(sampleSummary);
    },
    prependToSampleList(state, sampleSummary) {
      // sampleSummary is a json object summarizing the new sample
      state.sample_list.unshift(sampleSummary);
    },
    deleteFromSampleList(state, item_id) {
      const index = state.sample_list.map((e) => e.item_id).indexOf(item_id);
      if (index > -1) {
        state.sample_list.splice(index, 1);
      } else {
        console.log(`deleteFromSampleList couldn't find the item with id ${item_id}`);
      }
    },
    createItemData(state, payload) {
      // payload should have the following fields:
      // item_id, item_data
      // Object.assign(state.all_sample_data[payload.item_data], payload.item_data)
      state.all_item_data[payload.item_id] = payload.item_data;
      state.all_item_children[payload.item_id] = payload.child_items;
      state.all_item_parents[payload.item_id] = payload.parent_items;
      state.saved_status[payload.item_id] = true;
    },
    updateFiles(state, files_data) {
      // payload should be an object with file ids as key and file data as values
      // Note: this will overwrite any entries with the same file_ids
      Object.assign(state.files, files_data);
    },
    addFileToSample(state, payload) {
      state.all_item_data[payload.item_id].file_ObjectIds.push(payload.file_id);
    },
    removeFileFromSample(state, payload) {
      var file_ids = state.all_item_data[payload.item_id].file_ObjectIds;
      const index = file_ids.indexOf(payload.file_id);
      if (index > -1) {
        file_ids.splice(index, 1);
      }
    },
    setRemoteDirectoryTree(state, remoteDirectoryTree) {
      state.remoteDirectoryTree = remoteDirectoryTree.data;
    },
    setRemoteDirectoryTreeSecondsSinceLastUpdate(state, secondsSinceLastUpdate) {
      state.remoteDirectoryTreeSecondsSinceLastUpdate = secondsSinceLastUpdate;
    },
    addABlock(state, { item_id, new_block_obj, new_block_insert_index }) {
      // payload: item_id, new_block_obj, new_display_order

      // I should actually throw an error if this fails!
      console.assert(
        item_id == new_block_obj.item_id,
        "The block has a different item_id (%s) than the item_id provided to addABlock (%s)",
        item_id,
        new_block_obj.item_id
      );
      console.log(`addABlock called with: ${item_id}, ${new_block_obj}, ${new_block_insert_index}`);
      let new_block_id = new_block_obj.block_id;
      state.all_item_data[item_id]["blocks_obj"][new_block_id] = new_block_obj;
      if (new_block_insert_index) {
        state.all_item_data[item_id]["display_order"].splice(
          new_block_insert_index,
          0,
          new_block_id
        );
      }
      // if new_block_insert_index is None, then block is inserted at the end
      else {
        state.all_item_data[item_id]["display_order"].push(new_block_id);
      }
      state.saved_status[item_id] = false;
    },
    updateBlockData(state, payload) {
      // requires the following fields in payload:
      // item_id, block_id, block_data
      console.log("updating block data with:", payload);
      Object.assign(
        state.all_item_data[payload.item_id]["blocks_obj"][payload.block_id],
        payload.block_data
      );
      state.saved_status[payload.item_id] = false;
    },
    updateItemData(state, payload) {
      //requires the following fields in payload:
      // item_id, block_data
      Object.assign(state.all_item_data[payload.item_id], payload.block_data);
      state.saved_status[payload.item_id] = false;
    },
    setSaved(state, payload) {
      // requires the following fields in payload:
      // item_id, isSaved
      state.saved_status[payload.item_id] = payload.isSaved;
    },
    removeBlockFromDisplay(state, payload) {
      // requires the following fields in payload:
      // item_id, block_id
      var display_order = state.all_item_data[payload.item_id].display_order;
      const index = display_order.indexOf(payload.block_id);
      if (index > -1) {
        display_order.splice(index, 1);
      }
    },
    addFile(state, payload) {
      // requires the following fileds in payload:
      // item_id, filename
      state.all_item_data[payload.item_id].files.push(payload.filename);
    },
    removeFilename(state, payload) {
      // requires the following fields in payload:
      // item_id, filename
      var files = state.all_item_data[payload.item_id].files;
      const index = files.indexOf(payload.filename);
      if (index > -1) {
        files.splice(index, 1);
      }
    },
    swapBlockDisplayOrder(state, payload) {
      // requires the following fields in payload:
      // item_id, index1, index2
      // Swaps index1 and index2 in item_id.display_order
      var display_order = state.all_item_data[payload.item_id].display_order;
      if (payload.index1 < display_order.length && payload.index2 < display_order.length) {
        [display_order[payload.index1], display_order[payload.index2]] = [
          display_order[payload.index2],
          display_order[payload.index1],
        ];
      }
      state.saved_status[payload.item_id] = false;
    },
    setBlockUpdating(state, block_id) {
      state.updating[block_id] = true;
      state.updatingDelayed[block_id] = true;
    },
    async setBlockNotUpdating(state, block_id) {
      state.updating[block_id] = false;
      await new Promise((resolve) => setTimeout(resolve, 500));
      state.updatingDelayed[block_id] = false; // delayed by 0.5 s, helpful for some animations
    },
    setFileSelectModalOpenStatus(state, isOpen) {
      state.fileSelectModalIsOpen = isOpen;
    },
    setRemoteDirectoryTreeIsLoading(state, isLoading) {
      state.remoteDirectoryTreeIsLoading = isLoading;
    },
    setItemGraph(state, payload) {
      state.itemGraphData = payload;
    },
  },
  getters: {
    getItem: (state) => (item_id) => {
      return state.all_item_data[item_id];
    },
    getBlockByItemIDandBlockID: (state) => (item_id, block_id) => {
      console.log("getBlockBySampleIDandBlockID called with:", item_id, block_id);
      return state.all_sample_data[item_id]["blocks_obj"][block_id];
    },
  },
  actions: {},
  modules: {},
  // plugins: [createLogger()],
});
