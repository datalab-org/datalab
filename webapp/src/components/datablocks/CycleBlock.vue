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
			
		<div v-if="cycle_num_error" class="alert alert-warning">{{ cycle_num_error }}</div>
		<!-- Insert another div here, if the filled value is a string or something -->
		</div>
		<div class="button-box">
				<input type="button"  class="btn btn-dark" value="Plot!" @click="updateBlock2" >
				<input type="button" class="btn btn-dark" id='norm' value="Normal analysis!" @click="normal_modeselect(); color_select()">
				<input type="button" class="btn btn-dark"  id ='dqdv' value="dq/dv analysis!" @click="dqdv_modeselect(); color_select() ">
				<input type="button" class="btn btn-dark"  id='dvdq' value="dV/dq analysis!" @click="dvdq_modeselect(); color_select()">
		</div>
		<div class="slider-block">
			<div class="slider">
				<input type="range" v-model="p_spline"  id="p_spline" name="p_spline" min="3" max="9"  step="2">
				<label for="volume">Polynomial Spline: {{p_spline }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="s_spline" id="s_spline" name="s_spline" min="3" max="10" step="0.2">
				<label for="volume">-ve log Spline fit: {{- s_spline }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="win_size_1" id="win_size_1" name="win_size_1" min="501" max="1501">
				<label for="volume">Window Size 1: {{ win_size_1 }}</label>
			</div>
			<div class="slider">
				<input type="range" v-model="win_size_2" id="win_size_2" name="win_size_2" min="51" max="151">
				<label for="volume">Window Size 2: {{ win_size_2 }}</label>
			</div>
		</div>

		<div class="row" id='plotarea'>
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
		win_size_1: createComputedSetterForBlockField("win_size_1"),
		win_size_2: createComputedSetterForBlockField("win_size_2"),
		dqdv_mode: createComputedSetterForBlockField("plotmode-dqdv"),
		dvdq_mode: createComputedSetterForBlockField("plotmode-dvdq"),
		
		
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
			// if (!this.all_cycles) {
			// 	return
			// }
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
		dqdv_modeselect(){
			
			
			//Default value for dqdv mode is False, following lines reverses boolean and shows/removes the dqdv slider section accordingly
			this.dqdv_mode = !(this.dqdv_mode)

			//if dqdv mode is activated, then dvdq mode HAS to be false
			if (this.dqdv_mode && this.dvdq_mode){       // When calling the dqdv button, we know user wants dqdv. If both dqdv and dvdq are true, set dvdq to false
				this.dvdq_mode = !(this.dvdq_mode)
			}

			console.log(this.dvdq_mode)
			console.log(this.dqdv_mode)
			if (this.dqdv_mode){
				document.getElementsByClassName("slider-block")[0].style.display = "block"
			}else{
				document.getElementsByClassName("slider-block")[0].style.display = "none"
			}


			
		},
		dvdq_modeselect(){
			//Default value for dqdv mode is False, following lines reverses boolean and shows/removes the dqdv slider section accordingly
			this.dvdq_mode = !(this.dvdq_mode)

			//if dqdv mode is activated, then dvdq mode HAS to be false
			if (this.dvdq_mode && this.dqdv_mode){
				this.dqdv_mode = !(this.dqdv_mode)
			}
			console.log(this.dvdq_mode)
			console.log(this.dqdv_mode)
			if (this.dvdq_mode){
				document.getElementsByClassName("slider-block")[0].style.display = "block"
			}else{
				document.getElementsByClassName("slider-block")[0].style.display = "none"
			}
		},
		normal_modeselect(){
			
			if (this.dqdv_mode){
				this.dqdv_mode = !(this.dqdv_mode)
			}
			if (this.dvdq_mode){
				this.dvdq_mode = !(this.dvdq_mode)
			}
			console.log(this.dvdq_mode)
			console.log(this.dqdv_mode)
		
			document.getElementsByClassName("slider-block")[0].style.display = "none"
			
		},
		color_select(){
			var dqdv = document.getElementById('dqdv');
			var dvdq = document.getElementById('dvdq');
			var norm = document.getElementById('norm');

			if (this.dqdv_mode){
				
				dqdv.style.color = 'green';
				dvdq.style.color = 'white';
				norm.style.color = 'white';
			} 
			else if (this.dvdq_mode){
				
				dqdv.style.color = 'white';
				dvdq.style.color = 'green';
				norm.style.color = 'white';
			} 
			else {
				
				dqdv.style.color = 'white';
				dvdq.style.color = 'white';
				norm.style.color = 'green';
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

.button-box {
	display: block;
	width: 100%;
	margin: 10px 0 10px 0;
	
}


.button-box input{
	margin-right: 10px;
}
.slider {
	display: inline-block;
	width: 25%;
}

.slider label{
	display: block;
}

.slider-block{
	margin-top: 20px;
	margin-bottom: 20px;
	display: none;

}
.mx-auto {
	margin-left: 0 !important;
	margin-right: 0 !important;
	max-width: 100%;
}

#plotarea {
	max-width: 100% !important;
	display: block !important;
}
</style>