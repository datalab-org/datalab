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

      const greekLetters =
        "α|β|γ|δ|ε|ζ|η|θ|ι|κ|λ|μ|ν|ξ|ο|π|ρ|σ|τ|υ|φ|χ|ψ|ω|Α|Β|Γ|Δ|Ε|Ζ|Η|Θ|Ι|Κ|Λ|Μ|Ν|Ξ|Ο|Π|Ρ|Σ|Τ|Υ|Φ|Χ|Ψ|Ω";
      const specialChars = "′|″|‴|⁰|¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|∙|•|×|·|∗|∞";

      // Create a regex that matches either element symbols or sequences of digits/periods
      const validFormulaRegex = new RegExp(
        `^[A-Za-z0-9.+x()\\[\\]\\s${greekLetters.replace(/\|/g, "")}${specialChars.replace(
          /\|/g,
          "",
        )}-]+$`,
        "u",
      );

      const isValidFormula = validFormulaRegex.test(this.formula);

      if (!isValidFormula) {
        return this.formula;
      }

      let formatted = this.formula;

      formatted = formatted.replace(/\.(?=\s*[A-Z([∙•])/g, " · ");

      formatted = formatted.replace(/[∙•]/g, " · ");

      formatted = formatted.replace(/\[([^\]]+)\](\d+)/g, (match, content, number) => {
        return `<span data-bracket>${content}</span><span data-number>${number}</span>`;
      });

      formatted = formatted.replace(/([A-Z][a-z]?)(\d+)([+-])(?=\s|$|[A-Z])/g, "$1<sup>$2$3</sup>");

      formatted = formatted.replace(/([A-Z][a-z]?)([+-])(?=\s|$|[A-Z])/g, "$1<sup>$2</sup>");

      formatted = formatted.replace(
        new RegExp(`(${elementSymbols})(\\d+\\.?\\d*[+xyzn-]*)`, "g"),
        (match, element, number) => {
          if (number && !number.match(/^[+-]$/)) {
            return `${element}<sub>${number}</sub>`;
          }
          return match;
        },
      );

      formatted = formatted.replace(/\)(\d+\.?\d*)/g, ")<sub>$1</sub>");

      formatted = formatted.replace(
        /<span data-bracket>([^<]+)<\/span><span data-number>(\d+)<\/span>/g,
        "[$1]<sub>$2</sub>",
      );

      return formatted;
    },
  },
};
</script>
