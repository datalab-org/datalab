<template>
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-show="blockInfo.attributes.accepted_file_extensions.length > 0"
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      update-block-on-change
    />
    <div v-if="file_id">
      <div v-if="haveWavelengthProperties">
        <div class="form-row col-md-6 col-lg-4 mt-2 mb-2 pl-0">
          <div class="input-group form-inline">
            <label class="mr-2"
              ><b>{{ properties.wavelength.label }}</b></label
            >
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
        </div>

        <div class="row">
          <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
            <BokehPlot :bokeh-plot-data="bokehPlotData" />
          </div>
        </div>
      </div>
      <img
        v-if="isPhoto"
        data-testid="media-block-img"
        :src="media_url"
        class="img-fluid mx-auto"
      />
      <video v-if="isVideo" :src="media_url" controls class="mx-auto" />
    </div>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";

import { blockTypes, API_URL } from "@/resources.js";
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
    all_files() {
      return this.$store.state.all_item_data[this.item_id].files;
    },
    block_data() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    blockInfo() {
      return this.$store.state.blocksInfos[this.block_data.blocktype];
    },
    properties() {
      return blockTypes[this.block_data.blocktype].properties;
    },
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    haveWavelengthProperties() {
      return this.properties && "wavelength" in this.properties;
    },
    media_url() {
      // If the API has already base64 encoded the image, then use it,
      let b64_encoding = this.block_data["b64_encoded_image"] || null;
      if ((b64_encoding != null && b64_encoding[this.file_id]) || null != null) {
        return `data:image/png;base64,${b64_encoding[this.file_id]}`;
      }
      return `${API_URL}/files/${this.file_id}/${this.lookup_file_field("name", this.file_id)}`;
    },
    isPhoto() {
      return [".png", ".jpeg", ".jpg", ".tif", ".tiff"].includes(
        this.lookup_file_field("extension", this.file_id),
      );
    },
    isVideo() {
      return [".mp4", ".mov", ".webm"].includes(this.lookup_file_field("extension", this.file_id));
    },
    file_id: createComputedSetterForBlockField("file_id"),
    wavelength: createComputedSetterForBlockField("wavelength"),
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
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      );
    },
    lookup_file_field(field, file_id) {
      return this.all_files.find((file) => file.immutable_id === file_id)?.[field];
    },
  },
};
</script>

<style scoped>
image,
video {
  display: block;
  max-height: 600px;
}
</style>
