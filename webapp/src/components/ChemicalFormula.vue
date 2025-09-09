<template>
  <!-- eslint-disable-next-line  -->
  <span v-html="chemFormulaFormat"></span>
</template>

<script>
import { formatChemicalFormula } from "@/utils/chemicalFormulaFormatter.js";

export default {
  props: {
    formula: {
      type: String,
      default: null,
    },
  },
  computed: {
    chemFormulaFormat() {
      return formatChemicalFormula(this.formula);
    },
  },
};
</script>
