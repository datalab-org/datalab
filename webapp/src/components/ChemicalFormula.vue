<template>
  <span v-html="chemFormulaFormat"></span>
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
      // From an LLM, needs checking...
      const elementSymbols =
        "H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og";
      // Create a regex that matches either element symbols or sequences of digits/periods
      const chemicalFormulaRegexFull = new RegExp(`^(${elementSymbols})|(\\d+\\.?\\d*)+$`, "g");
      const chemicalFormulaRegex = new RegExp(`(${elementSymbols})|(\\d+\\.?\\d*)`, "g");

      if (this.formula.matchAll(chemicalFormulaRegexFull)) {
        return this.formula.replace(chemicalFormulaRegex, (match, element, number) => {
          if (element) {
            // If it's an element, return it unchanged
            return element;
          } else if (number) {
            // If it's a number or period, wrap in subscript tags
            return `<sub>${number}</sub>`;
          }
          return match;
        });
      }

      return this.formula;
    },
  },
};
</script>
