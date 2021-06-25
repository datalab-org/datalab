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
				@keydown.enter="updateBlock2"
				@blur="updateBlock2">
			</div>
			<input type="button"  value="Plot!" @click="updateBlock2">
			<input type="button" value="dq/dv analysis!" @click="modeselect">
		<div v-if="cycle_num_error" class="alert alert-warning">{{ cycle_num_error }}</div>
		<!-- Insert another div here, if the filled value is a string or something -->
		</div>
		<div class="slider-block">
			<div class="slider">
				<input type="range" v-model="p_spline"  id="p_spline" name="p_spline" min="1" max="5">
				<label for="volume">Polynomial Spline: {{p_spline }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="s_spline" id="s_spline" name="s_spline" min="2" max="10">
				<label for="volume">-ve log Spline fit: {{- s_spline }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="polyorder1" id="polyorder1" name="polyorder1" min="1" max="7">
				<label for="volume">Polynomial order 1: {{ polyorder1 }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="polyorder2" id="polyorder2" name="polyorder2" min="1" max="7">
				<label for="volume">Polynomial order 2: {{ polyorder1 }}</label>
			</div>
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
			cycle_number: "",
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
		all_cycles: createComputedSetterForBlockField("cyclenumber"),
		p_spline: createComputedSetterForBlockField("p_spline"),
		s_spline: createComputedSetterForBlockField("s_spline"),
		polyorder1: createComputedSetterForBlockField("polyorder1"),
		polyorder2: createComputedSetterForBlockField("polyorder2"),
		mode: createComputedSetterForBlockField("plotmode"),
		
		
	},
	methods: {
		parseCycleNumber(cycle_number) {
			let cycle_string = cycle_number.replace(/\s/g, '')
			var cycle_regex = /^(\d+(-\d+)?,)*(\d+(-\d+)?)$/g
			if (cycle_number.match(/^ *$/) !== null){
				this.cycle_num_error = "Plotting all cycles!"
				return false
			}
			else if (!cycle_regex.test(cycle_string)) {
				this.cycle_num_error = "Please enter a valid input!"
				return false
			}
			let cycle_string_sections = cycle_string.split(',')
			var all_cycles = []
			for (const section of cycle_string_sections) {
				let split_section = section.split('-')
				if (split_section.length == 1) {
					all_cycles.push(parseInt(split_section[0]))
				} else {
					let upper_range = parseInt(split_section[1])
					let lower_range = parseInt(split_section[0])
					for (let j = Math.min(lower_range, upper_range); j <= Math.max(lower_range, upper_range); j++) {
						all_cycles.push(j)
					}
				}
			}
			
			return all_cycles
		},
		updateBlock2() {
			this.all_cycles = this.parseCycleNumber(this.cycle_number)
			if (!this.all_cycles) {
				return
			}
			console.log('parsing')
			this.cycle_num_error = this.all_cycles
			updateBlockFromServer(this.sample_id, this.block_id, 
				this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
		},
		updateBlock() {
			// if (this.bruh = True) {
			// 	this.cycle_num_error = ""
			// 	updateBlockFromServer(this.sample_id, this.block_id, 
			// 		this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
			// } 
	
			// else {
			// 	this.cycle_num_error="Please enter a number!"
			// }
			var regex = /[a-zA-Z!@#$%^&*)(+=._]+$/g
			var regex2 = /^[a-zA-Z!@#$%^&*)(+=._]+$/g
			var regex3 = /[,-]{2,}/g
			var regex4 = /[,\s-]{3,}/g
			//var regex = /^[\d\-\s]*$/g
			//var regex = /[0-9\-\s]*/g
			//var cycle_regex = /^(\d+(\-\d+)?,)*(\d+(\-\d+)?)$/g
			
			if (regex2.test(this.cycle_number)) {
				this.cycle_num_error="Please enter a valid input!"	
			} else if ( regex.test(this.cycle_number)){
				this.cycle_num_error="Please enter a valid input!"
			} else if (regex3.test(this.cycle_number)){
					this.cycle_num_error="Please enter a valid input!"
			}
			else if (regex4.test(this.cycle_number)){
					this.cycle_num_error="Please enter a valid input!"
			}
	
			else {
				this.cycle_num_error = ""
				updateBlockFromServer(this.sample_id, this.block_id, 
					this.$store.state.all_sample_data[this.sample_id]["blocks_obj"][this.block_id])
				
			}

		},
		modeselect(){
			//Default value for dqdv mode is False, following lines reverses boolean and shows/removes the dqdv slider section accordingly
			this.mode = !(this.mode)
			console.log(this.mode)
			if (this.mode){
				document.getElementsByClassName("slider-block")[0].style.display = "block"
			}else{
				document.getElementsByClassName("slider-block")[0].style.display = "none"
			}
		}

	},
	components: {
		DataBlockBase,
		FileSelectDropdown,
		BokehPlot,
	},	
}
</script>

<style scoped>
.slider {
	display: inline-block;
	width: 25%;
}

.slider-block{
	margin-top: 20px;
	margin-bottom: 20px;
	display: none;

}
</style>