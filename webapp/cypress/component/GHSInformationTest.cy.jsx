import { getPictogramsFromHazardCode, getHCodesFromHazardStatement } from "@/resources.js";

describe("test hazard pictograms", () => {
  const f = getPictogramsFromHazardCode;

  // Parsed from https://pubchem.ncbi.nlm.nih.gov/ghs/ghscode_10.txt
  const ghs_parsed = {
    200: "GHS01",
    201: "GHS01",
    202: "GHS01",
    203: "GHS01",
    204: "GHS01,GHS07",
    205: "GHS02",
    206: "GHS02",
    207: "GHS02",
    208: "GHS02",
    209: "GHS01",
    210: "GHS01",
    211: "GHS01",
    220: "GHS02",
    221: "GHS02",
    222: "GHS02",
    223: "GHS02",
    224: "GHS02",
    225: "GHS02",
    226: "GHS02",
    227: NaN,
    228: "GHS02",
    229: "GHS02",
    230: "GHS02",
    231: "GHS02",
    232: "GHS02",
    240: "GHS01",
    241: "GHS01,GHS02",
    242: "GHS02",
    250: "GHS02",
    251: "GHS02",
    252: "GHS02",
    260: "GHS02",
    261: "GHS02",
    270: "GHS03",
    271: "GHS03",
    272: "GHS03",
    280: "GHS04",
    281: "GHS04",
    282: "GHS02,GHS04",
    283: "GHS02,GHS04",
    284: "GHS04",
    290: "GHS05",
    300: "GHS06",
    301: "GHS06",
    302: "GHS07",
    303: NaN,
    304: "GHS08",
    305: "GHS08",
    310: "GHS06",
    311: "GHS06",
    312: "GHS07",
    313: NaN,
    314: "GHS05",
    315: "GHS07",
    316: NaN,
    317: "GHS07",
    318: "GHS05",
    319: "GHS07",
    320: NaN,
    330: "GHS06",
    331: "GHS06",
    332: "GHS07",
    333: NaN,
    334: "GHS08",
    335: "GHS07",
    336: "GHS07",
    340: "GHS08",
    341: "GHS08",
    350: "GHS08",
    351: "GHS08",
    360: "GHS08",
    361: "GHS08",
    362: NaN,
    370: "GHS08",
    371: "GHS08",
    372: "GHS08",
    373: "GHS08",
    400: "GHS09",
    401: NaN,
    402: NaN,
    410: "GHS09",
    411: "GHS09",
    412: NaN,
    413: NaN,
    420: "GHS07",
  };

  function checkGHS(input, result, expected) {
    // Loop over results Set and extract codes
    let actual = new Set();
    for (const pictogram of result) {
      actual.add(pictogram.code);
    }
    // Check if its a NaN
    let expectedSet = new Set();
    if (!(expected != expected)) {
      expectedSet = new Set(expected.split(","));
    }

    if (actual.size !== expectedSet.size) {
      throw new Error(`Size mismatch: ${actual.size} vs ${expectedSet.size}`);
    }

    let correct = Array.from(actual).every((code) => expectedSet.has(code));
    if (!correct) {
      throw new Error(
        `Incorrect codes: ${Array.from(actual).join(",")} vs ${expectedSet} for ${input}`,
      );
    }

    return correct;
  }

  it("exhaustively correct GHS hazard codes from H-codes", () => {
    // Loop through all hazard codes and check values
    for (const [code, expected] of Object.entries(ghs_parsed)) {
      let result = f(Number(code));
      expect(checkGHS(code, result, expected)).to.be.true;
    }
  });

  it("parses various hazard statement strings into the correct codes", () => {
    let hazard_statements = [
      "H200,H302,H402",
      "H350 H341 H360 H334 H317 H410",
      "European Commission: H225",
      "Australian Department of Health: H319 H315 H360Sigma-Aldrich: H315 H319 H335 H360\nEuropean Chemicals Agency: H315 H319 H335",
      "This stuff is very dangerous",
      "This stuff is very dangerous (H110,H222)",
    ];

    let expected_h_codes = [
      ["H200", "H302", "H402"],
      ["H350", "H341", "H360", "H334", "H317", "H410"],
      ["H225"],
      ["H319", "H315", "H360", "H315", "H319", "H335", "H360", "H315", "H319", "H335"],
      [],
      ["H110", "H222"],
    ];

    for (const i in hazard_statements) {
      const hazard_statement = hazard_statements[i];
      const expected = expected_h_codes[i];
      const result = getHCodesFromHazardStatement(hazard_statement);
      expect(result).to.deep.equal(expected);
    }
  });
});
