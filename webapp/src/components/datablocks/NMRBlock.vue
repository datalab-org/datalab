<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      update-block-on-change
    />
    <div v-show="file_id">
      <div class="form-inline mt-2">
        <div class="form-group">
          <label class="mr-2"><b>Process number:</b></label>
          <select v-model="selected_process" class="form-control" @change="updateBlock">
            <option v-for="process_number in block.available_processes" :key="process_number">
              {{ process_number }}
            </option>
          </select>
        </div>
      </div>

      <div class="mt-4">
        <span class="mr-2">
          <Isotope :isotope-string="metadata?.nucleus" /> {{ metadata?.pulse_program_name }}
        </span>
        <a type="button" class="btn btn-default btn-sm mb-2" @click="titleShown = !titleShown">{{
          titleShown ? "hide title" : "show title"
        }}</a>
        <a
          type="button"
          class="btn btn-default btn-sm mb-2 ml-2"
          @click="detailsShown = !detailsShown"
          >{{ detailsShown ? "hide measurement details" : "show measurement details" }}</a
        >
      </div>
      <div v-if="titleShown" class="card mb-2">
        <div class="card-body" style="white-space: pre">
          {{ metadata?.topspin_title }}
        </div>
      </div>
      <div class="row">
        <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
          <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
        </div>
        <div v-if="detailsShown" class="col-xl-4 col-lg-4 ml-0">
          <table class="table table-sm">
            <tbody>
              <tr>
                <th scope="row">nucleus</th>
                <td><Isotope :isotope-string="metadata?.nucleus" /></td>
              </tr>
              <tr>
                <th scope="row">pulse program</th>
                <td>{{ metadata?.pulse_program_name }}</td>
              </tr>
              <tr>
                <th scope="row">Data shape</th>
                <td>
                  {{ metadata?.processed_data_shape }} (<i>d</i> =
                  {{ metadata?.processed_data_shape.length }})
                </td>
              </tr>
              <tr>
                <th scope="row">probe</th>
                <td>{{ metadata?.probe_name }} s</td>
              </tr>

              <tr>
                <th scope="row"># of scans</th>
                <td>{{ metadata?.nscans }}</td>
              </tr>

	      <tr v-if="metadata?.relaxation_delay" >
		<th scope="row">relaxation delay</th>
		<td>{{metadata?.relaxation_delay }} s</td>
	      </tr>


              <tr v-if="metadata?.recycle_delay || !metadata?.relaxation_delay">
                <th scope="row">recycle delay</th>
                <td>{{ metadata?.recycle_delay }} s</td>
              </tr>
              <tr>
                <th scope="row">carrier frequency</th>
                <td>{{ metadata?.carrier_frequency_MHz.toPrecision(4) }} MHz</td>
              </tr>

	      <tr v-if="metadata?.carrier_offset_ppm">
		<th scope="row">carrier offset</th>
		<td>
		{{ metadata?.carrier_offset_ppm }}
		ppm
		</td>
	      </tr>

              <tr v-else>
                <th scope="row">carrier offset</th>
                <td>
                  {{ (metadata?.carrier_offset_Hz / metadata?.carrier_frequency_MHz).toFixed(1) }}
                  ppm
                </td>
              </tr>
              
	      <tr v-if="metadata?.spectral_window_Hz">
		<th scope="row">spectral window</th>
		<td>
		{{ metadata?.spectral_window_Hz.toFixed(1) }}
		Hz
		</td>
	      </tr>
	      <tr>
                <th scope="row">cnst31</th>
                <td>{{ metadata?.CNST31 }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import Isotope from "@/components/Isotope";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    Isotope,
  },
  props: {
    item_id: {
      type: String,
      required: true,
    },
    block_id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      wavelengthParseError: "",
      detailsShown: true,
      titleShown: false,
    };
  },
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    metadata() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]?.metadata;
    },
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["nmr"];
    },
    file_id: createComputedSetterForBlockField("file_id"),
    selected_process: createComputedSetterForBlockField("selected_process"),
  },
  methods: {
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
  },
};
</script>

<style scoped>
.attribute-label {
  color: grey;
}

th {
  color: #454545;
  font-weight: 500;
}
</style>
