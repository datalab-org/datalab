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
      <div class="form-inline">
        <div class="form-group mb-2">
          <label class="mr-2"><b>NMR folder name</b></label>
          <input
            v-model="nmr_folder_name"
            type="text"
            class="form-control mr-2"
            @keydown.enter="validateFolderNames()"
            @blur="validateFolderNames()"
          />
          <label class="mr-2"><b>Echem folder name</b></label>
          <input
            v-model="echem_folder_name"
            type="text"
            class="form-control"
            @keydown.enter="validateFolderNames()"
            @blur="validateFolderNames()"
          />
          <div v-if="folderNameError" class="alert alert-danger mt-2 mx-auto">
            {{ folderNameError }}
          </div>
        </div>
        <div class="form-group mt-2 mb-2">
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
    <div v-show="nmr_folder_name && echem_folder_name" class="row mt-2">
      <div id="bokehPlotContainer" class="col-xl-8 col-lg-8 col-md-11 mx-auto">
        <BokehPlot :bokeh-plot-data="bokehPlotData" />
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
      folderNameError: "",
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["insitu"];
    },
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    ppm1: createComputedSetterForBlockField("ppm1"),
    ppm2: createComputedSetterForBlockField("ppm2"),
    nmr_folder_name: createComputedSetterForBlockField("nmr_folder_name"),
    echem_folder_name: createComputedSetterForBlockField("echem_folder_name"),
    file_id: createComputedSetterForBlockField("file_id"),
    folder_name: createComputedSetterForBlockField("folder_name"),
  },
  methods: {
    parsePPM() {
      if (isNaN(parseFloat(this.ppm1)) || isNaN(parseFloat(this.ppm2))) {
        this.ppmParseError = "Please provide a valid number";
      } else {
        this.ppmParseError = "";
      }
    },
    validateFolderNames() {
      if (!this.nmr_folder_name || !this.echem_folder_name) {
        this.folderNameError = "Both NMR and Echem folder names are required";
        return false;
      }
      this.folderNameError = "";
      this.updateBlock();
      return true;
    },
    updateBlock() {
      const foundFile = this.all_files.find((file) => file.immutable_id === this.file_id);
      this.folder_name = foundFile?.name || "Folder not found";
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
