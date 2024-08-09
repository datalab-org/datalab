<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <FileSelectDropdown
      v-model="file_id"
      :item_id="item_id"
      :block_id="block_id"
      :extensions="blockInfo.attributes.accepted_file_extensions"
      update-block-on-change
    />

		<div v-if="file_id">
      <div class="form-row col-md-6 col-lg-4 mt-2 mb-2 pl-0">
				<div v-for="property in blockPropertiesSpec" :key="property">
					<div class="input-group form-inline">
						<label class="mr-2"><b>{{ property.label }}:</b></label>
						<input
							v-model="property"
							type="text"
							class="form-control"
							@keydown.enter="updateBlock()"
							@blur="updateBlock()"
						/>
          </div>
        </div>
      </div>

    <div class="row">
      <div id="bokehPlotContainer" class="col-xl-9 col-lg-10 col-md-11 mx-auto">
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
		block_type: {
			type: String,
			required: true,
		}
  },
  data() {
    return {
      wavelengthParseError: "",
    };
  },
  computed: {
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos[this.block_type];
    },
		blockPropertiesSpec() {
			return this.blockInfo()["properties"];
		},
		properties: createComputedSetterForBlockField("properties"),
    file_id: createComputedSetterForBlockField("file_id"),
  },
  methods: {
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
