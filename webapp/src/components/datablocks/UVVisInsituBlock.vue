<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <template #controls>
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        update-block-on-change
        @change="onFileChange"
      />
      <div v-show="file_id">
        <div class="row">
          <div class="col-lg-4 col-md-6 col-sm-12 mb-2">
            <label><b>UV-Vis folder name</b></label>
            <FolderSelect
              v-model="uvvis_folder_name"
              :options="availableFolders"
              @update:model-value="onFolderSelected"
            />
          </div>
          <div class="col-lg-4 col-md-6 col-sm-12 mb-2">
            <label><b>UV-Vis reference folder name</b></label>
            <FolderSelect
              v-model="uvvis_reference_folder_name"
              :options="availableFolders"
              @update:model-value="onFolderSelected"
            />
          </div>
          <div class="col-lg-4 col-md-6 col-sm-12 mb-2">
            <label><b>Echem folder name</b></label>
            <FolderSelect
              v-model="echem_folder_name"
              :options="availableFolders"
              @update:model-value="onFolderSelected"
            />
          </div>
        </div>
        <div v-if="folderNameError" class="alert alert-danger mt-2 mx-auto">
          {{ folderNameError }}
        </div>
      </div>
      <div class="form-group mb-2">
        <label class="mr-2"><b>Scan time (s)</b></label>
        <input
          v-model="scan_time_buffer"
          type="text"
          class="form-control"
          placeholder="Enter scan time"
          style="width: 160px; display: inline-block"
          inputmode="decimal"
          @change="onScanTimeSelected"
        />
      </div>
      <div class="form-inline mb-2">
        <label class="mr-2"><b>Data granularity</b></label>
        <input
          v-model="data_granularity_buffer"
          type="number"
          class="form-control"
          min="1"
          style="width: 100px"
        />
        <label class="ml-3 mr-2"><b>Sample granularity</b></label>
        <input
          v-model="sample_granularity_buffer"
          type="number"
          class="form-control"
          min="1"
          style="width: 100px"
        />
        <button class="btn btn-primary ml-2" @click="onGranularitySubmit">Apply</button>
      </div>
    </template>

    <template #plot>
      <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
    </template>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import FolderSelect from "@/components/FolderSelect";
import BokehPlot from "@/components/BokehPlot";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    FolderSelect,
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
      folderNameError: "",
      isUpdating: false,
      scan_time_buffer: "",
    };
  },
  watch: {
    scan_time: {
      immediate: true,
      handler(newVal) {
        this.scan_time_buffer = newVal;
      },
    },
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
      return this.$store.state.blocksInfos["insitu-uvvis"];
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
    uvvis_folder_name: createComputedSetterForBlockField("uvvis_folder_name"),
    uvvis_reference_folder_name: createComputedSetterForBlockField("uvvis_reference_folder_name"),
    echem_folder_name: createComputedSetterForBlockField("echem_folder_name"),
    file_id: createComputedSetterForBlockField("file_id"),
    folder_name: createComputedSetterForBlockField("folder_name"),
    scan_time: createComputedSetterForBlockField("scan_time"),
    data_granularity: createComputedSetterForBlockField("data_granularity"),
    sample_granularity: createComputedSetterForBlockField("sample_granularity"),
  },
  methods: {
    onFileChange() {
      this.uvvis_folder_name = "";
      this.uvvis_reference_folder_name = "";
      this.echem_folder_name = "";

      this.updateBlock();
    },
    onFolderSelected() {
      if (this.uvvis_folder_name && this.echem_folder_name && this.uvvis_reference_folder_name) {
        this.folderNameError = "";
        this.updateBlock();
      } else if (
        this.uvvis_folder_name ||
        this.echem_folder_name ||
        this.uvvis_reference_folder_name
      ) {
        this.folderNameError =
          "UV-Vis sample and reference folders, along with an echem folder is required.";
      }
    },
    onScanTimeSelected() {
      const parsed = parseFloat(this.scan_time_buffer);
      if (!isNaN(parsed)) {
        this.scan_time = parsed;
        this.updateBlock();
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
