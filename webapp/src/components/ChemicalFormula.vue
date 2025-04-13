<template>
  <span>
    {{ chemFormulaFormat }}
  </span>
</template>

<script>
export default {
  props: {
    formula: {
      type: String,
      default: null,
    },
  },
  computed: {
    chemFormulaFormat() {
      // Need to capture several groups, if the overall format doesn't apply, then
      // there should be no additional formatting whatsoever
      //
      // Some rules:
      //
      // * numbers between element symbols need to be subscripted, including "." and variables like "x"
      //    - e.g., Na3P => Na<sub>3</sub>P, Na3+xP => Na<sub>3+x</sub>P
      // * charges need to be handled separately and superscripted
      //    - e.g., Na+Cl- => Na<sup>+</sup>Cl<sup>-</sup>
      // * empirical labels for formula units like [pyr] must be left alone
      // * dots, when not used within numbers, must be treated as an interpunct "dot product" style dot
      //     - e.g., Cu2SO4.H2O => Cu<sub>2</sub>SO<sub>4</sub> · H<sub>2</sub>O
      if (!this.formula) {
        return this.formula;
      }
      // Optimistically subscript all numbers in formula if it matches
      // regexp for element symbols, brackets and numbers only
      const chemicalFormulaRegex = /[A-Z][a-z]{0,2}(?:\d*(?:\.\d+)?)?|[([{]|[)]}]/g;
      if (this.formula.match(chemicalFormulaRegex)) {
        // Do stuff
      }

      return this.formula;
    },
  },
};
</script>
