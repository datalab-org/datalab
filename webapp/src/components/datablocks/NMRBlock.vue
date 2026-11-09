<template>
  <!-- think about elegant two-way binding to DataBlockBase... or, just pass all the block data into
DataBlockBase as a prop, and save from within DataBlockBase  -->
  <DataBlockBase :item_id="item_id" :block_id="block_id">
    <template #controls>
      <FileSelectDropdown
        v-model="file_id"
        :item_id="item_id"
        :block_id="block_id"
        :extensions="blockInfo.attributes.accepted_file_extensions"
        update-block-on-change
      />
      <div v-show="file_id">
        <div class="block-controls mt-2">
          <div class="block-control">
            <label class="block-control-label" for="nmr-process">Process number</label>
            <select
              id="nmr-process"
              v-model="selected_process"
              class="custom-select custom-select-sm"
              @change="updateBlock"
            >
              <option v-for="process_number in block.available_processes" :key="process_number">
                {{ process_number }}
              </option>
            </select>
          </div>
          <div class="block-control">
            <label class="block-control-label" for="nmr-experiment">Experiment</label>
            <select
              id="nmr-experiment"
              v-model="selected_experiment"
              class="custom-select custom-select-sm"
              @change="updateBlock"
            >
              <option v-for="experiment in block.available_experiments" :key="experiment">
                {{ experiment }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="hasSummary" class="nmr-summary mt-4">
          <div class="summary-fields">
            <div v-if="metadata?.nucleus" class="summary-field">
              <div class="summary-label">Nucleus</div>
              <div class="summary-value summary-value-lg">
                <Isotope :isotope-string="metadata.nucleus" />
              </div>
            </div>
            <div v-if="metadata?.pulse_program_name" class="summary-field">
              <div class="summary-label">Pulse program</div>
              <div class="summary-value">{{ metadata.pulse_program_name }}</div>
            </div>
          </div>
          <div v-if="metadata?.title" class="summary-field mt-3">
            <div class="summary-label">Title</div>
            <div class="summary-value nmr-title">{{ metadata.title }}</div>
          </div>
        </div>
      </div>
    </template>

    <template #plot>
      <div v-show="file_id" id="bokehPlotContainer">
        <BokehPlot v-if="bokehPlotData" :bokeh-plot-data="bokehPlotData" />
      </div>
    </template>
  </DataBlockBase>
</template>

<script>
import DataBlockBase from "@/components/datablocks/DataBlockBase";
import FileSelectDropdown from "@/components/FileSelectDropdown";
import BokehPlot from "@/components/BokehPlot";
import Isotope from "@/components/Isotope";

import { createComputedSetterForBlockField } from "@/field_utils.js";
import { updateBlockFromServer } from "@/server_fetch_utils.js";

export default {
  components: {
    DataBlockBase,
    FileSelectDropdown,
    BokehPlot,
    Isotope,
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
    block() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id];
    },
    metadata() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]?.metadata;
    },
    hasSummary() {
      return Boolean(
        this.metadata?.nucleus || this.metadata?.pulse_program_name || this.metadata?.title,
      );
    },
    bokehPlotData() {
      return this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id]
        .bokeh_plot_data;
    },
    blockInfo() {
      return this.$store.state.blocksInfos["nmr"];
    },
    file_id: createComputedSetterForBlockField("file_id"),
    selected_process: createComputedSetterForBlockField("selected_process"),
    selected_experiment: createComputedSetterForBlockField("selected_experiment"),
  },
  methods: {
    updateBlock() {
      updateBlockFromServer(
        this.item_id,
        this.block_id,
        this.$store.state.all_item_data[this.item_id]["blocks_obj"][this.block_id],
      ).catch((error) => {
        console.error("Error updating block:", error);
      });
    },
  },
};
</script>

<style scoped>
/* Block controls sit in a wrapping row, each with its label above, so they line
   up with the shared file selector regardless of label length. */
.block-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem 1.5rem;
}

.block-control {
  display: flex;
  flex-direction: column;
}

.block-control-label {
  margin-bottom: 0.15rem;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #6c757d;
}

.block-control select {
  min-width: 8rem;
}

/* Headline acquisition parameters, shown above the plot so the fields that
   identify the experiment are readable at a glance. Laid out as labelled
   columns rather than a full-width table. */
.summary-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem 2.5rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: #6c757d;
}

.summary-value {
  margin-top: 0.15rem;
  color: #212529;
}

.summary-value-lg {
  font-size: 1.5rem;
  line-height: 1.2;
}

/* TopSpin titles are free text and often span several lines. */
.nmr-title {
  max-width: 40rem;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.attribute-label {
  color: grey;
}

th {
  color: #454545;
  font-weight: 500;
}
</style>
