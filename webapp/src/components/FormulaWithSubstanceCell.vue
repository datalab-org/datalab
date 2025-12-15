<template>
  <div class="formula-cell">
    <span
      v-if="hasData"
      ref="trigger"
      class="substance-icon"
      @mouseenter="$refs.popover.show($event, $refs.trigger)"
      @mouseleave="$refs.popover.hide()"
    >
      <font-awesome-icon icon="vial" class="substance-indicator" />
      <Popover ref="popover" :dismissable="false">
        <SubstanceInfoSmall
          :chemform="chemform"
          :smiles="smiles"
          :inchi-key="inchiKey"
          :ghs-codes="ghsCodes"
          :molar-mass="molarMass"
        />
      </Popover>
    </span>
    <ChemicalFormula v-if="chemform" :formula="chemform" />
  </div>
</template>

<script>
import Popover from "primevue/popover";
import SubstanceInfoSmall from "@/components/SubstanceInfoSmall.vue";
import ChemicalFormula from "@/components/ChemicalFormula";

export default {
  components: { Popover, SubstanceInfoSmall, ChemicalFormula },
  props: {
    chemform: { type: String, default: null },
    smiles: { type: String, default: null },
    inchiKey: { type: String, default: null },
    ghsCodes: { type: String, default: null },
    molarMass: { type: [Number, String], default: null },
  },
  computed: {
    hasData() {
      return !!(this.chemform || this.smiles || this.inchiKey || this.ghsCodes || this.molarMass);
    },
  },
};
</script>

<style scoped>
.formula-cell {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.substance-icon {
  display: inline-flex;
  align-items: center;
}

.substance-indicator {
  color: var(--color-text-muted, #94a3b8);
  cursor: default;
  transition: color 0.15s ease;
}

.substance-indicator:hover {
  color: var(--color-accent, #6366f1);
}
</style>
