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
          <label class="mr-2"><b>XRD folder name</b></label>
          <v-select
            v-model="xrd_folder_name"
            :options="availableFolders"
            :reduce="(folder) => folder"
            class="folder-select mr-2"
            placeholder="Select a folder"
            @update:model-value="onFolderSelected"
          />
          <label class="mr-2"><b>Temperature or Echem folder name</b></label>
          <v-select
            v-model="time_series_folder_name"
            :options="availableFolders"
            :reduce="(folder) => folder"
            class="folder-select"
            placeholder="Select a folder"
            @update:model-value="onFolderSelected"
          />
        </div>
      </div>
      <div v-if="folderNameError" class="alert alert-danger mt-2 mx-auto">
        {{ folderNameError }}
      </div>
    </div>
    <div class="form-inline mb-2">
      <label class="mr-2"><b>Data granularity</b></label>
      <input
        v-model="data_granularity_buffer"
        type="text"
        class="form-control mr-3"
        style="width: 100px; display: inline-block"
      />
      <label class="mr-2"><b>Sample granularity</b></label>
      <input
        v-model="sample_granularity_buffer"
        type="text"
        class="form-control"
        style="width: 100px; display: inline-block"
      />
      <button class="btn btn-primary ml-3" @click="onGranularitySubmit">Apply</button>
    </div>
    <div
      v-show="xrd_folder_name && time_series_folder_name"
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
      folderNameError: "",
      isUpdating: false,
      scan_time_buffer: "",
    };
  },
  watch: {
    data_granularity: {
      immediate: true,
      handler(newVal) {
        this.data_granularity_buffer = newVal;
      },
    },
    sample_granularity: {
      immediate: true,
      handler(newVal) {
        this.sample_granularity_buffer = newVal;
      },
    },
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["insitu-xrd"];
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
    xrd_folder_name: createComputedSetterForBlockField("xrd_folder_name"),
    time_series_folder_name: createComputedSetterForBlockField("time_series_folder_name"),
    file_id: createComputedSetterForBlockField("file_id"),
    folder_name: createComputedSetterForBlockField("folder_name"),
    data_granularity: createComputedSetterForBlockField("data_granularity"),
    sample_granularity: createComputedSetterForBlockField("sample_granularity"),
  },
  methods: {
    onFileChange() {
      this.xrd_folder_name = "";
      this.time_series_folder_name = "";

      this.updateBlock();
    },
    onFolderSelected() {
      if (this.xrd_folder_name && this.time_series_folder_name) {
        this.folderNameError = "";
        this.updateBlock();
      } else if (this.xrd_folder_name || this.time_series_folder_name) {
        this.folderNameError = "XRD and either an echem or temperature folder is required.";
      }
    },
    onGranularitySubmit() {
      const dataVal = parseFloat(this.data_granularity_buffer);
      const sampleVal = parseFloat(this.sample_granularity_buffer);

      if (!isNaN(dataVal)) this.data_granularity = dataVal;
      if (!isNaN(sampleVal)) this.sample_granularity = sampleVal;

      if (!isNaN(dataVal) || !isNaN(sampleVal)) {
        this.updateBlock();
      }
    },
    updateBlock() {
      this.isLoading = true;
      const foundFile = this.all_files.find((file) => file.immutable_id === this.file_id);
      this.folder_name = foundFile?.name || "Folder not found";

      const blockToUpdate = {
        ...this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      };

      updateBlockFromServer(this.item_id, this.block_id, blockToUpdate)
        .then(() => {
          this.isLoading = false;
        })
        .catch((error) => {
          this.isLoading = false;
          console.error("Error updating block:", error);
        });
    },
  },
};
</script>

<style scoped></style>
