<template>
	<DataBlockBase :sample_id="sample_id" :block_id="block_id"> 
		<FileSelectDropdown v-model="filename"
			:sample_id="sample_id" 
			:block_id="block_id"
			:extensions='[".png", ".jpg", ".jpeg"]'
		/>
		<div class="col-xl-6 col-lg-7 col-md-10 mx-auto">
			<img v-if="filename" :src="image_url" class="img-fluid"> 
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
		filename:  createComputedSetterForBlockField("filename"),
		image_url() {
			return `http://localhost:5001/files/${this.sample_id}/${this.filename.replace(" ","_")}`
		}
	},
	components: {
		DataBlockBase,
		FileSelectDropdown
	}
}
</script>