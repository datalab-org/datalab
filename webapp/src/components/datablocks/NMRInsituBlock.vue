<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      update-block-on-change
      @change="onFileChange"
    />
    <div v-show="file_id">
      <div class="form-inline">
        <div class="form-group mb-2">
          <label class="mr-2"><b>NMR folder name</b></label>
          <v-select
            v-model="nmr_folder_name"
            :options="availableFolders"
            :reduce="(folder) => folder"
            class="folder-select mr-2"
            placeholder="Select a folder"
            @update:model-value="onFolderSelected"
          />
          <label class="mr-2"><b>Echem folder name</b></label>
          <v-select
            v-model="echem_folder_name"
            :options="availableFolders"
            :reduce="(folder) => folder"
            class="folder-select"
            placeholder="Select a folder"
            @update:model-value="onFolderSelected"
          />
          <div v-if="folderNameError" class="alert alert-danger mt-2 mx-auto">
            {{ folderNameError }}
          </div>
        </div>
        <div class="form-group mt-2 mb-2">
          <label class="mr-2"><b>Lower PPM range</b></label>
          <input
            v-model.number="ppm1"
            type="number"
            class="form-control mr-2"
            @keydown.enter="handlePPMUpdate"
            @blur="handlePPMUpdate"
          />
          <label class="mr-2"><b>Upper PPM range</b></label>
          <input
            v-model.number="ppm2"
            type="number"
            class="form-control"
            @keydown.enter="handlePPMUpdate"
            @blur="handlePPMUpdate"
          />
          <div v-if="ppmParseError" class="alert alert-danger mt-2 mx-auto">
            {{ ppmParseError }}
          </div>
        </div>
      </div>
    </div>
    <div
      v-show="nmr_folder_name && echem_folder_name"
      class="row mt-2 text-center justify-content-center"
    >
      <div
        id="bokehPlotContainer"
        class="col-xl-10 col-lg-11 col-md-12 d-flex justify-content-center overflow-auto"
      >
        <BokehPlot :bokeh-plot-data="bokehPlotData" class="mw-100" />
      </div>
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import vSelect from "vue-select";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    vSelect,
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
      isUpdating: false,
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
    currentBlock() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    availableFolders() {
      return this.currentBlock.available_folders || [];
    },
    ppm1: createComputedSetterForBlockField("ppm1"),
    ppm2: createComputedSetterForBlockField("ppm2"),
    nmr_folder_name: createComputedSetterForBlockField("nmr_folder_name"),
    echem_folder_name: createComputedSetterForBlockField("echem_folder_name"),
    file_id: createComputedSetterForBlockField("file_id"),
    folder_name: createComputedSetterForBlockField("folder_name"),
  },
  methods: {
    onFileChange() {
      this.nmr_folder_name = "";
      this.echem_folder_name = "";

      this.updateBlock();
    },
    parsePPM() {
      const ppm1Value = parseFloat(this.ppm1);
      const ppm2Value = parseFloat(this.ppm2);

      if (isNaN(ppm1Value) || isNaN(ppm2Value)) {
        this.ppmParseError = "Please provide valid numbers for both PPM values";
        return false;
      } else if (ppm1Value === ppm2Value) {
        this.ppmParseError = "PPM values must be different";
        return false;
      }

      this.ppmParseError = "";
      return true;
    },
    onFolderSelected() {
      if (this.nmr_folder_name && this.echem_folder_name) {
        this.folderNameError = "";
        this.updateBlock();
      } else if (this.nmr_folder_name || this.echem_folder_name) {
        this.folderNameError = "Both NMR and Echem folder names are required";
      }
    },
    updateBlock() {
      this.isLoading = true;
      const foundFile = this.all_files.find((file) => file.immutable_id === this.file_id);
      this.folder_name = foundFile?.name || "Folder not found";

      const blockToUpdate = {
        ...this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      };

      blockToUpdate.ppm1 = this.ppm1;
      blockToUpdate.ppm2 = this.ppm2;

      updateBlockFromServer(this.item_id, this.block_id, blockToUpdate)
        .then(() => {
          this.isLoading = false;
        })
        .catch((error) => {
          this.isLoading = false;
          console.error("Error updating block:", error);
        });
    },
    handlePPMUpdate() {
      if (this.parsePPM()) {
        this.updateBlock();
      }
    },
  },
};
</script>

<style scoped></style>
