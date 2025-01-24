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
          <div v-if="ppmParseError" class="alert alert-danger mt-2 mx-auto">
            {{ ppmParseError }}
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-6 pr-2">
        <BokehPlot :key="'bokeh_plot1'" :bokeh-plot-data="bokehPlotData1" />
      </div>
      <div class="col-6 pl-2">
        <BokehPlot :key="'bokeh_plot2'" :bokeh-plot-data="bokehPlotData2" />
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
  },
};
</script>

<style scoped></style>
