<template>
  <div id="substance-information" ref="outerdiv" class="data-block" data-testid="substance-block">
    <div
      class="datablock-header"
      :class="{ clickable: !isEditing }"
      @click="!isEditing && enterEditMode()"
    >
      <font-awesome-icon :icon="['fas', 'flask']" fixed-width class="header-icon" />
      <label class="block-title">Substance Information</label>
      <font-awesome-icon
        v-if="!isEditing"
        id="edit-icon"
        class="ml-auto mr-2"
        icon="pen"
        size="xs"
      />
    </div>

    <!-- COMPACT DISPLAY MODE -->
    <div v-if="!isEditing" class="substance-card" @click="enterEditMode">
      <div v-if="hasAnyData" class="substance-card-content">
        <div class="substance-display-row">
          <!-- Molecule structure from InChIKey/InChI/SMILES -->
          <div v-if="hasStructureIdentifier && !moleculeImageError" class="molecule-display">
            <img
              :src="pubchemImageUrl"
              alt="Molecule structure"
              class="molecule-image-compact"
              @error="moleculeImageError = true"
            />
          </div>

          <!-- Text info items -->
          <div class="info-items">
            <!-- Chemical formula -->
            <div v-if="chemform" class="info-item">
              <span class="display-label">Formula</span>
              <ChemicalFormula :formula="chemform" class="formula-value" />
            </div>

            <!-- Molar mass -->
            <div v-if="molar_mass" class="info-item">
              <span class="display-label">Molar mass</span>
              <span class="info-value">{{ molar_mass }} g/mol</span>
            </div>

            <!-- GHS Hazard pictograms (inline with other info) -->
            <div v-if="GHS_codes && hasPictograms" class="info-item ghs-item">
              <span class="display-label">Hazards</span>
              <GHSHazardPictograms :model-value="GHS_codes" />
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state placeholder -->
      <div v-else class="substance-empty-state">
        <span class="text-muted">
          <font-awesome-icon :icon="['fas', 'plus-circle']" class="mr-1" />
          Click to add substance information
        </span>
      </div>
    </div>

    <!-- EDIT MODE -->
    <OnClickOutside v-if="isEditing" :options="{ ignore: [outerDivRef] }" @trigger="exitEditMode">
      <div class="substance-edit-form">
        <div class="form-row">
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-chemform">Chemical formula</label>
            <ChemFormulaInput id="substance-chemform" v-model="chemform" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-smiles">SMILES</label>
            <input id="substance-smiles" v-model="smiles" class="form-control" type="text" />
          </div>
          <div v-if="hasStructureIdentifier" class="form-group col-sm-4 col-6 pr-2">
            <label>Structure</label>
            <div class="molecule-image-container">
              <img
                v-if="!moleculeImageError"
                :src="pubchemImageUrl"
                alt="Molecule structure"
                class="molecule-image"
                @error="moleculeImageError = true"
              />
              <span v-else class="molecule-image-error">Unable to load structure image</span>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-inchi">InChI</label>
            <input id="substance-inchi" v-model="inchi" class="form-control" type="text" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-inchi-key">InChI Key</label>
            <input id="substance-inchi-key" v-model="inchi_key" class="form-control" type="text" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-mass">Molar mass / molecular weight</label>
            <input id="substance-mass" v-model="molar_mass" class="form-control" type="text" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-6 col-12 pr-2">
            <label for="substance-ghs">GHS codes</label>
            <GHSHazardInformation id="substance-ghs" v-model="GHS_codes" :editable="true" />
          </div>
        </div>

        <!-- Done button -->
        <div class="form-row">
          <div class="col-12 text-right">
            <button class="btn btn-sm btn-outline-secondary" @click.stop="exitEditMode">
              Done
            </button>
          </div>
        </div>
      </div>
    </OnClickOutside>
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import GHSHazardInformation from "@/components/GHSHazardInformation.vue";
import GHSHazardPictograms from "@/components/GHSHazardPictograms.vue";
import ChemFormulaInput from "@/components/ChemFormulaInput";
import ChemicalFormula from "@/components/ChemicalFormula";
import { OnClickOutside } from "@vueuse/components";
import { getPictogramsFromHazardInformation } from "@/resources.js";

export default {
  components: {
    ChemFormulaInput,
    ChemicalFormula,
    GHSHazardInformation,
    GHSHazardPictograms,
    OnClickOutside,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      isEditing: false,
      outerDivRef: null,
      moleculeImageError: false,
    };
  },
  computed: {
    chemform: createComputedSetterForItemField("chemform"),
    smiles: createComputedSetterForItemField("smiles"),
    inchi: createComputedSetterForItemField("inchi"),
    inchi_key: createComputedSetterForItemField("inchi_key"),
    GHS_codes: createComputedSetterForItemField("GHS_codes"),
    molar_mass: createComputedSetterForItemField("molar_mass"),

    hasStructureIdentifier() {
      return !!(this.inchi_key || this.inchi || this.smiles);
    },

    pubchemImageUrl() {
      // Prefer InChIKey > InChI > SMILES (InChI/InChIKey are more robust)
      if (this.inchi_key) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/${encodeURIComponent(this.inchi_key)}/PNG?image_size=200x200`;
      }
      if (this.inchi) {
        // InChI contains "/" characters, so must be passed as query parameter
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/PNG?inchi=${encodeURIComponent(this.inchi)}&image_size=200x200`;
      }
      if (this.smiles) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/${encodeURIComponent(this.smiles)}/PNG?image_size=200x200`;
      }
      return null;
    },

    hasAnyData() {
      return !!(
        this.chemform ||
        this.smiles ||
        this.inchi ||
        this.inchi_key ||
        this.GHS_codes ||
        this.molar_mass
      );
    },

    hasPictograms() {
      if (!this.GHS_codes) return false;
      const pictograms = getPictogramsFromHazardInformation(this.GHS_codes);
      return pictograms.size > 0;
    },
  },
  watch: {
    // Reset error state when any structure identifier changes
    inchi_key() {
      this.moleculeImageError = false;
    },
    inchi() {
      this.moleculeImageError = false;
    },
    smiles() {
      this.moleculeImageError = false;
    },
  },
  mounted() {
    this.outerDivRef = this.$refs.outerdiv;
  },
  methods: {
    enterEditMode() {
      this.isEditing = true;
    },
    exitEditMode() {
      this.isEditing = false;
    },
  },
};
</script>

<style scoped>
.data-block {
  padding-bottom: 18px;
}

.datablock-header {
  display: flex;
  align-items: center;
  font-size: large;
  height: 35px;
  margin: auto;
}

.datablock-header.clickable {
  cursor: pointer;
}

.datablock-header.clickable:hover {
  background-color: #f8f9fa;
}

.header-icon {
  color: #004175;
  margin-right: 0.5rem;
}

.block-title {
  display: flex;
  align-items: center;
  font-size: large;
  font-weight: 500;
  margin: auto 0;
}

#edit-icon {
  color: grey;
}

/* Compact Card Display Styles */
.substance-card {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem 1rem;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.substance-card:hover {
  border-color: #adb5bd;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.substance-card-content {
  display: flex;
  flex-direction: column;
}

.substance-display-row {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 1rem;
}

.molecule-display {
  flex-shrink: 0;
}

.molecule-image-compact {
  width: 100px;
  height: 100px;
  object-fit: contain;
  background-color: white;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  padding: 0.25rem;
}

.info-items {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 1.5rem;
  flex: 1;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.ghs-item {
  flex-basis: 100%;
}

.ghs-item :deep(.ghs-display) {
  margin: 0;
}

/* Smaller GHS icons for compact view */
.ghs-item :deep(.ghs-icon) {
  width: 2.5rem;
  height: 2.5rem;
  margin-right: 4px;
}

.display-label {
  font-size: 0.75rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.125rem;
}

.formula-value {
  font-size: 1.25rem;
  font-weight: 500;
}

.info-value {
  font-size: 1rem;
}

.substance-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  color: #6c757d;
}

/* Edit Form Styles */
.substance-edit-form {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  background-color: #fff;
}

.molecule-image-container {
  background-color: white;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
}

.molecule-image {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.molecule-image-error {
  color: #6c757d;
  font-size: 0.875rem;
  font-style: italic;
}
</style>
