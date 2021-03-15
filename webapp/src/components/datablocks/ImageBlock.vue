<template>
	<DataBlockBase :sample_id="sample_id" :block_id="block_id"> 
		<FileSelectDropdown v-model="file_id"
			:sample_id="sample_id" 
			:block_id="block_id"
			:extensions='[".png", ".jpg", ".jpeg"]'
		/>
		<div class="col-xl-6 col-lg-7 col-md-10 mx-auto">
			<img v-if="file_id" :src="image_url" class="img-fluid"> 
		</div>
	</DataBlockBase>
</template>


<script>

import DataBlockBase from "@/components/datablocks/DataBlockBase"
import FileSelectDropdown from "@/components/FileSelectDropdown"
import {createComputedSetterForBlockField} from "@/field_utils.js"

export default {
	props: {
		sample_id: String,
		block_id: String,
	},
	computed: {
		file_id:  createComputedSetterForBlockField("file_id"),
		image_url() {
			// return ''
			console.log("trying to get image_url for file_id:")
			console.log(this.file_id)
			return `http://localhost:5001/${this.$store.state.files[this.file_id].url_path}`
		}
	},	
	components: {
		DataBlockBase,
		FileSelectDropdown
	}
}
</script>