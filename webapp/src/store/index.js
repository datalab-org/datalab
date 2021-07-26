import { createStore } from 'vuex'
// import { set } from 'vue'

export default createStore({
	state: {
		all_sample_data: {}, // keys: sample_ids, vals: objects containing all data
		sample_list: [],
		saved_status: {},
		updating: {},
		updatingDelayed: {},
		remoteDirectoryTree: {},
		remoteDirectoryTreeSecondsSinceLastUpdate: null,
		files: {},
	},
	mutations: {
		test_mutation(state, data_val) {
			state.all_sample_data = data_val
		},
		setSampleList(state, sample_summaries) {
			// sample_summary is an array of json objects summarizing the available samples
			state.sample_list = sample_summaries
		},
		appendToSampleList(state, sample_summary) {
			//sample should be a json object sumarizing the available samples
			state.sample_list.push(sample_summary)
		},
		deleteFromSampleList(state, sample_summary) {
			const index = state.sample_list.indexOf(sample_summary)
			// const index = state.sample_list.map(function(e) { return e.sample_id; }).indexOf(sample_id);
			if (index > -1) {
				state.sample_list.splice(index, 1);
			}
			else { console.log("deleteFromSampleList couldn't find the object") }
		},
		createSampleData(state, payload) {
			// payload should have the following fields:
			// sample_id, sample_data
			// Object.assign(state.all_sample_data[payload.sample_id], payload.sample_data)
			state.all_sample_data[payload.sample_id] = payload.sample_data
			state.saved_status[payload.sample_id] = true
		},
		updateFiles(state, files_data) {
			// payload should be an object with file ids as key and file data as values
			// Note: this will overwrite any entries with the same file_ids
			Object.assign(state.files, files_data)
		},
		addFileToSample(state, payload) {
			state.all_sample_data[payload.sample_id].file_ObjectIds.push(payload.file_id)
		},
		removeFileFromSample(state, payload) {
			var file_ids = state.all_sample_data[payload.sample_id].file_ObjectIds
			const index = file_ids.indexOf(payload.file_id)
			if (index > -1) {
				file_ids.splice(index, 1);
			}
		},
		setRemoteDirectoryTree(state, remoteDirectoryTree) {
			state.remoteDirectoryTree = remoteDirectoryTree
		},
		setRemoteDirectoryTreeSecondsSinceLastUpdate(state, secondsSinceLastUpdate) {
			state.remoteDirectoryTreeSecondsSinceLastUpdate = secondsSinceLastUpdate
		},
		addABlock(state, payload) {
			// payload: sample_id, new_block_obj, new_display_order

			// I should actually throw an error if this fails!
			console.assert(payload.sample_id == payload.new_block_obj.sample_id,
				"The block has a different sample_id (%s) than the sample_id provided to addABlock (%s)",
				payload.sample_id, payload.new_block_obj.sample_id)

			let new_block_id = payload.new_block_obj.block_id
			state.all_sample_data[payload.sample_id]["blocks_obj"][new_block_id] = payload.new_block_obj
			state.all_sample_data[payload.sample_id]["display_order"] = payload.new_display_order

			state.saved_status[payload.sample_id] = false
		},
		updateBlockData(state, payload) {
			// requires the following fields in payload:
			// sample_id, block_id, block_data
			console.log("updating block data with:", payload)
			Object.assign(state.all_sample_data[payload.sample_id]["blocks_obj"][payload.block_id], payload.block_data)
			state.saved_status[payload.sample_id] = false
		},
		updateSampleData(state, payload) {
			//requires the following fields in payload:
			// sample_id, block_data
			Object.assign(state.all_sample_data[payload.sample_id], payload.block_data)
			state.saved_status[payload.sample_id] = false
		},
		setSaved(state, payload) {
			// requires the following fields in payload:
			// sample_id, isSaved
			state.saved_status[payload.sample_id] = payload.isSaved
		},
		removeBlockFromDisplay(state, payload) {
			// requires the following fields in payload:
			// sample_id, block_id
			var display_order = state.all_sample_data[payload.sample_id].display_order
			const index = display_order.indexOf(payload.block_id)
			if (index > -1) {
				display_order.splice(index, 1);
			}
		},
		addFile(state, payload) {
			// requires the following fileds in payload:
			// sample_id, filename
			state.all_sample_data[payload.sample_id].files.push(payload.filename)
		},
		removeFilename(state, payload) {
			// requires the following fields in payload:
			// sample_id, filename
			var files = state.all_sample_data[payload.sample_id].files
			const index = files.indexOf(payload.filename)
			if (index > -1) {
				files.splice(index, 1)
			}
		},
		swapBlockDisplayOrder(state, payload) {
			// requires the following fields in payload:
			// sample_id, index1, index2
			// Swaps index1 and index2 in sample_id.display_order
			var display_order = state.all_sample_data[payload.sample_id].display_order
			if ((payload.index1 < display_order.length) && (payload.index2 < display_order.length)) {
				[display_order[payload.index1], display_order[payload.index2]] = [display_order[payload.index2], display_order[payload.index1]]
			}
			state.saved_status[payload.sample_id] = false
		},
		setBlockUpdating(state, block_id) {
			state.updating[block_id] = true;
			state.updatingDelayed[block_id] = true;
		},
		async setBlockNotUpdating(state, block_id) {
			state.updating[block_id] = false;
			await new Promise(resolve => setTimeout(resolve, 500));
			state.updatingDelayed[block_id] = false; // delayed by 0.5 s, helpful for some animations
		}
	},
	getters: {
		testGetter: (state) => state.all_sample_data,
		getSample: (state) => (sample_id) => {
				return state.all_sample_data[sample_id]
			},
		getBlockBySampleIDandBlockID: (state) => (sample_id, block_id) => {
			console.log("getBlockBySampleIDandBlockID called with:", sample_id, block_id)
			return state.all_sample_data[sample_id]["blocks_obj"][block_id]
		},
	},
	actions: {
	},
	modules: {
	},
	plugins: [],
})
