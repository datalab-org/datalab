<!--
  Custom panel for the `mixed_solutions` example item type: a list of `solutions`
  references, each with a volume. Pulls each solution's concentration via getItemData
  and computes the composition bar and resulting per-solute concentrations.
-->
<template>
  <div class="container mixed-solution-panel mt-3">
    <div class="plugin-card">
      <div class="plugin-card-header d-flex align-items-center justify-content-between">
        <span>Mixed Solution</span>
        <TooltipIcon
          text="List the solutions blended together and the volume of each. The composition bar and resulting concentrations are computed live from each linked solution's concentration (Σ c·v / Σ v)."
        />
      </div>
      <div class="plugin-card-body">
        <table class="table table-sm mb-2">
          <thead>
            <tr>
              <th>Solution</th>
              <th style="width: 10rem">Volume</th>
              <th style="width: 1%"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(component, index) in components" :key="index">
              <td>
                <div v-if="component.solution" class="input-group">
                  <div class="form-control ref-display">
                    <FormattedItemName
                      :item_id="component.solution.item_id"
                      :item-type="component.solution.type"
                      :name="component.solution.name || ''"
                      enable-click
                      enable-modified-click
                    />
                  </div>
                  <div class="input-group-append">
                    <button
                      type="button"
                      class="btn btn-outline-secondary"
                      title="Clear"
                      @click="updateComponent(index, 'solution', null)"
                    >
                      <font-awesome-icon :icon="['fas', 'times']" />
                    </button>
                  </div>
                </div>
                <ItemSelect
                  v-else
                  :model-value="component.solution"
                  :types-to-query="['solutions']"
                  @update:model-value="updateComponent(index, 'solution', $event)"
                />
              </td>
              <td>
                <div class="input-group">
                  <input
                    type="number"
                    step="any"
                    min="0"
                    class="form-control"
                    :value="component.volume ?? ''"
                    @change="updateVolume(index, $event.target.value)"
                  />
                  <div class="input-group-append"><span class="input-group-text">mL</span></div>
                </div>
              </td>
              <td class="text-right">
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  title="Remove"
                  @click="removeComponent(index)"
                >
                  <font-awesome-icon :icon="['fas', 'times']" />
                </button>
              </td>
            </tr>
            <tr v-if="components.length === 0">
              <td colspan="3" class="text-muted small fst-italic">No components yet.</td>
            </tr>
          </tbody>
        </table>

        <button class="btn btn-sm btn-outline-secondary mb-3" @click="addComponent">
          <font-awesome-icon :icon="['fas', 'plus']" class="mr-1" />Add component
        </button>

        <!-- Live composition bar, computed client-side from the component volumes. -->
        <div class="form-group">
          <label class="mb-1">
            Composition by volume
            <span v-if="totalVolume > 0" class="text-muted"
              >· total <strong>{{ totalVolume.toFixed(1) }} mL</strong></span
            >
          </label>
          <div v-if="segments.length" class="comp-bar">
            <div
              v-for="(seg, i) in segments"
              :key="i"
              class="comp-seg"
              :style="{ width: seg.width + '%', background: seg.color }"
              :title="seg.label"
            >
              <span v-if="seg.width > 10">{{ seg.short }}</span>
            </div>
          </div>
          <div v-else class="text-muted small fst-italic">
            Add components with a volume to see the composition.
          </div>
        </div>

        <!-- Resulting concentrations, recomputed live from the pulled solution data. -->
        <div class="form-group mb-0">
          <label class="mb-1">Resulting concentrations</label>
          <ul v-if="resultingConcentrations.length" class="list-unstyled mb-0">
            <li v-for="row in resultingConcentrations" :key="row.solute">
              <strong>{{ row.solute }}</strong> — {{ row.concentration.toFixed(4) }} mol/L
            </li>
          </ul>
          <div v-else class="text-muted small fst-italic">
            Link solutions that have a concentration to see the result.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";
import TooltipIcon from "@/components/TooltipIcon.vue";
import FormattedItemName from "@/components/FormattedItemName.vue";
import { getItemData } from "@/server_fetch_utils.js";

const PALETTE = ["#3a7ca5", "#b5651d", "#5a8f29", "#8e44ad", "#c0392b", "#16a085"];

export default {
  name: "MixedSolutionPanel",
  components: { ItemSelect, TooltipIcon, FormattedItemName },
  props: {
    item_id: { type: String, required: true },
    itemType: { type: String, required: true },
  },
  computed: {
    itemData() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    components() {
      return this.itemData.components || [];
    },
    // Pull each referenced solution's concentration (normalised to mol/L) and solute label.
    resolvedComponents() {
      return this.components.map((component) => {
        const data = component.solution?.item_id
          ? this.$store.state.all_item_data[component.solution.item_id]
          : null;
        let concentration = data ? Number(data.concentration) : NaN;
        if (data?.concentration_unit === "mmol/L") concentration /= 1000;
        const solute = data?.solute?.name || data?.solute?.item_id || null;
        return {
          volume: Number(component.volume) || 0,
          concentration,
          solute,
          label: component.solution?.name || component.solution?.item_id || "?",
        };
      });
    },
    totalVolume() {
      return this.resolvedComponents.reduce((sum, c) => sum + c.volume, 0);
    },
    segments() {
      if (!(this.totalVolume > 0)) return [];
      return this.resolvedComponents
        .filter((c) => c.volume > 0)
        .map((c, i) => ({
          width: (c.volume / this.totalVolume) * 100,
          color: PALETTE[i % PALETTE.length],
          label: `${c.label}: ${c.volume} mL`,
          short: c.label,
        }));
    },
    resultingConcentrations() {
      if (!(this.totalVolume > 0)) return [];
      const bySolute = {};
      for (const c of this.resolvedComponents) {
        if (!c.solute || !(c.concentration >= 0) || !(c.volume > 0)) continue;
        bySolute[c.solute] = (bySolute[c.solute] || 0) + (c.concentration * c.volume) / this.totalVolume;
      }
      return Object.entries(bySolute).map(([solute, concentration]) => ({ solute, concentration }));
    },
  },
  watch: {
    components: { handler: "ensureSolutionsLoaded", immediate: true },
  },
  methods: {
    commit(components) {
      this.$store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { components },
      });
    },
    addComponent() {
      this.commit([...this.components, { solution: null, volume: null }]);
    },
    removeComponent(index) {
      this.commit(this.components.filter((_, i) => i !== index));
    },
    updateComponent(index, field, value) {
      this.commit(this.components.map((c, i) => (i === index ? { ...c, [field]: value } : c)));
      if (field === "solution" && value?.item_id) getItemData(value.item_id);
    },
    updateVolume(index, raw) {
      this.updateComponent(index, "volume", raw === "" ? null : Number(raw));
    },
    // Pull data for any referenced solution not yet in the store, so concentrations resolve.
    ensureSolutionsLoaded() {
      for (const component of this.components) {
        const id = component.solution?.item_id;
        if (id && !this.$store.state.all_item_data[id]) getItemData(id);
      }
    },
  },
};
</script>

<style scoped>
.mixed-solution-panel {
  padding-bottom: 1rem;
}
.plugin-card {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
}
.plugin-card-header {
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
  padding: 0.65rem 1rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  border-radius: 0.375rem 0.375rem 0 0;
}
.plugin-card-body {
  padding: 1rem;
}
.ref-display {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  color: inherit;
  text-decoration: none;
  flex: 1;
}
.comp-bar {
  display: flex;
  width: 100%;
  height: 1.6rem;
  border-radius: 0.375rem;
  overflow: hidden;
  border: 1px solid #dee2e6;
}
.comp-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  transition: width 0.2s ease;
}
</style>
