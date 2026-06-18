<!--
  Custom panel for the `heat_treatments` example item type.

  Demonstrates what a plugin-supplied .vue unlocks beyond annotation-only rendering:
   - a cross-CUSTOM-type reference (to `annealing_protocols`),
   - "Populate from protocol" — fetch the linked custom item and seed fields
     (the same pattern as AELIOS "Populate from recipe"),
   - a live, client-computed SVG temperature-vs-time plot of the as-run schedule.

  Fully self-contained: it renders all of its own fields and reuses only datalab's
  atomic components (ItemSelect, TooltipIcon).
-->
<template>
  <div class="container heat-treatment-panel mt-3">
    <div class="plugin-card">
      <div class="plugin-card-header d-flex align-items-center justify-content-between">
        <span>Heat Treatment</span>
        <TooltipIcon
          text="Link the annealing protocol that was followed and click 'Populate from protocol' to copy its schedule. The temperature profile is drawn live from the as-run values below."
        />
      </div>
      <div class="plugin-card-body">
        <div class="form-row">
          <!-- Protocol: cross custom-type reference -->
          <div class="form-group col-md-6 col-lg-4">
            <label>Annealing protocol</label>
            <div v-if="itemData.protocol" class="input-group">
              <div class="form-control ref-display">
                <FormattedItemName
                  :item_id="itemData.protocol.item_id"
                  :item-type="itemData.protocol.type"
                  :name="itemData.protocol.name || ''"
                  enable-click
                  enable-modified-click
                />
              </div>
              <div class="input-group-append">
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  title="Clear"
                  @click="updateField('protocol', null)"
                >
                  <font-awesome-icon :icon="['fas', 'times']" />
                </button>
              </div>
            </div>
            <ItemSelect
              v-else
              :model-value="itemData.protocol"
              :types-to-query="['annealing_protocols']"
              @update:model-value="updateField('protocol', $event)"
            />
          </div>

          <!-- Precursor: reference to a built-in material -->
          <div class="form-group col-md-6 col-lg-4">
            <label>Precursor</label>
            <div v-if="itemData.precursor" class="input-group">
              <div class="form-control ref-display">
                <FormattedItemName
                  :item_id="itemData.precursor.item_id"
                  :item-type="itemData.precursor.type"
                  :name="itemData.precursor.name || ''"
                  enable-click
                  enable-modified-click
                />
              </div>
              <div class="input-group-append">
                <button
                  type="button"
                  class="btn btn-outline-secondary"
                  title="Clear"
                  @click="updateField('precursor', null)"
                >
                  <font-awesome-icon :icon="['fas', 'times']" />
                </button>
              </div>
            </div>
            <ItemSelect
              v-else
              :model-value="itemData.precursor"
              :types-to-query="['samples', 'starting_materials']"
              @update:model-value="updateField('precursor', $event)"
            />
          </div>

          <!-- Atmosphere -->
          <div class="form-group col-md-6 col-lg-4">
            <label for="ht-atmosphere">Atmosphere</label>
            <select
              id="ht-atmosphere"
              class="form-control"
              :value="itemData.atmosphere ?? ''"
              @change="updateField('atmosphere', $event.target.value || null)"
            >
              <option value="">—</option>
              <option v-for="a in atmospheres" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
        </div>

        <div class="d-flex align-items-center mb-3">
          <button
            class="btn btn-sm btn-outline-secondary mr-1"
            :disabled="!itemData.protocol || seeding"
            @click="seedFromProtocol"
          >
            <font-awesome-icon :icon="['fas', 'sync']" :spin="seeding" class="mr-1" />
            {{ seeding ? "Populating…" : "Populate from protocol" }}
          </button>
          <TooltipIcon
            text="Copies peak temperature, ramp rate, dwell time and atmosphere from the linked protocol, converting to °C / °C·min⁻¹ / min. Edit the as-run values afterwards as needed."
          />
        </div>

        <div class="form-row">
          <div class="form-group col-6 col-md-3">
            <label for="ht-peak">Peak temperature</label>
            <div class="input-group">
              <input
                id="ht-peak"
                type="number"
                step="any"
                class="form-control"
                :value="itemData.peak_temperature ?? ''"
                @change="updateNumber('peak_temperature', $event.target.value)"
              />
              <div class="input-group-append"><span class="input-group-text">°C</span></div>
            </div>
          </div>
          <div class="form-group col-6 col-md-3">
            <label for="ht-ramp">Ramp rate</label>
            <div class="input-group">
              <input
                id="ht-ramp"
                type="number"
                step="any"
                class="form-control"
                :value="itemData.ramp_rate ?? ''"
                @change="updateNumber('ramp_rate', $event.target.value)"
              />
              <div class="input-group-append"><span class="input-group-text">°C/min</span></div>
            </div>
          </div>
          <div class="form-group col-6 col-md-3">
            <label for="ht-dwell">Dwell time</label>
            <div class="input-group">
              <input
                id="ht-dwell"
                type="number"
                step="any"
                class="form-control"
                :value="itemData.dwell_time ?? ''"
                @change="updateNumber('dwell_time', $event.target.value)"
              />
              <div class="input-group-append"><span class="input-group-text">min</span></div>
            </div>
          </div>
        </div>

        <!-- Live temperature-vs-time profile, computed client-side. -->
        <div class="profile-wrapper mt-2">
          <label class="mb-1">Temperature profile</label>
          <div v-if="profile" class="profile-box">
            <svg :viewBox="`0 0 ${profile.W} ${profile.H}`" class="profile-svg">
              <!-- axes -->
              <line
                :x1="profile.padL" :y1="profile.padT" :x2="profile.padL" :y2="profile.y0"
                class="axis"
              />
              <line
                :x1="profile.padL" :y1="profile.y0" :x2="profile.W - profile.padR" :y2="profile.y0"
                class="axis"
              />
              <!-- peak gridline -->
              <line
                :x1="profile.padL" :y1="profile.peakY" :x2="profile.W - profile.padR" :y2="profile.peakY"
                class="gridline"
              />
              <text :x="profile.W - profile.padR" :y="profile.peakY - 4" class="lbl" text-anchor="end">
                peak {{ profile.peakLabel }}
              </text>
              <!-- temperature curve -->
              <polyline :points="profile.poly" class="curve" />
              <!-- axis labels -->
              <text :x="profile.padL" :y="profile.H - 6" class="lbl">0</text>
              <text :x="profile.W - profile.padR" :y="profile.H - 6" class="lbl" text-anchor="end">
                {{ profile.totalLabel }}
              </text>
              <text x="6" :y="profile.padT + 8" class="lbl">T (°C)</text>
            </svg>
            <div class="text-muted small mt-1">
              Peak <strong>{{ profile.peak }} °C</strong> · ramp
              {{ itemData.ramp_rate }} °C/min · dwell {{ itemData.dwell_time }} min · total ≈
              <strong>{{ profile.totalLabel }}</strong>
            </div>
          </div>
          <div v-else class="text-muted small fst-italic">
            Enter peak temperature, ramp rate and dwell time (or populate from a protocol) to draw
            the profile.
          </div>
        </div>
      </div>
    </div>

    <!-- Second bespoke card: characterization + a live, client-computed mass-loss bar. -->
    <div class="plugin-card mt-3">
      <div class="plugin-card-header"><span>Characterization</span></div>
      <div class="plugin-card-body">
        <div class="form-row">
          <div class="form-group col-md-6 col-lg-4">
            <label for="ht-phase">Resulting phase</label>
            <select
              id="ht-phase"
              class="form-control"
              :value="itemData.resulting_phase ?? ''"
              @change="updateField('resulting_phase', $event.target.value || null)"
            >
              <option value="">—</option>
              <option v-for="p in phases" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          <div class="form-group col-md-6 col-lg-4">
            <label for="ht-color">Colour</label>
            <input
              id="ht-color"
              type="text"
              class="form-control"
              :value="itemData.color ?? ''"
              @change="updateField('color', $event.target.value || null)"
            />
          </div>
          <div class="form-group col-md-6 col-lg-4">
            <label for="ht-crucible">Crucible</label>
            <select
              id="ht-crucible"
              class="form-control"
              :value="itemData.crucible ?? ''"
              @change="updateField('crucible', $event.target.value || null)"
            >
              <option value="">—</option>
              <option v-for="c in crucibles" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
        </div>

        <div class="form-row align-items-end">
          <div class="form-group col-6 col-md-3">
            <label for="ht-mass-before">Mass before</label>
            <div class="input-group">
              <input
                id="ht-mass-before"
                type="number"
                step="any"
                class="form-control"
                :value="itemData.mass_before ?? ''"
                @change="updateNumber('mass_before', $event.target.value)"
              />
              <div class="input-group-append"><span class="input-group-text">g</span></div>
            </div>
          </div>
          <div class="form-group col-6 col-md-3">
            <label for="ht-mass-after">Mass after</label>
            <div class="input-group">
              <input
                id="ht-mass-after"
                type="number"
                step="any"
                class="form-control"
                :value="itemData.mass_after ?? ''"
                @change="updateNumber('mass_after', $event.target.value)"
              />
              <div class="input-group-append"><span class="input-group-text">g</span></div>
            </div>
          </div>
          <div class="form-group col-md-6">
            <label class="mb-1">Mass loss</label>
            <div v-if="massLoss != null" class="d-flex align-items-center">
              <div class="mass-loss-track mr-2">
                <div class="mass-loss-fill" :style="{ width: Math.min(massLoss, 100) + '%' }"></div>
              </div>
              <strong>{{ massLoss.toFixed(1) }} %</strong>
            </div>
            <div v-else class="text-muted small fst-italic">Enter both masses to compute loss.</div>
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

const AMBIENT_C = 25;

export default {
  name: "HeatTreatmentPanel",
  components: { ItemSelect, TooltipIcon, FormattedItemName },
  props: {
    item_id: { type: String, required: true },
    itemType: { type: String, required: true },
  },
  data() {
    return {
      seeding: false,
      atmospheres: ["air", "N2", "Ar", "O2", "forming_gas", "vacuum"],
      phases: ["olivine", "spinel", "layered", "rock-salt", "perovskite", "amorphous", "other"],
      crucibles: ["alumina", "platinum", "quartz", "graphite"],
    };
  },
  computed: {
    itemData() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    // Mass lost during treatment, as a percentage — a simple client-side derived value.
    massLoss() {
      const b = Number(this.itemData.mass_before);
      const a = Number(this.itemData.mass_after);
      if (!(b > 0) || !(a >= 0) || a > b) return null;
      return ((b - a) / b) * 100;
    },
    // Build the ambient → ramp → dwell → cool profile and its SVG geometry.
    profile() {
      const peak = Number(this.itemData.peak_temperature);
      const ramp = Number(this.itemData.ramp_rate);
      const dwell = Number(this.itemData.dwell_time);
      if (!(peak > AMBIENT_C) || !(ramp > 0) || !(dwell >= 0)) return null;

      const tRamp = (peak - AMBIENT_C) / ramp;
      const tDwellEnd = tRamp + dwell;
      const tEnd = tDwellEnd + (peak - AMBIENT_C) / ramp; // symmetric cool at the ramp rate
      const pts = [
        [0, AMBIENT_C],
        [tRamp, peak],
        [tDwellEnd, peak],
        [tEnd, AMBIENT_C],
      ];

      const W = 540, H = 180, padL = 44, padR = 12, padT = 16, padB = 26;
      const y0 = H - padB;
      const tMax = tEnd || 1;
      const yMax = peak * 1.08;
      const sx = (t) => padL + (t / tMax) * (W - padL - padR);
      const sy = (v) => y0 - (v / yMax) * (y0 - padT);
      const poly = pts.map(([t, v]) => `${sx(t).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");

      const totalLabel = tEnd >= 60 ? `${(tEnd / 60).toFixed(1)} h` : `${tEnd.toFixed(0)} min`;

      return {
        W, H, padL, padR, padT, y0,
        poly,
        peakY: sy(peak),
        peak: Math.round(peak),
        peakLabel: `${Math.round(peak)} °C`,
        totalLabel,
      };
    },
  },
  methods: {
    updateField(fieldName, value) {
      this.$store.commit("updateItemData", {
        item_id: this.item_id,
        item_data: { [fieldName]: value },
      });
    },
    updateNumber(fieldName, raw) {
      this.updateField(fieldName, raw === "" ? null : Number(raw));
    },
    // Fetch the linked protocol (a custom item type) and copy its schedule, normalizing
    // units to °C / °C·min⁻¹ / min. Mirrors the AELIOS "Populate from recipe" flow.
    async seedFromProtocol() {
      const ref = this.itemData.protocol;
      if (!ref?.item_id) return;
      this.seeding = true;
      try {
        await getItemData(ref.item_id);
        const p = this.$store.state.all_item_data[ref.item_id];
        if (!p) return;

        let peak = p.peak_temperature;
        if (peak != null && p.peak_temperature_unit === "K") peak = Number(peak) - 273.15;
        // °C/min and K/min are identical for a rate (a temperature *difference*).
        const ramp = p.ramp_rate != null ? Number(p.ramp_rate) : null;
        let dwell = p.dwell_time;
        if (dwell != null && p.dwell_time_unit === "h") dwell = Number(dwell) * 60;

        this.$store.commit("updateItemData", {
          item_id: this.item_id,
          item_data: {
            peak_temperature: peak != null ? Number(Number(peak).toFixed(2)) : null,
            ramp_rate: ramp,
            dwell_time: dwell != null ? Number(dwell) : null,
            atmosphere: p.atmosphere ?? this.itemData.atmosphere ?? null,
          },
        });
      } finally {
        this.seeding = false;
      }
    },
  },
};
</script>

<style scoped>
.heat-treatment-panel {
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
.mass-loss-track {
  flex: 1;
  height: 0.9rem;
  background: #f1f3f5;
  border-radius: 0.45rem;
  overflow: hidden;
}
.mass-loss-fill {
  height: 100%;
  background: #a83232;
  transition: width 0.2s ease;
}
.ref-display {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  flex: 1;
}
.ref-display:hover {
  background-color: #e9ecef;
  text-decoration: none;
  color: inherit;
}
.profile-box {
  max-width: 560px;
}
.profile-svg {
  width: 100%;
  height: auto;
  border: 1px solid #eee;
  border-radius: 0.25rem;
  background: #fff;
}
.profile-svg .axis {
  stroke: #adb5bd;
  stroke-width: 1;
}
.profile-svg .gridline {
  stroke: #e0a3a3;
  stroke-width: 1;
  stroke-dasharray: 4 3;
}
.profile-svg .curve {
  fill: none;
  stroke: #a83232;
  stroke-width: 2;
}
.profile-svg .lbl {
  fill: #868e96;
  font-size: 10px;
}
</style>
