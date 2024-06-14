<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      updateBlockOnChange
    />
    <div v-show="file_id">
      <div class="form-inline mt-2">
        <div class="form-group">
          <label class="mr-2"><b>Process number:</b></label>
          <select class="form-control" v-model="selected_process" @change="updateBlock">
            <option v-for="process_number in block.available_processes" :key="process_number">
              {{ process_number }}
            </option>
          </select>
        </div>
      </div>

      <div class="mt-4">
        <span class="mr-2">
          <Isotope :isotopeString="block.nucleus" /> {{ block.pulse_program_name }}
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
          {{ block.topspin_title }}
        </div>
      </div>
      <div class="row">
        <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
          <BokehPlot v-if="bokehPlotData" :bokehPlotData="bokehPlotData" />
          <div v-else class="alert alert-secondary">
            Plotting currently not available for data with dimension > 1
          </div>
        </div>
        <div v-if="detailsShown" class="col-xl-4 col-lg-4 ml-0">
          <table class="table table-sm">
            <tbody>
              <tr>
                <th scope="row">nucleus</th>
                <td><Isotope :isotopeString="block.nucleus" /></td>
              </tr>
              <tr>
                <th scope="row">pulse program</th>
                <td>{{ block.pulse_program_name }}</td>
              </tr>
              <tr>
                <th scope="row">Data shape</th>
                <td>
                  {{ block.processed_data_shape }} (<i>d</i> =
                  {{ block.processed_data_shape.length }})
                </td>
              </tr>
              <tr>
                <th scope="row">probe</th>
                <td>{{ block.probe_name }} s</td>
              </tr>

              <tr>
                <th scope="row"># of scans</th>
                <td>{{ block.nscans }}</td>
              </tr>

              <tr>
                <th scope="row">recycle delay</th>
                <td>{{ block.recycle_delay }} s</td>
              </tr>
              <tr>
                <th scope="row">carrier frequency</th>
                <td>{{ block.carrier_frequency_MHz }} MHz</td>
              </tr>

              <tr>
                <th scope="row">carrier offset</th>
                <td>
                  {{ (block.carrier_offset_Hz / block.carrier_frequency_MHz).toFixed(1) }} ppm
                </td>
              </tr>
              <tr>
                <th scope="row">cnst31</th>
                <td>{{ block.CNST31 }}</td>
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
  data() {
    return {
      wavelengthParseError: "",
      detailsShown: false,
      titleShown: false,
    };
  },
  props: {
    item_id: String,
    block_id: String,
  },
  computed: {
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
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
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    Isotope,
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
