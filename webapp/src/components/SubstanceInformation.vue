<template>
  <div id="substance-information" ref="outerdiv" class="data-block" data-testid="substance-block">
    <div
      class="datablock-header"
      :class="{ clickable: !isEditing, expanded: isEditing }"
      @click="!isEditing && enterEditMode()"
    >
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        @click.stop="toggleEditMode"
      />
      <label class="block-title">Substance Information</label>
      <font-awesome-icon v-if="!isEditing" id="edit-icon" class="ml-2" icon="pen" size="xs" />
    </div>

    <!-- VIEW MODE -->
    <div v-if="!isEditing && hasAnyData" class="substance-card" @click="enterEditMode">
      <div class="substance-card-content">
        <div class="substance-display-row">
          <div class="info-items">
            <div v-if="chemform" class="info-item">
              <span class="display-label">Formula</span>
              <ChemicalFormula :formula="chemform" class="formula-value" />
            </div>
            <div v-if="molar_mass" class="info-item">
              <span class="display-label">Molar mass</span>
              <span class="info-value"
                >{{
                  Number.isFinite(Number(molar_mass)) ? Number(molar_mass).toFixed(2) : molar_mass
                }}
                g/mol</span
              >
            </div>
            <div v-if="CAS" class="info-item">
              <span class="display-label">CAS</span>
              <span class="structure-value">
                <span class="identifier-text">{{ CAS }}</span>
                <button
                  type="button"
                  class="icon-button"
                  :title="copiedField === 'cas-view' ? 'Copied!' : 'Copy CAS'"
                  @click.stop="copyToClipboard(CAS, 'cas-view')"
                >
                  <font-awesome-icon :icon="copiedField === 'cas-view' ? 'check' : 'copy'" />
                </button>
                <a
                  :href="casSearchUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="icon-button"
                  title="Search on CAS Common Chemistry"
                  @click.stop
                >
                  <font-awesome-icon icon="search" />
                </a>
              </span>
            </div>
            <div v-if="hasStructureIdentifier" class="info-item structure-item">
              <span class="display-label">{{ structureIdentifier.label }}</span>
              <span class="structure-value">
                <span class="identifier-text" :title="structureIdentifier.value">{{
                  structureIdentifier.value
                }}</span>
                <button
                  type="button"
                  class="icon-button"
                  :title="copiedField === 'structure' ? 'Copied!' : 'Copy'"
                  @click.stop="copyToClipboard(structureIdentifier.value, 'structure')"
                >
                  <font-awesome-icon :icon="copiedField === 'structure' ? 'check' : 'copy'" />
                </button>
                <a
                  :href="pubchemSearchUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="icon-button"
                  title="Search on PubChem"
                  @click.stop
                >
                  <font-awesome-icon icon="search" />
                </a>
              </span>
            </div>
            <div v-if="GHS_codes && hasPictograms" class="info-item ghs-item">
              <span class="display-label">Hazards</span>
              <GHSHazardPictograms :model-value="GHS_codes" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- EDIT MODE -->
    <OnClickOutside v-if="isEditing" :options="{ ignore: [outerDivRef] }" @trigger="exitEditMode">
      <div class="substance-edit-form">
        <div class="form-row">
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-chemform">Chemical formula</label>
            <ChemFormulaInput id="substance-chemform" v-model="chemform" />
          </div>
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-smiles">SMILES</label>
            <div class="input-with-copy">
              <InputText id="substance-smiles" v-model="smiles" fluid class="p-inputtext-sm" />
              <button
                v-if="smiles"
                type="button"
                class="copy-button"
                :title="copiedField === 'smiles' ? 'Copied!' : 'Copy SMILES'"
                @click.stop="copyToClipboard(smiles, 'smiles')"
              >
                <font-awesome-icon :icon="copiedField === 'smiles' ? 'check' : 'copy'" />
              </button>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-inchi">InChI</label>
            <div class="input-with-copy">
              <InputText id="substance-inchi" v-model="inchi" fluid class="p-inputtext-sm" />
              <button
                v-if="inchi"
                type="button"
                class="copy-button"
                :title="copiedField === 'inchi' ? 'Copied!' : 'Copy InChI'"
                @click.stop="copyToClipboard(inchi, 'inchi')"
              >
                <font-awesome-icon :icon="copiedField === 'inchi' ? 'check' : 'copy'" />
              </button>
            </div>
          </div>
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-inchi-key">InChI Key</label>
            <div class="input-with-copy">
              <InputText
                id="substance-inchi-key"
                v-model="inchi_key"
                fluid
                class="p-inputtext-sm"
              />
              <button
                v-if="inchi_key"
                type="button"
                class="copy-button"
                :title="copiedField === 'inchi_key' ? 'Copied!' : 'Copy InChI Key'"
                @click.stop="copyToClipboard(inchi_key, 'inchi_key')"
              >
                <font-awesome-icon :icon="copiedField === 'inchi_key' ? 'check' : 'copy'" />
              </button>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-mass">Molar mass (g/mol)</label>
            <InputNumber
              id="substance-mass"
              v-model="molar_mass"
              fluid
              input-class="p-inputtext-sm"
              style="width: 100%"
            />
          </div>
          <div class="form-group col-sm-6 pr-2">
            <label for="substance-cas">CAS</label>
            <div class="input-with-copy">
              <InputText id="substance-cas" v-model="CAS" fluid class="p-inputtext-sm" />
              <button
                v-if="CAS"
                type="button"
                class="copy-button"
                :title="copiedField === 'cas' ? 'Copied!' : 'Copy CAS'"
                @click.stop="copyToClipboard(CAS, 'cas')"
              >
                <font-awesome-icon :icon="copiedField === 'cas' ? 'check' : 'copy'" />
              </button>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-12 pr-2">
            <GHSHazardInformation v-model="GHS_codes" :editable="true" />
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
      copiedField: null,
      copiedTimeout: null,
    };
  },
  computed: {
    chemform: createComputedSetterForItemField("chemform"),
    smiles: createComputedSetterForItemField("smiles"),
    inchi: createComputedSetterForItemField("inchi"),
    inchi_key: createComputedSetterForItemField("inchi_key"),
    GHS_codes: createComputedSetterForItemField("GHS_codes"),
    molar_mass: createComputedSetterForItemField("molar_mass"),
    CAS: createComputedSetterForItemField("CAS"),

    hasStructureIdentifier() {
      return !!(this.inchi_key || this.inchi || this.smiles);
    },

    structureIdentifier() {
      if (this.inchi_key) return { label: "InChIKey", value: this.inchi_key };
      if (this.smiles) return { label: "SMILES", value: this.smiles };
      if (this.inchi) return { label: "InChI", value: this.inchi };
      return { label: "", value: "" };
    },

    pubchemSearchUrl() {
      const query = this.inchi_key || this.smiles || this.inchi;
      if (!query) return null;
      return `https://pubchem.ncbi.nlm.nih.gov/#query=${encodeURIComponent(query)}`;
    },

    casSearchUrl() {
      if (!this.CAS) return null;
      return `https://commonchemistry.cas.org/detail?cas_rn=${encodeURIComponent(this.CAS)}`;
    },

    hasAnyData() {
      return !!(
        this.chemform ||
        this.smiles ||
        this.inchi ||
        this.inchi_key ||
        this.GHS_codes ||
        this.molar_mass ||
        this.CAS
      );
    },

    hasPictograms() {
      if (!this.GHS_codes) return false;
      return getPictogramsFromHazardInformation(this.GHS_codes).size > 0;
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
    toggleEditMode() {
      this.isEditing = !this.isEditing;
    },
    copyToClipboard(value, fieldName) {
      if (!value) return;
      navigator.clipboard.writeText(value).catch(() => {});
      this.copiedField = fieldName;
      if (this.copiedTimeout) clearTimeout(this.copiedTimeout);
      this.copiedTimeout = setTimeout(() => {
        this.copiedField = null;
      }, 1500);
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

.collapse-arrow {
  font-size: large;
  margin-right: 10px;
  color: var(--color-accent, #004175);
  cursor: pointer;
  transition: transform 0.4s;
}

.datablock-header.expanded .collapse-arrow {
  transform: rotate(90deg);
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
  overflow: hidden;
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

.structure-item {
  flex-basis: 100%;
  min-width: 0;
  overflow: hidden;
}

.ghs-item {
  flex-basis: 100%;
}

.ghs-item :deep(.ghs-display) {
  margin: 0;
}

.ghs-item :deep(.ghs-icon) {
  width: 4rem;
  height: 4rem;
  min-width: 4rem;
  max-width: none;
  margin-right: 6px;
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

.structure-value {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}

.identifier-text {
  font-family: var(--font-monospace, monospace);
  font-size: 0.95rem;
  word-break: break-all;
  min-width: 0;
}

.icon-button {
  color: var(--color-accent, #004175);
  text-decoration: none;
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 0 0.15rem;
  cursor: pointer;
  font-size: inherit;
  line-height: 1;
}

.icon-button:hover {
  color: var(--color-text-secondary, #6c757d);
}

.input-with-copy {
  position: relative;
}

.input-with-copy :deep(.p-inputtext) {
  padding-right: 2rem;
}

.copy-button {
  position: absolute;
  right: 0.25rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 0.25rem;
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  line-height: 1;
}

.copy-button:hover {
  color: var(--color-accent, #004175);
}

/* Edit mode */
.substance-edit-form {
  border: 1px solid var(--color-border, #dee2e6);
  border-radius: 0.375rem;
  padding: 1rem;
  background-color: var(--color-surface, #fff);
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}
</style>
