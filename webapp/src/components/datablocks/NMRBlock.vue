<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="['.zip']"
      updateBlockOnChange
    />

    <div class="form-row">
      <div class="col-lg-2 mt-2 mb-2 pl-1">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Nucleus:</b></label>
          <Isotope :isotopeString="nucleus" />
        </div>
      </div>
      <div class="col-lg-4 mt-2 mb-2 pl-1">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Probe:</b></label>
          {{ probe_name }}
        </div>
      </div>

      <div class="col-lg-2 mt-2 mb-2 pl-1">
        <div class="input-group form-inline">
          <label class="mr-2"><b>Recycle delay:</b></label>
          {{ recycle_delay }} s
        </div>
      </div>

      <div class="col-lg-2 mt-2 mb-2 pl-1">
        <div class="input-group form-inline">
          <label class="mr-2"><b># of scans:</b></label>
          {{ nscans }}
        </div>
      </div>
    </div>

    <div class="row">
      <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
        <BokehPlot :bokehPlotData="bokehPlotData" />
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
export default {
  data() {
    return {
      wavelengthParseError: "",
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
    nucleus() {
      return this.block.nucleus;
    },
    probe_name() {
      return this.block.probe_name;
    },
    recycle_delay() {
      return this.block.recycle_delay;
    },
    nscans() {
      return this.block.nscans;
    },
    file_id: createComputedSetterForBlockField("file_id"),
  },
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    Isotope,
  },
  // methods: {
  //   updateBlock() {
  //     updateBlockFromServer(
  //       this.item_id,
  //       this.block_id,
  //       this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
  //     );
  //   },
  // },
  // mounted() {
  // 	this.makeBokehPlot()
  // }
};
</script>

<style scoped></style>
