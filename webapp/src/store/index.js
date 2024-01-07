import { createStore } from "vuex";
// import { createLogger } from "vuex";
// import { set } from 'vue'

export default createStore({
  state: {
    all_item_data: {}, // keys: item_ids, vals: objects containing all data
    all_block_data: {},
    all_item_children: {},
    all_item_parents: {},
    all_collection_data: {},
    all_collection_children: {},
    all_collection_parents: {},
    sample_list: [],
    equipment_list: [],
    starting_material_list: [],
    collection_list: [],
    saved_status_items: {},
    saved_status_blocks: {},
    saved_status_collections: {},
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
    setStartingMaterialList(state, startingMaterialSummaries) {
      // startingMaterialSummaries is an array of json objects summarizing the available starting materials
      state.starting_material_list = startingMaterialSummaries;
    },
    setCollectionList(state, collectionSummaries) {
      // collectionSummaries is an array of json objects summarizing the available collections
      state.collection_list = collectionSummaries;
    },
    setEquipmentList(state, equipmentSummaries) {
      // equipmentSummary is an array of json objects summarizing the available samples
      state.equipment_list = equipmentSummaries;
    },
    appendToSampleList(state, sampleSummary) {
      // sampleSummary is a json object summarizing the new sample
      state.sample_list.push(sampleSummary);
    },
    prependToSampleList(state, sampleSummary) {
      // sampleSummary is a json object summarizing the new sample
      state.sample_list.unshift(sampleSummary);
    },
    prependToEquipmentList(state, equipmentSummary) {
      // sampleSummary is a json object summarizing the new sample
      state.equipment_list.unshift(equipmentSummary);
    },
    prependToCollectionList(state, collectionSummary) {
      // collectionSummary is a json object summarizing the new collection
      state.collection_list.unshift(collectionSummary);
    },
    deleteFromSampleList(state, item_id) {
      const index = state.sample_list.map((e) => e.item_id).indexOf(item_id);
      if (index > -1) {
        state.sample_list.splice(index, 1);
      } else {
        console.log(`deleteFromSampleList couldn't find the item with id ${item_id}`);
      }
    },
    deleteFromCollectionList(state, collection_summary) {
      const index = state.collection_list.indexOf(collection_summary);
      if (index > -1) {
        state.collection_list.splice(index, 1);
      } else {
        console.log("deleteFromCollectionList couldn't find the object");
      }
    },
    createItemData(state, payload) {
      // payload should have the following fields:
      // item_id, item_data, child_items, parent_items
      // Object.assign(state.all_sample_data[payload.item_data], payload.item_data)
      state.all_item_data[payload.item_id] = payload.item_data;
      state.all_item_children[payload.item_id] = payload.child_items;
      state.all_item_parents[payload.item_id] = payload.parent_items;
      state.saved_status_items[payload.item_id] = true;
    },
    setCollectionData(state, payload) {
      // payload should have the following fields:
      // collection_id, data, child_items
      // Object.assign(state.all_sample_data[payload.item_data], payload.item_data)
      state.all_collection_data[payload.collection_id] = payload.data;
      state.saved_status_collections[payload.collection_id] = true;
    },
    setCollectionSampleList(state, payload) {
      state.all_collection_children[payload.collection_id] = payload.child_items;
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
        new_block_obj.item_id,
      );
      console.log(`addABlock called with: ${item_id}, ${new_block_obj}, ${new_block_insert_index}`);
      let new_block_id = new_block_obj.block_id;
      state.all_item_data[item_id]["blocks_obj"][new_block_id] = new_block_obj;
      if (new_block_insert_index) {
        state.all_item_data[item_id]["display_order"].splice(
          new_block_insert_index,
          0,
          new_block_id,
        );
      }
      // if new_block_insert_index is None, then block is inserted at the end
      else {
        state.all_item_data[item_id]["display_order"].push(new_block_id);
      }
    },
    updateBlockData(state, payload) {
      // requires the following fields in payload:
      // item_id, block_id, block_data
      console.log("updating block data with:", payload);
      Object.assign(
        state.all_item_data[payload.item_id]["blocks_obj"][payload.block_id],
        payload.block_data,
      );
      state.saved_status_blocks[payload.block_id] = false;
    },
    updateItemData(state, payload) {
      //requires the following fields in payload:
      // item_id, item_data
      Object.assign(state.all_item_data[payload.item_id], payload.item_data);
      state.saved_status_items[payload.item_id] = false;
    },
    updateCollectionData(state, payload) {
      //requires the following fields in payload:
      // item_id, block_data
      Object.assign(state.all_collection_data[payload.collection_id], payload.block_data);
      state.saved_status_collections[payload.collection_id] = false;
    },
    setItemSaved(state, payload) {
      // requires the following fields in payload:
      // item_id, isSaved
      state.saved_status_items[payload.item_id] = payload.isSaved;
    },
    setBlockSaved(state, payload) {
      // requires the following fields in payload:
      // block_id, isSaved
      state.saved_status_blocks[payload.block_id] = payload.isSaved;
    },
    setSavedCollection(state, payload) {
      // requires the following fields in payload:
      // item_id, isSaved
      state.saved_status_collections[payload.collection_id] = payload.isSaved;
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
      state.saved_status_items[payload.item_id] = false;
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
