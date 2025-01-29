<template>
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
          <label class="mr-2"><b>ppm 1</b></label>
          <input
            v-model.number="ppm1"
            type="number"
            class="form-control mr-2"
            @keydown.enter="
              parsePPM();
              updateBlock();
            "
            @blur="
              parsePPM();
              updateBlock();
            "
          />
          <label class="mr-2"><b>ppm 2</b></label>
          <input
            v-model.number="ppm2"
            type="number"
            class="form-control"
            @keydown.enter="
              parsePPM();
              updateBlock();
            "
            @blur="
              parsePPM();
              updateBlock();
            "
          />
          <button @click="print">Print</button>
          <div v-if="ppmParseError" class="alert alert-danger mt-2 mx-auto">
            {{ ppmParseError }}
          </div>
        </div>
      </div>
    </div>
    <div class="row mt-2">
      <!-- <div class="col-6 pr-2">
        <BokehPlot :key="'bokeh_plot1'" :bokeh-plot-data="bokehPlotData1" />
      </div>
      <div class="col-6 pl-2">
        <div class="mb-2">
          <button v-show="file_id" class="btn btn-secondary" @click="togglePlot">
            Switch to {{ showPlot2 ? "echem" : "fitting" }}
          </button>
        </div>
        <BokehPlot v-if="showPlot2" :key="'bokeh_plot2'" :bokeh-plot-data="bokehPlotData2" />
        <BokehPlot v-else :key="'bokeh_plot3'" :bokeh-plot-data="bokehPlotData3" />
      </div> -->
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData5" />
      </div>
    </div>
    <div class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData4" />
      </div>
    </div>
    <div class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData6" />
      </div>
    </div>
    <div class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData1" />
      </div>
    </div>
    <div class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData2" />
      </div>
    </div>
    <div class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData3" />
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
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
      ppmParseError: "",
      showPlot2: true,
    };
  },
  computed: {
    bokehPlotData1() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_1;
    },
    bokehPlotData2() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_2;
    },
    bokehPlotData3() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_3;
    },
    bokehPlotData4() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_4;
    },
    bokehPlotData5() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_5;
    },
    bokehPlotData6() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data_6;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["insitu"];
    },
    ppm1: createComputedSetterForBlockField("ppm1"),
    ppm2: createComputedSetterForBlockField("ppm2"),
    file_id: createComputedSetterForBlockField("file_id"),
  },
  methods: {
    parsePPM() {
      if (isNaN(parseFloat(this.ppm1)) || isNaN(parseFloat(this.ppm2))) {
        this.ppmParseError = "Please provide a valid number";
      } else {
        this.ppmParseError = "";
      }
    },
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
    togglePlot() {
      this.showPlot2 = !this.showPlot2;
    },
    print() {
      console.log("#%$#$%#$%#%$%#$$%#%$#%$#");
      console.log(this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]);
      console.log("#%$#$%#$%#%$%#$$%#%$#%$#");
    },
  },
};
</script>

<style scoped></style>
