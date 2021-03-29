<template>
<div id="topScrollPoint"></div>
<nav class="navbar navbar-expand sticky-top bg-dark navbar-dark py-0 editor-navbar">
	<span class="navbar-brand" @click="scrollToID($event, 'topScrollPoint')">Flask-dl&nbsp;&nbsp;|&nbsp;&nbsp; {{ sample_id }} </span>
	<div class="navbar-nav">
		<a class="nav-item nav-link" href="/">Home</a>
		<div class="nav-item dropdown">
			<a class="nav-link dropdown-toggle ml-2" id="navbarDropdown" role="button"
			data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"
			@click="isMenuDropdownVisible = !isMenuDropdownVisible" >
			Add a block
			</a>
			<div class="dropdown-menu" style="display: block" aria-labelledby="navbarDropdown"
				v-show="isMenuDropdownVisible">
				<a v-for="block_kind in block_kinds"
					:key="block_kind.id"
					class="dropdown-item" href="#"
					@click="newBlock($event, block_kind.id)">
					{{ block_kind.description }}
				</a>
			</div>
		</div>
	</div>
	<div class="navbar-nav ml-auto">
		<span v-if="sample_data_loaded && !savedStatus" class="navbar-text unsaved-warning"> Unsaved changes </span>
		<span v-if="sample_data_loaded" class="navbar-text mx-2"><i>Last saved: {{ lastModified }}</i></span>
		<font-awesome-icon icon="save" fixed-width class="nav-item nav-link navbar-icon"
		@click="saveSample" /> 
	</div>
</nav>


<div class="container">
<!-- Sample information -->
	<div class="form-row">
		<div class="form-group col-md-2">
			<label for="sample_id" class="mr-2">Sample ID</label>
			<input id="sample_id" class="form-control-plaintext" readonly=true :value="sample_id" />
		</div>
		<div class="form-group col-md-7">
			<label for="name" class="mr-2">Name</label>
			<input id="name" class="form-control" v-model="Name"/>
		</div>
		<div class="form-group col-md-3">
			<label for="date" class="mr-2">Date</label>
			<input v-model="DateCreated" type="date" class="form-control" />
		</div>
	</div>
	<div class="form-row">
		<div class="form-group col-md-4">
			<label for="chemform" class="mr-2">Chemical formula</label>
			<input id="chemform" class="form-control" v-model="ChemForm" />
		</div>
	</div>

	<label class="mr-2">Description</label>

	<TinyMceInline v-model="SampleDescription"></TinyMceInline>

<!-- Table of Contents -->
	<label class="mr-2">Contents</label>
	<div class="card">
		<div class="card-body overflow-auto">
			<ol id="contents-ol">
				<li class="contents-item" v-for="block_id in sample_data.display_order" :key="block_id" @click="scrollToID($event, block_id)">
						<!-- <span class="contents-blocktype">{{ blocks[block_id].blocktype }} block</span> -->
						<!-- {{ block_id }} -->
						<span class="contents-blocktitle">{{ blocks[block_id].title }}</span>
				</li>
			</ol>
		</div>
	</div>


<!-- Files block -->
	<label class="mr-2">Files</label>
	<div class="card">
		<div class="card-body overflow-auto" id="filearea">
			<div class="file-group" v-for="file_id in file_ids" :key="file_id">	
				<a @click="deleteFile($event, file_id)">
					<font-awesome-icon icon="times" fixed-width class="delete-file-button" />
				</a>
				<a class="filelink" target="_blank" :href='`http://localhost:5001/${stored_files[file_id].url_path}`'>
					{{ stored_files[file_id].name }}
				</a>
				<font-awesome-icon v-if="stored_files[file_id].is_live==true" class="link-icon" v-show="true" :icon='["fa","link"]' />

			</div>
		</div>
		<div class="row">
			<button id="uppy-trigger" class="btn btn-default btn-sm mb-3 ml-4" type="button">Upload files...</button><!-- Surrounding divs so that buttons 	don't become full-width in the card -->
			<button class="btn btn-default btn-sm mb-3 ml-2" type="button" @click="serverFileModalIsOpen = true">Add files from server...</button>
		</div>

	</div>

	<hr />

<!-- List of blocks -->	
	<div v-for="block_id in sample_data.display_order" :key="block_id">
		<component :is="getBlockDisplayType(block_id)" 
			:sample_id="sample_id"
			:block_id="block_id"
		/>
	</div>

</div>

<!-- Modal for file selection from server -->
<div class="modal-enclosure">
	<Modal v-model="serverFileModalIsOpen">
		<template v-slot:header>
			Select files to add 
			<button @click="updateRemoteTree" :disabled="isLoadingRemoteTree" class="ml-4 btn btn-small btn-default">
				<font-awesome-icon v-show="isLoadingRemoteTree" :icon='["fa","sync"]'
				class="fa-spin" />
				Update tree
			</button>
		</template>
	
		<template v-slot:body>
			<SelectableFileTree :defaultSearchTerm="sample_id" @update:selectedEntries="selectedRemoteFiles = $event" />
		</template>
	
		<template v-slot:footer>
			<button 
				type="button" class="btn btn-info"
				:disabled='isLoadingRemoteFiles || selectedRemoteFiles.length<1'
				@click="loadSelectedRemoteFiles"
			>
				<font-awesome-icon v-show="isLoadingRemoteFiles" :icon='["fa","sync"]' class="fa-spin" />
				{{loadFilesButtonValue}}
			</button>
			<button type="button" class="btn  btn-secondary" data-dismiss="modal" @click="serverFileModalIsOpen = false">Close</button>
		</template>
	</Modal>
</div>

</template>

<script>

import DataBlockBase from "@/components/datablocks/DataBlockBase"
import ImageBlock from "@/components/datablocks/ImageBlock"
import XRDBlock from "@/components/datablocks/XRDBlock"
import CycleBlock from "@/components/datablocks/CycleBlock"
import TinyMceInline from "@/components/TinyMceInline"
import FileSelectDropdown from "@/components/FileSelectDropdown"
import SelectableFileTree from "@/components/SelectableFileTree"
import Modal from "@/components/Modal"

import { getSampleData,addABlock, saveSample, deleteFileFromSample, fetchRemoteTree, fetchCachedRemoteTree, addRemoteFileToSample } from "@/server_fetch_utils"

import setupUppy from '@/file_upload.js'

import {createComputedSetterForSampleField} from "@/field_utils.js"

import tinymce from 'tinymce/tinymce';

export default {
	data() {
		return {
			sample_id: this.$route.params.id,
			sample_data_loaded: false,
			block_kinds: [
				{ id:"test", description:"Test Block" },
				{ id:"comment", description:"Comment"},
				{ id:"image", description:"Image Block"},
				{ id: "xrd", description:"Powder XRD"},
				{ id: "cycle", description:"Echem Block"}
			],
			isMenuDropdownVisible: false,
			serverFileModalIsOpen: false,
			selectedRemoteFiles: [],
			isLoadingRemoteTree: false,
			isLoadingRemoteFiles: false, 
		}
	},
	methods: {
		async newBlock(event, block_kind, index=null) {
			var block_id = await addABlock(this.sample_id, block_kind, index)
			// close the dropdown scroll to the new block :)
			this.isMenuDropdownVisible = false
			var new_block_el = document.getElementById(block_id)
			new_block_el.scrollIntoView({behavior: 'smooth'})

		},
		scrollToID(event, id) {
			var element = document.getElementById(id)
			element.scrollIntoView({behavior: 'smooth'})
		},
		change_a_block(event, block_id) {
			let sample_id = this.sample_id
			let new_data = { block_id: 7, a_new_field: "foo bar"}
			console.log(new_data)
			this.$store.commit('updateBlockData', {
				sample_id,
				block_id,
				block_data: new_data
			});
			// this.$store.state.all_sample_data[sample_id]
		},
		getBlockDisplayType(block_id){
			var type = this.blocks[block_id].blocktype;
			if (type == "image") {return ImageBlock; }
			if (type == "xrd") { return XRDBlock; }
			if (type == "cycle") { return CycleBlock}
			return DataBlockBase;
		},

		saveSample() {
			// trigger the mce save so that they update the store with their content
			console.log("save sample clicked!")
			tinymce.editors.forEach( editor => editor.save() )
			saveSample(this.sample_id)
		},
		deleteFile(event, file_id) {
			console.log(`delete file button clicked!`)
			console.log(event)
			deleteFileFromSample(this.sample_id, file_id)
			return false
		},
		async getSampleData() {
			await getSampleData(this.sample_id);
			this.sample_data_loaded = true;
		},
		async loadCachedTree() {
			var response_json = await fetchCachedRemoteTree()
			// What happens if the reponse is an error? 
			console.log(`loadCachedTree received, ${response_json.seconds_since_last_update} seconds out of date:`)
			if (response_json.seconds_since_last_update > 3600) {
				console.log("cache more than 1 hr out of date. Fetching new sample tree")
				this.updateRemoteTree()
			}

			// console.log(response_json)
		},
		async updateRemoteTree() {
			this.isLoadingRemoteTree = true
			await fetchRemoteTree()
			this.isLoadingRemoteTree = false
		},
		async loadSelectedRemoteFiles() {
			this.isLoadingRemoteFiles = true;
			var promises = []
			for (let i = 0; i < this.selectedRemoteFiles.length; i++) {
				console.log("processing load from remote server for entry")
				console.log(this.selectedRemoteFiles[i])
				promises.push(addRemoteFileToSample(this.selectedRemoteFiles[i], this.sample_id))
			}
			await Promise.all(promises)
			this.isLoadingRemoteFiles = false;
		}
	},	
	computed: {
		sample_data() {
			// console.log("hello, here is the sample data", this.$store.state.all_sample_data)
			return this.$store.state.all_sample_data[this.sample_id] || {}
		},
		blocks() {
			return this.sample_data.blocks_obj;
		},
		savedStatus() {
			return this.$store.state.saved_status[this.sample_id];
		},
		lastModified() {
			// if (!this.sample_data.last_modified) { return "" }
			const save_date = new Date(this.sample_data.last_modified);
			// const today = new Date()
			// check if today:
			// if (save_date.toDateString() == today.toDateString()) {
			// 	return "today"
			// }
			return save_date.toLocaleTimeString("en-GB", {hour: '2-digit', minute:'2-digit'})
		},
		files() {
			return this.sample_data.files
		},
		file_ids() {
			return this.sample_data.file_ObjectIds
		},
		stored_files() {
			return this.$store.state.files
		},
		loadFilesButtonValue() {
			const len = this.selectedRemoteFiles.length
			if (len == 1) { return "Load 1 file" }
			if (len > 1) { return `Load ${len} files`}
			return "Load files" 
		},
		SampleDescription: createComputedSetterForSampleField("description"),
		Name: createComputedSetterForSampleField("name"),
		ChemForm: createComputedSetterForSampleField("chemform"),
		DateCreated: createComputedSetterForSampleField("date"),
	},
	created() {
		this.getSampleData();
	},
	components: {
		DataBlockBase,
		ImageBlock,
		FileSelectDropdown,
		TinyMceInline, 
		Modal,
		SelectableFileTree
	},
	mounted() {
		// overwrite ctrl-s and cmd-s to save the page
		this._keyListener = function(e) {
			if (e.key === "s" && (e.ctrlKey || e.metaKey)) {	
				e.preventDefault(); // present "Save Page" from getting triggered.
				this.saveSample();
			}
		};
		document.addEventListener('keydown', this._keyListener.bind(this));

		// Retreive the cached file tree
		this.loadCachedTree()
		// this.updateRemoteTree()

		// setup the uppy instsance
		setupUppy(this.sample_id, '#uppy-trigger', this.stored_files)
	},
	beforeUnmount() {
		document.removeEventListener('keydown', this._keyListener);
	}
}
</script>


<style scoped>



.editor-navbar {
  margin-bottom: 1rem;
  z-index: 900;
}

.nav-link {
  cursor: pointer; 
}

.nav-link:hover {
  background-color: black;
  color: white;
}

.navbar-icon {
	width: 2.5rem ;
	height:2.5rem;
  /*padding: 0.3rem;*/
}

.unsaved-warning {
	font-weight: 600;
	color: #ffc845;
}


/* file block styles */
#filearea {
  max-height: 14rem;
  padding: 0.9rem 1.25rem;
}

#uppy-trigger {
  scroll-anchor: auto;
  width: 8rem;
}

.file-group {
  padding: 0.25rem 0rem;
}

.filelink {
  color: #004175;
}

.filelink:hover {
  text-decoration: none;
}

.link-icon {
	margin-left: 0.4rem;
	color: #888;
	font-size: small;
}

.delete-file-button {
  padding-right: 0.5rem;
  color: gray;
  cursor: pointer;
}

label, h6 {
	color: #006699;
	font-weight: 600;
	font-size: smaller;
}

/* Table of contents links */
.contents-item {
	cursor: pointer;
}

.contents-blocktype {
	font-style: italic;
	color: gray;
	margin-right: 1rem;
}

.contents-blocktitle {
	color: #004175;
}

#contents-ol {
	margin-bottom: 0rem;
	padding-left: 1rem;
}

.navbar-brand {
	cursor: pointer;
}

.modal-enclosure >>> .modal-header {
	padding: 0.5rem 1rem;
}

.modal-enclosure >>> .modal-dialog {
	max-width: 95%;
	min-height: 95vh;
	margin-top: 2.5vh;
	margin-bottom: 2.5vh;
}

.modal-enclosure >>> .modal-content {
	height: 95vh;
	/*overflow: scroll;*/
}


</style>

