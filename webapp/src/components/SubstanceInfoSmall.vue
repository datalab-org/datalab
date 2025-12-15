<template>
  <div v-if="hasAnyData" class="substance-small">
    <div v-if="hasStructureIdentifier && !imageError" class="substance-small-image">
      <img
        :src="pubchemImageUrl"
        alt="Molecule structure"
        class="structure-thumbnail"
        @error="imageError = true"
      />
    </div>

    <div class="substance-small-info">
      <div v-if="chemform" class="substance-small-row">
        <span class="small-label">Formula</span>
        <ChemicalFormula :formula="chemform" class="small-formula" />
      </div>
      <div v-if="molarMass" class="substance-small-row">
        <span class="small-label">Mass</span>
        <span class="small-value">{{ molarMass }} g/mol</span>
      </div>
      <div v-if="ghsCodes && hasPictograms" class="substance-small-row">
        <span class="small-label">Hazards</span>
        <GHSHazardPictograms :model-value="ghsCodes" class="small-pictograms" />
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
  },
  data() {
    return {
      imageError: false,
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
        this.molarMass
      );
    },
    hasStructureIdentifier() {
      return !!(this.inchiKey || this.inchi || this.smiles);
    },
    pubchemImageUrl() {
      if (this.inchiKey) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/${encodeURIComponent(this.inchiKey)}/PNG?image_size=200x200`;
      }
      if (this.inchi) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchi/PNG?inchi=${encodeURIComponent(this.inchi)}&image_size=200x200`;
      }
      if (this.smiles) {
        return `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/${encodeURIComponent(this.smiles)}/PNG?image_size=200x200`;
      }
      return null;
    },
    hasPictograms() {
      if (!this.ghsCodes) return false;
      return getPictogramsFromHazardInformation(this.ghsCodes).size > 0;
    },
  },
  watch: {
    inchiKey() {
      this.imageError = false;
    },
    inchi() {
      this.imageError = false;
    },
    smiles() {
      this.imageError = false;
    },
  },
};
</script>

<style scoped>
.substance-small {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
}

.substance-small-image {
  flex-shrink: 0;
}

.structure-thumbnail {
  width: 78px;
  height: 78px;
  object-fit: contain;
  border: 1px solid var(--color-border, #e9ecef);
  border-radius: 0.25rem;
  background-color: var(--color-surface, #fff);
  padding: 2px;
}

.substance-small-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.substance-small-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.375rem;
}

.small-label {
  font-size: 0.65rem;
  color: var(--color-text-secondary, #6c757d);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.small-formula {
  font-size: 0.9rem;
  font-weight: 500;
}

.small-value {
  font-size: 0.85rem;
}

.small-pictograms :deep(.ghs-display) {
  margin: 0;
}

.small-pictograms :deep(.ghs-icon) {
  width: 1.5rem;
  height: 1.5rem;
  margin-right: 2px;
}
</style>
