<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <template #controls>
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
        <div class="form-inline mt-2">
          <div class="form-group">
            <label class="mr-2"><b>Experiment:</b></label>
            <select v-model="selected_experiment" class="form-control" @change="updateBlock">
              <option v-for="experiment in block.available_experiments" :key="experiment">
                {{ experiment }}
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
        </div>
        <div v-if="titleShown" class="card mb-2">
          <div class="card-body" style="white-space: pre">
            {{ metadata?.topspin_title }}
          </div>
        </div>
      </div>
    </template>

    <template #plot>
      <div v-show="file_id" id="bokehPlotContainer">
        <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
      </div>
    </template>

    <template #metadata="{ metadata: blockMetadata }">
      <table class="table table-sm">
        <tbody>
          <tr>
            <th scope="row">nucleus</th>
            <td><Isotope :isotope-string="blockMetadata?.nucleus" /></td>
          </tr>
          <tr>
            <th scope="row">pulse program</th>
            <td>{{ blockMetadata?.pulse_program_name }}</td>
          </tr>
          <tr>
            <th scope="row">Data shape</th>
            <td>
              {{ blockMetadata?.processed_data_shape }} (<i>d</i> =
              {{ blockMetadata?.processed_data_shape.length }})
            </td>
          </tr>
          <tr>
            <th scope="row">probe</th>
            <td>{{ blockMetadata?.probe_name }} s</td>
          </tr>

          <tr>
            <th scope="row"># of scans</th>
            <td>{{ blockMetadata?.nscans }}</td>
          </tr>

          <tr>
            <th scope="row">recycle delay</th>
            <td>{{ blockMetadata?.recycle_delay }} s</td>
          </tr>

          <tr>
            <th scope="row">carrier frequency</th>
            <td>{{ blockMetadata?.carrier_frequency_MHz.toPrecision(4) }} MHz</td>
          </tr>

          <tr v-if="blockMetadata?.carrier_offset_ppm">
            <th scope="row">carrier offset</th>
            <td>
              {{ blockMetadata?.carrier_offset_ppm }}
              ppm
            </td>
          </tr>

          <tr v-else>
            <th scope="row">carrier offset</th>
            <td>
              {{
                (blockMetadata?.carrier_offset_Hz / blockMetadata?.carrier_frequency_MHz).toFixed(1)
              }}
              ppm
            </td>
          </tr>

          <tr v-if="blockMetadata?.spectral_window_Hz">
            <th scope="row">spectral window</th>
            <td>
              {{ blockMetadata?.spectral_window_Hz.toFixed(1) }}
              Hz
            </td>
          </tr>
          <tr>
            <th scope="row">cnst31</th>
            <td>{{ blockMetadata?.CNST31 }}</td>
          </tr>
        </tbody>
      </table>
    </template>
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
    selected_experiment: createComputedSetterForBlockField("selected_experiment"),
  },
  methods: {
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      ).catch((error) => {
        console.error("Error updating block:", error);
      });
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
