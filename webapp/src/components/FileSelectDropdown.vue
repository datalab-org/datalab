<template>
	<div class="input-group form-inline">
		<label class="mr-4"><b>Select a file:</b></label>
		<select class="form-control"
			:value="modelValue"
			@input="handleInput">

			<option v-for="filename in available_filenames" :key="filename">
				{{ filename	}}
			</option>

		</select>
	</div>
</template>

<script>

import {updateBlockFromServer} from "@/server_fetch_utils.js"

export default {
	props: {
		modelValue: String,
		sample_id: String,
		block_id: String, 
		extensions: {
			type: Array, // array of strings, file extensions
			default: () => [""], // show all files
		},
		updateBlockOnChange: {
			type: Boolean,
			default: false
		},
	},
	computed: {
		available_filenames() {
			let all_files =  this.$store.state.all_sample_data[this.sample_id].files
			return all_files.filter(file => {
				return this.extensions.map(extension => file.endsWith(extension)).some(element => element) // check if any elements are true
			});
		},
	},
	methods: {
		handleInput(event) {
			this.$emit('update:modelValue', event.target.value);
			if ( this.updateBlockOnChange ) {
				updateBlockFromServer(this.sample_id, this.block_id, 
					this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
			}

		}
	}
}

</script>