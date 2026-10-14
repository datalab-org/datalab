import { buildOptimadeFilter, quoteString, toRfc3339 } from "@/utils/optimadeFilter.js";

const fields = [
  { id: "name", value_type: "string" },
  { id: "molar_mass", value_type: "number" },
  { id: "date", value_type: "timestamp" },
  { id: "tags.name", value_type: "string", is_list: true },
];

const rule = (field, operator, value) => ({ kind: "rule", field, operator, value });
const group = (combinator, children, negate = false) => ({
  kind: "group",
  combinator,
  children,
  negate,
});

describe("buildOptimadeFilter", () => {
  it("quotes and escapes string literals", () => {
    expect(quoteString('a "b" \\c')).to.equal('"a \\"b\\" \\\\c"');
    expect(buildOptimadeFilter(rule("name", "CONTAINS", 'say "hi"'), fields)).to.equal(
      'name CONTAINS "say \\"hi\\""',
    );
  });

  it("formats values by property type", () => {
    expect(buildOptimadeFilter(rule("molar_mass", ">=", "12.5"), fields)).to.equal(
      "molar_mass >= 12.5",
    );
    const local = "2026-01-31T12:00";
    expect(buildOptimadeFilter(rule("date", "<", local), fields)).to.equal(
      `date < "${toRfc3339(local)}"`,
    );
    expect(toRfc3339("2026-01-31T12:00:00Z")).to.equal("2026-01-31T12:00:00Z");
  });

  it("supports the OPTIMADE operator forms", () => {
    expect(buildOptimadeFilter(rule("name", "IS UNKNOWN"), fields)).to.equal("name IS UNKNOWN");
    expect(buildOptimadeFilter(rule("name", "STARTS WITH", "Li"), fields)).to.equal(
      'name STARTS WITH "Li"',
    );
    expect(buildOptimadeFilter(rule("tags.name", "HAS ANY", ["a", "b"]), fields)).to.equal(
      'tags.name HAS ANY "a", "b"',
    );
    expect(buildOptimadeFilter(rule("tags.name", "HAS", "a"), fields)).to.equal(
      'tags.name HAS "a"',
    );
    expect(buildOptimadeFilter(rule("tags.name", "LENGTH", 2), fields)).to.equal(
      "tags.name LENGTH 2",
    );
  });

  it("combines groups with explicit parentheses and NOT", () => {
    const tree = group("and", [
      rule("name", "CONTAINS", "LFP"),
      group("or", [rule("molar_mass", ">", 10), rule("name", "IS UNKNOWN")]),
      group("and", [rule("name", "=", "x")], true),
    ]);
    expect(buildOptimadeFilter(tree, fields)).to.equal(
      'name CONTAINS "LFP" AND (molar_mass > 10 OR name IS UNKNOWN) AND (NOT name = "x")',
    );
    expect(
      buildOptimadeFilter(group("or", [rule("name", "=", "a"), rule("name", "=", "b")], true)),
    ).to.equal('NOT (name = "a" OR name = "b")');
  });

  it("returns an empty filter for an empty tree", () => {
    expect(buildOptimadeFilter(group("and", []), fields)).to.equal("");
  });

  it("refuses values that do not fit the property type", () => {
    expect(() => buildOptimadeFilter(rule("molar_mass", ">", "abc"), fields)).to.throw();
    expect(() => buildOptimadeFilter(rule("date", "<", "last week"), fields)).to.throw();
  });
});
