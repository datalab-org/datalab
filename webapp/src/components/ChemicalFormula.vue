<template>
  <span>
    {{ chemFormulaFormat }}
    <!--
    <span v-for="(match, index) in chemFormulaFormat" :key="index">
      {{ match[1] }}<sub v-if="match[2]">{{ match[2] }}</sub>
    </span>
    -->
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
      return this.formula;
      //if (!this.formula) {
      //  return " ";
      //}
      //const re = /([A-Z][a-z]?)(\d+\.?\d*)?/g;
      //var all_matches = [...this.formula.matchAll(re)];
      //return all_matches;
    },
  },
};
</script>
