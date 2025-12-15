<template>
  <div id="substance-information" ref="outerdiv" class="data-block" data-testid="substance-block">
    <div
      class="datablock-header"
      :class="{ clickable: !isEditing }"
      @click="!isEditing && enterEditMode()"
    >
      <font-awesome-icon icon="vial" fixed-width class="header-icon" />
      <label class="block-title">Substance Information</label>
      <font-awesome-icon
        v-if="!isEditing"
        id="edit-icon"
        class="ml-auto mr-2"
        icon="pen"
        size="xs"
      />
    </div>

    <!-- VIEW MODE -->
    <div v-if="!isEditing" class="substance-card" @click="enterEditMode">
      <div v-if="hasAnyData" class="substance-card-content">
        <div class="substance-display-row">
          <div v-if="hasStructureIdentifier && !moleculeImageError" class="molecule-display">
            <img
              :src="pubchemImageUrl"
              alt="Molecule structure"
              class="molecule-image-compact"
              @error="moleculeImageError = true"
            />
          </div>
          <div class="info-items">
            <div v-if="chemform" class="info-item">
              <span class="display-label">Formula</span>
              <ChemicalFormula :formula="chemform" class="formula-value" />
            </div>
            <div v-if="molar_mass" class="info-item">
              <span class="display-label">Molar mass</span>
              <span class="info-value">{{ molar_mass }} g/mol</span>
            </div>
            <div v-if="GHS_codes && hasPictograms" class="info-item ghs-item">
              <span class="display-label">Hazards</span>
              <GHSHazardPictograms :model-value="GHS_codes" />
            </div>
          </div>
        </div>
      </div>
      <div v-else class="substance-empty-state">
        <span class="text-muted">
          <font-awesome-icon icon="plus" class="mr-1" />
          Click to add substance information
        </span>
      </div>
    </div>

    <!-- EDIT MODE -->
    <OnClickOutside v-if="isEditing" :options="{ ignore: [outerDivRef] }" @trigger="exitEditMode">
      <div class="substance-edit-form">
        <div class="edit-layout">
          <div class="edit-fields">
            <div class="form-row">
              <div class="form-group col-sm-6 pr-2">
                <label for="substance-chemform">Chemical formula</label>
                <ChemFormulaInput id="substance-chemform" v-model="chemform" />
              </div>
              <div class="form-group col-sm-6 pr-2">
                <label for="substance-smiles">SMILES</label>
                <InputText id="substance-smiles" v-model="smiles" fluid class="p-inputtext-sm" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group col-sm-6 pr-2">
                <label for="substance-inchi">InChI</label>
                <InputText id="substance-inchi" v-model="inchi" fluid class="p-inputtext-sm" />
              </div>
              <div class="form-group col-sm-6 pr-2">
                <label for="substance-inchi-key">InChI Key</label>
                <InputText
                  id="substance-inchi-key"
                  v-model="inchi_key"
                  fluid
                  class="p-inputtext-sm"
                />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group col-sm-6 pr-2">
                <label for="substance-mass">Molar mass (g/mol)</label>
                <InputNumber
                  id="substance-mass"
                  v-model="molar_mass"
                  fluid
                  :min-fraction-digits="0"
                  :max-fraction-digits="4"
                  input-class="p-inputtext-sm"
                  style="width: 100%"
                />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group col-12 pr-2">
                <GHSHazardInformation v-model="GHS_codes" :editable="true" />
              </div>
            </div>
          </div>

          <div v-if="hasStructureIdentifier" class="edit-structure">
            <span class="display-label">Structure</span>
            <div class="molecule-image-container">
              <img
                v-if="!moleculeImageError"
                :src="pubchemImageUrl"
                alt="Molecule structure"
                class="molecule-image"
                @error="moleculeImageError = true"
              />
              <span v-else class="molecule-image-error">Unable to load structure</span>
            </div>
          </div>
        </div>

        <div class="edit-footer">
          <button class="btn btn-sm btn-outline-secondary" @click.stop="exitEditMode">Done</button>
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
import InputText from "primevue/inputtext";
import InputNumber from "primevue/inputnumber";

export default {
  components: {
    ChemFormulaInput,
    ChemicalFormula,
    GHSHazardInformation,
    GHSHazardPictograms,
    OnClickOutside,
    InputText,
    InputNumber,
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
      if (this.inchi_key) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/${encodeURIComponent(this.inchi_key)}/PNG?image_size=200x200`;
      }
      if (this.inchi) {
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
      return getPictogramsFromHazardInformation(this.GHS_codes).size > 0;
    },
  },
  watch: {
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
  background-color: var(--color-accent-light, #f8f9fa);
}

.header-icon {
  color: var(--color-accent, #004175);
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
  color: var(--color-text-secondary, grey);
}

/* View mode */
.substance-card {
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 0.375rem;
  padding: 1rem 1.25rem;
  background-color: var(--color-surface, #fff);
  cursor: pointer;
  max-width: 680px;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.substance-card:hover {
  border-color: var(--color-text-muted, #adb5bd);
  box-shadow: var(--shadow-sm, 0 2px 4px rgba(0, 0, 0, 0.05));
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
  width: 120px;
  height: 120px;
  object-fit: contain;
  background-color: var(--color-surface, white);
  border: 1px solid var(--color-border, #e9ecef);
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

.ghs-item :deep(.ghs-icon) {
  width: 2.5rem;
  height: 2.5rem;
  margin-right: 4px;
}

.substance-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  color: var(--color-text-muted, #6c757d);
}

.display-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6c757d);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.125rem;
}

.formula-value {
  font-size: 1.25rem;
  font-weight: 500;
}

.info-value {
  font-size: 1.25rem;
}

/* Edit mode */
.substance-edit-form {
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 0.375rem;
  padding: 1rem;
  background-color: var(--color-surface, #fff);
}

.edit-layout {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.edit-fields {
  flex: 1;
  min-width: 0;
}

.edit-structure {
  flex-shrink: 0;
  width: 160px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.molecule-image-container {
  background-color: var(--color-surface, white);
  border: 1px solid var(--color-border, #ced4da);
  border-radius: 0.25rem;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.molecule-image {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.molecule-image-error {
  color: var(--color-text-muted, #6c757d);
  font-size: 0.875rem;
  font-style: italic;
  text-align: center;
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}
</style>
