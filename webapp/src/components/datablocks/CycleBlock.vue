<template>
	<DataBlockBase :sample_id="sample_id" :block_id="block_id">
		<div class="form-row col-lg-8">
			<FileSelectDropdown
				v-model="file_id"
				:sample_id="sample_id" 
				:block_id="block_id"
				:extensions='[".mpr", ".txt", ".xls", ".xlsx", ".txt", ".res"]'
				updateBlockOnChange
			/>
		</div>
		<div class="form-row col-md-4 col-lg-5 mt-2">
			<div class="input-group form-inline">
				<label class="mr-2"><b>Cycle number:</b></label>
				<input type="text" class="form-control" 
				v-model="cycle_number" 
				@keydown.enter="updateBlock"
				@blur="updateBlock">
			</div>
		<div v-if="cycle_num_error" class="alert alert-warning">{{ cycle_num_error }}</div>
		<!-- Insert another div here, if the filled value is a string or something -->
		</div>
		<div class="row">
			<div class="col-xl-8 col-lg-9 col-md-11 mx-auto">
				<BokehPlot :bokehPlotData="bokehPlotData" />
				<!-- <div v-if="!bokehPlotData" class="alert alert-danger">No bokeh Plot Data is loaded</div> -->
			</div>
		</div>
	</DataBlockBase>
</template>



<script>

import DataBlockBase from "@/components/datablocks/DataBlockBase"
import FileSelectDropdown from "@/components/FileSelectDropdown"
import BokehPlot from "@/components/BokehPlot"

import {updateBlockFromServer} from "@/server_fetch_utils.js"
import {createComputedSetterForBlockField} from "@/field_utils.js"

export default {
	data() {
		return {
			cycle_num_error: "",
			
		}
	},
	props: {
		sample_id: String,
		block_id: String,
	},
	computed: {
		bokehPlotData() {
			return this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id].bokeh_plot_data
		},
		numberOfCycles() {
			return this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id].number_of_cycles
		},
		file_id: createComputedSetterForBlockField("file_id"),
		cycle_number: createComputedSetterForBlockField("cyclenumber"),
		
	},
	methods: {
		
		updateBlock() {
			// if (this.bruh = True) {
			// 	this.cycle_num_error = ""
			// 	updateBlockFromServer(this.sample_id, this.block_id, 
			// 		this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
			// } 
	
			// else {
			// 	this.cycle_num_error="Please enter a number!"
			// }

			this.cycle_num_error = ""
			updateBlockFromServer(this.sample_id, this.block_id, 
			this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
				

			


		}

	},
	components: {
		DataBlockBase,
		FileSelectDropdown,
		BokehPlot
	},	
}
</script>