const ELEMENT_SYMBOLS = [
  "H",
  "He",
  "Li",
  "Be",
  "B",
  "C",
  "N",
  "O",
  "F",
  "Ne",
  "Na",
  "Mg",
  "Al",
  "Si",
  "P",
  "S",
  "Cl",
  "Ar",
  "K",
  "Ca",
  "Sc",
  "Ti",
  "V",
  "Cr",
  "Mn",
  "Fe",
  "Co",
  "Ni",
  "Cu",
  "Zn",
  "Ga",
  "Ge",
  "As",
  "Se",
  "Br",
  "Kr",
  "Rb",
  "Sr",
  "Y",
  "Zr",
  "Nb",
  "Mo",
  "Tc",
  "Ru",
  "Rh",
  "Pd",
  "Ag",
  "Cd",
  "In",
  "Sn",
  "Sb",
  "Te",
  "I",
  "Xe",
  "Cs",
  "Ba",
  "La",
  "Ce",
  "Pr",
  "Nd",
  "Pm",
  "Sm",
  "Eu",
  "Gd",
  "Tb",
  "Dy",
  "Ho",
  "Er",
  "Tm",
  "Yb",
  "Lu",
  "Hf",
  "Ta",
  "W",
  "Re",
  "Os",
  "Ir",
  "Pt",
  "Au",
  "Hg",
  "Tl",
  "Pb",
  "Bi",
  "Po",
  "At",
  "Rn",
  "Fr",
  "Ra",
  "Ac",
  "Th",
  "Pa",
  "U",
  "Np",
  "Pu",
  "Am",
  "Cm",
  "Bk",
  "Cf",
  "Es",
  "Fm",
  "Md",
  "No",
  "Lr",
  "Rf",
  "Db",
  "Sg",
  "Bh",
  "Hs",
  "Mt",
  "Ds",
  "Rg",
  "Cn",
  "Nh",
  "Fl",
  "Mc",
  "Lv",
  "Ts",
  "Og",
];

const GREEK_LETTERS = {
  α: "&alpha;",
  β: "&beta;",
  γ: "&gamma;",
  δ: "&delta;",
  ε: "&epsilon;",
  ζ: "&zeta;",
  η: "&eta;",
  θ: "&theta;",
  ι: "&iota;",
  κ: "&kappa;",
  λ: "&lambda;",
  μ: "&mu;",
  ν: "&nu;",
  ξ: "&xi;",
  ο: "&omicron;",
  π: "&pi;",
  ρ: "&rho;",
  σ: "&sigma;",
  τ: "&tau;",
  υ: "&upsilon;",
  φ: "&phi;",
  χ: "&chi;",
  ψ: "&psi;",
  ω: "&omega;",
  Α: "&Alpha;",
  Β: "&Beta;",
  Γ: "&Gamma;",
  Δ: "&Delta;",
  Ε: "&Epsilon;",
  Ζ: "&Zeta;",
  Η: "&Eta;",
  Θ: "&Theta;",
  Ι: "&Iota;",
  Κ: "&Kappa;",
  Λ: "&Lambda;",
  Μ: "&Mu;",
  Ν: "&Nu;",
  Ξ: "&Xi;",
  Ο: "&Omicron;",
  Π: "&Pi;",
  Ρ: "&Rho;",
  Σ: "&Sigma;",
  Τ: "&Tau;",
  Υ: "&Upsilon;",
  Φ: "&Phi;",
  Χ: "&Chi;",
  Ψ: "&Psi;",
  Ω: "&Omega;",
};

/**
 * Check if a string contains only valid chemical elements
 * @param {string} formula - The chemical formula to validate
 * @returns {boolean} - True if formula contains only valid elements
 */
export function isValidChemicalFormula(formula) {
  if (!formula) return false;

  if (formula.includes("[") && formula.includes("]")) {
    const empiricalPattern = /\[[^\]]+\]/g;
    const withoutEmpirical = formula.replace(empiricalPattern, "");
    if (withoutEmpirical.trim() === "") return true;
  }

  const elementPattern = new RegExp(`(${ELEMENT_SYMBOLS.join("|")})`, "g");
  const elements = formula.match(elementPattern);

  return elements && elements.length > 0;
}

/**
 * Convert Greek letters to HTML entities
 * @param {string} formula - Formula that may contain Greek letters
 * @returns {string} - Formula with Greek letters converted to HTML entities
 */
export function convertGreekLetters(formula) {
  let result = formula;
  for (const [greek, html] of Object.entries(GREEK_LETTERS)) {
    result = result.replace(new RegExp(greek, "g"), html);
  }
  return result;
}

/**
 * Main function to format chemical formulas with subscripts, superscripts, and special characters
 * @param {string} formula - The raw chemical formula string
 * @returns {string} - HTML-formatted chemical formula
 */
export function formatChemicalFormula(formula) {
  if (!formula || typeof formula !== "string") {
    return formula;
  }

  try {
    let formattedFormula = formula.trim();

    formattedFormula = convertGreekLetters(formattedFormula);

    const empiricalUnits = [];
    const empiricalPattern = /\[[^\]]+\]/g;
    formattedFormula = formattedFormula.replace(empiricalPattern, (match) => {
      const placeholder = `__EMPIRICAL_${empiricalUnits.length}__`;
      empiricalUnits.push(match);
      return placeholder;
    });

    const chargePattern = /([A-Z][a-z]?|\))(\d*)([+-]{1,4})/g;
    formattedFormula = formattedFormula.replace(chargePattern, (match, element, count, charge) => {
      let result = element;
      if (count) {
        result += `<sub>${count}</sub>`;
      }

      const chargeCount = charge.length > 1 ? charge.length : "";
      const chargeSymbol = charge.charAt(0);
      result += `<sup>${chargeCount}${chargeSymbol}</sup>`;
      return result;
    });

    formattedFormula = formattedFormula.replace(/(?<!\d)\.(?!\d)/g, "·");

    const subscriptPattern =
      /([A-Z][a-z]?|\))(\d+\.?\d*[+-]?[xyz]?|\d*\.?\d+[+-]?[xyz]?|[xyz]\d*|[xyz])/g;

    formattedFormula = formattedFormula.replace(subscriptPattern, (match, element, subscript) => {
      if (match.includes("<") || match.includes(">")) {
        return match;
      }

      if (subscript && subscript.trim() !== "") {
        return `${element}<sub>${subscript}</sub>`;
      }
      return match;
    });

    const parenthesesPattern = /\(([^)]+)\)(\d+[+-]?[xyz]?|\d*[+-]?[xyz])/g;
    formattedFormula = formattedFormula.replace(parenthesesPattern, (match, content, subscript) => {
      return `(${content})<sub>${subscript}</sub>`;
    });

    empiricalUnits.forEach((unit, index) => {
      const placeholder = `__EMPIRICAL_${index}__`;
      formattedFormula = formattedFormula.replace(placeholder, unit);
    });

    formattedFormula = formattedFormula
      .replace(/<sub><sub>/g, "<sub>")
      .replace(/<\/sub><\/sub>/g, "</sub>")
      .replace(/<sup><sup>/g, "<sup>")
      .replace(/<\/sup><\/sup>/g, "</sup>")
      .replace(/<sub><\/sub>/g, "")
      .replace(/<sup><\/sup>/g, "");

    return formattedFormula;
  } catch (error) {
    console.warn("Error formatting chemical formula:", error);
    return formula; // Return original formula if formatting fails
  }
}

/**
 * Validate and format a chemical formula
 * @param {string} formula - The chemical formula to validate and format
 * @returns {Object} - {isValid: boolean, formatted: string, original: string}
 */
export function validateAndFormatChemicalFormula(formula) {
  const original = formula;
  const isValid = isValidChemicalFormula(formula);
  const formatted = isValid ? formatChemicalFormula(formula) : formula;

  return {
    isValid,
    formatted,
    original,
  };
}
