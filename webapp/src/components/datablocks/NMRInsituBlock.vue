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
      <div class="row">
        <div class="col-lg-6 col-md-6 col-sm-12 mb-2">
          <label><b>NMR folder name</b></label>
          <FolderSelect
            v-model="nmr_folder_name"
            :options="availableFolders"
            @update:model-value="onFolderChanged"
          />
        </div>
        <div class="col-lg-6 col-md-6 col-sm-12 mb-2">
          <label><b>Echem folder name</b></label>
          <FolderSelect
            v-model="echem_folder_name"
            :options="availableFolders"
            @update:model-value="onFolderChanged"
          />
        </div>
      </div>

      <div v-show="nmr_folder_name && echem_folder_name" class="row mt-2">
        <div class="col-lg-3 col-md-6 col-sm-12 mb-2">
          <label><b>Start Exp:</b></label>
          <input
            v-model.number="local_start_exp"
            type="number"
            class="form-control"
            min="1"
            :max="maxExperiments"
            :placeholder="maxExperiments ? `1-${maxExperiments}` : '1'"
            @input="onParameterChanged"
          />
        </div>

        <div class="col-lg-3 col-md-6 col-sm-12 mb-2">
          <label><b>End Exp:</b></label>
          <input
            v-model.number="local_end_exp"
            type="number"
            class="form-control"
            min="1"
            :max="maxExperiments"
            :placeholder="maxExperiments ? `1-${maxExperiments}` : '1'"
            @input="onParameterChanged"
          />
        </div>

        <div class="col-lg-2 col-md-6 col-sm-12 mb-2">
          <label><b>Step:</b></label>
          <input
            v-model.number="local_step_exp"
            type="number"
            class="form-control"
            min="1"
            @input="onParameterChanged"
          />
        </div>

        <div class="col-lg-2 col-md-6 col-sm-12 mb-2">
          <label><b>Exclude:</b></label>
          <input
            v-model="local_exclude_exp"
            type="text"
            class="form-control"
            placeholder="e.g., 1,3,5"
            @input="onParameterChanged"
          />
        </div>

        <div class="col-lg-2 col-md-12 col-sm-12 mb-2 d-flex align-items-end">
          <button class="btn btn-primary w-100" :disabled="buttonDisabled" @click="applyChanges">
            {{ isUpdating ? "Updating..." : "Apply" }}
          </button>
        </div>
      </div>

      <div v-if="folderNameError || validationError" class="alert alert-danger mt-2 mx-auto">
        {{ folderNameError || validationError }}
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
      originalParameters: {},
      local_start_exp: 1,
      local_end_exp: null,
      local_step_exp: null,
      local_exclude_exp: "",
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["insitu-nmr"];
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
    hasParameterChanges() {
      const currentStartExp = this.start_exp || 1;
      const currentEndExp = this.end_exp || this.maxExperiments;
      const currentStepExp = this.step_exp || null;
      const currentExcludeExp = this.exclude_exp || "";

      const hasChanges =
        this.local_start_exp !== currentStartExp ||
        this.local_end_exp !== currentEndExp ||
        this.local_step_exp !== currentStepExp ||
        this.local_exclude_exp !== currentExcludeExp;

      return hasChanges;
    },
    buttonDisabled() {
      return !this.hasParameterChanges || this.isUpdating || !!this.validationError;
    },
    validationError() {
      if (this.local_start_exp < 1) {
        return "Start experiment must be >= 1";
      }
      if (this.maxExperiments && this.local_start_exp > this.maxExperiments) {
        return `Start experiment must be <= ${this.maxExperiments}`;
      }
      if (this.local_end_exp && this.local_start_exp && this.local_end_exp < this.local_start_exp) {
        return "End experiment must be >= start experiment";
      }
      if (this.maxExperiments && this.local_end_exp && this.local_end_exp > this.maxExperiments) {
        return `End experiment must be <= ${this.maxExperiments}`;
      }
      if (this.local_step_exp != null && this.local_step_exp < 1) {
        return "Step must be >= 1";
      }
      return "";
    },
    maxExperiments() {
      return this.currentBlock.max_experiments || null;
    },
    defaultEndExp() {
      return this.end_exp || this.maxExperiments;
    },
    nmr_folder_name: createComputedSetterForBlockField("nmr_folder_name"),
    echem_folder_name: createComputedSetterForBlockField("echem_folder_name"),
    file_id: createComputedSetterForBlockField("file_id"),
    folder_name: createComputedSetterForBlockField("folder_name"),
    start_exp: createComputedSetterForBlockField("start_exp"),
    end_exp: createComputedSetterForBlockField("end_exp"),
    step_exp: createComputedSetterForBlockField("step_exp"),
    exclude_exp: createComputedSetterForBlockField("exclude_exp"),
  },
  watch: {
    maxExperiments: {
      handler(newVal) {
        if (newVal && !this.local_end_exp) {
          this.local_end_exp = newVal;
        }
      },
      immediate: true,
    },
    defaultEndExp(newVal) {
      if (newVal && !this.hasParameterChanges) {
        this.local_end_exp = newVal;
      }
    },
  },
  mounted() {
    this.originalParameters = {
      start_exp: this.start_exp,
      end_exp: this.end_exp,
      step_exp: this.step_exp,
      exclude_exp: this.exclude_exp,
    };
    this.local_start_exp = this.start_exp || 1;
    this.local_end_exp = this.defaultEndExp;
    this.local_step_exp = this.step_exp || null;
    this.local_exclude_exp = this.exclude_exp || "";
  },
  methods: {
    onFileChange() {
      this.nmr_folder_name = "";
      this.echem_folder_name = "";

      this.updateBlock();
    },
    onFolderChanged() {
      if (this.nmr_folder_name && this.echem_folder_name) {
        this.folderNameError = "";
        this.updateBlock();
      } else if (this.nmr_folder_name || this.echem_folder_name) {
        this.folderNameError = "Both NMR and Echem folder names are required";

        if (this.nmr_folder_name) {
          this.updateBlock();
        }
      }
    },
    applyChanges() {
      this.folderNameError = "";
      this.start_exp = this.local_start_exp;
      this.end_exp = this.local_end_exp;
      this.step_exp = this.local_step_exp;
      this.exclude_exp = this.local_exclude_exp;
      this.updateBlock();
    },
    updateBlock() {
      this.isUpdating = true;
      const foundFile = this.all_files.find((file) => file.immutable_id === this.file_id);
      this.folder_name = foundFile?.name || "Folder not found";

      const blockToUpdate = {
        ...this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      };
      updateBlockFromServer(this.item_id, this.block_id, blockToUpdate)
        .then(() => {
          this.isUpdating = false;
        })
        .catch((error) => {
          this.isUpdating = false;
          console.error("Error updating block:", error);
        });
    },
  },
};
</script>
