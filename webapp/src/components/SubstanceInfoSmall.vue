<template>
  <div v-if="hasAnyData" class="substance-small">
    <div class="substance-small-info">
      <div v-if="chemform" class="substance-small-row">
        <span class="small-label">Formula</span>
        <ChemicalFormula :formula="chemform" :hover="false" class="small-formula" />
      </div>
      <div v-if="molarMass" class="substance-small-row">
        <span class="small-label">Mass</span>
        <span class="small-value"
          >{{
            Number.isFinite(Number(molarMass)) ? Number(molarMass).toFixed(2) : molarMass
          }}
          g/mol</span
        >
      </div>
      <div v-if="ghsCodes && hasPictograms" class="substance-small-row">
        <span class="small-label">Hazards</span>
        <GHSHazardPictograms :model-value="ghsCodes" class="small-pictograms" />
      </div>
      <div v-if="hasStructureIdentifier" class="substance-small-row">
        <span class="small-label">{{ structureIdentifier.label }}</span>
        <span class="structure-value">
          <span class="identifier-text" :title="structureIdentifier.value">{{
            structureIdentifier.value
          }}</span>
          <button
            type="button"
            class="icon-button"
            :title="copiedField === 'structure' ? 'Copied!' : 'Copy'"
            @click="copyToClipboard(structureIdentifier.value, 'structure')"
          >
            <font-awesome-icon :icon="copiedField === 'structure' ? 'check' : 'copy'" />
          </button>
          <a
            :href="pubchemSearchUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="icon-button"
            title="Search on PubChem"
          >
            <font-awesome-icon icon="search" />
          </a>
        </span>
      </div>
      <div v-if="cas" class="substance-small-row">
        <span class="small-label">CAS</span>
        <span class="structure-value">
          <span class="identifier-text">{{ cas }}</span>
          <button
            type="button"
            class="icon-button"
            :title="copiedField === 'cas' ? 'Copied!' : 'Copy'"
            @click="copyToClipboard(cas, 'cas')"
          >
            <font-awesome-icon :icon="copiedField === 'cas' ? 'check' : 'copy'" />
          </button>
          <a
            :href="casSearchUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="icon-button"
            title="Search on CAS Common Chemistry"
          >
            <font-awesome-icon icon="search" />
          </a>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import ChemicalFormula from "@/components/ChemicalFormula";
import GHSHazardPictograms from "@/components/GHSHazardPictograms.vue";
import { getPictogramsFromHazardInformation } from "@/resources.js";

export default {
  components: {
    ChemicalFormula,
    GHSHazardPictograms,
  },
  props: {
    chemform: { type: String, default: null },
    smiles: { type: String, default: null },
    inchi: { type: String, default: null },
    inchiKey: { type: String, default: null },
    ghsCodes: { type: String, default: null },
    molarMass: { type: [Number, String], default: null },
    cas: { type: String, default: null },
  },
  data() {
    return {
      copiedField: null,
      copiedTimeout: null,
    };
  },
  computed: {
    hasAnyData() {
      return !!(
        this.chemform ||
        this.smiles ||
        this.inchi ||
        this.inchiKey ||
        this.ghsCodes ||
        this.molarMass ||
        this.cas
      );
    },
    hasStructureIdentifier() {
      return !!(this.inchiKey || this.inchi || this.smiles);
    },
    structureIdentifier() {
      if (this.smiles) return { label: "SMILES", value: this.smiles };
      if (this.inchiKey) return { label: "InChIKey", value: this.inchiKey };
      if (this.inchi) return { label: "InChI", value: this.inchi };
      return { label: "", value: "" };
    },
    pubchemSearchUrl() {
      const query = this.inchiKey || this.smiles || this.inchi;
      if (!query) return null;
      return `https://pubchem.ncbi.nlm.nih.gov/#query=${encodeURIComponent(query)}`;
    },
    casSearchUrl() {
      if (!this.cas) return null;
      return `https://commonchemistry.cas.org/detail?cas_rn=${encodeURIComponent(this.cas)}`;
    },
    hasPictograms() {
      if (!this.ghsCodes) return false;
      return getPictogramsFromHazardInformation(this.ghsCodes).size > 0;
    },
  },
  methods: {
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
.substance-small {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  padding: 0.375rem 0;
  min-width: 280px;
}

.substance-small-info {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex: 1;
  min-width: 0;
}

.substance-small-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.small-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6c757d);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.small-formula {
  font-size: 1.1rem;
  font-weight: 500;
}

.small-value {
  font-size: 1rem;
}

.small-pictograms :deep(.ghs-display) {
  margin: 0;
}

.small-pictograms :deep(.ghs-icon) {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  max-width: none;
  margin-right: 4px;
}

.structure-value {
  display: inline-flex;
  align-items: baseline;
  gap: 0.4rem;
  min-width: 0;
  max-width: 100%;
}

.identifier-text {
  font-family: var(--font-monospace, monospace);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.pubchem-link {
  color: var(--color-accent, #004175);
  text-decoration: none;
  flex-shrink: 0;
}

.pubchem-link:hover {
  color: var(--color-text-secondary, #6c757d);
}
</style>
