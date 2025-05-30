<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <div class="form-row">
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        :default-to-all-files="true"
        update-block-on-change
      />
    </div>

    <div class="form-row col-md-6 col-lg-4 mt-2 mb-2 pl-0">
      <div class="input-group form-inline">
        <label class="mr-2"><b>Wavelength (Å):</b></label>
        <input
          v-model="wavelength"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': wavelengthParseError }"
          @keydown.enter="
            parseWavelength();
            updateBlock();
          "
          @blur="
            parseWavelength();
            updateBlock();
          "
        />
        <div v-if="wavelengthParseError" class="alert alert-danger mt-2 mx-auto">
          {{ wavelengthParseError }}
        </div>
      </div>

      <div class="row">
        <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
          <BokehPlot :bokeh-plot-data="bokehPlotData" />
        </div>
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
      wavelengthParseError: "",
    };
  },
  computed: {
    bokehPlotData() {
      return this.block.bokeh_plot_data;
    },
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos["xrd"];
    },
    wavelength: createComputedSetterForBlockField("wavelength"),
    file_id: createComputedSetterForBlockField("file_id"),
  },
  methods: {
    parseWavelength() {
      if (isNaN(this.wavelength) || isNaN(parseFloat(this.wavelength))) {
        this.wavelengthParseError = "Please provide a valid number";
      } else {
        this.wavelengthParseError = "";
      }
    },
    updateBlock() {
      updateBlockFromServer(this.item_id, this.block_id, this.block);
    },
  },
};
</script>
