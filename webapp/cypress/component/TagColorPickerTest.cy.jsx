import TagColorPicker from "@/components/TagColorPicker.vue";
import { TAG_COLOR_PALETTE } from "@/resources.js";

describe("TagColorPicker.vue", () => {
  it("renders the preset palette", () => {
    cy.mount(TagColorPicker, { props: { modelValue: null } });
    cy.get(".swatch").should("have.length", TAG_COLOR_PALETTE.length);
  });

  it("emits the chosen preset color", () => {
    cy.mount(TagColorPicker, {
      props: { modelValue: null, "onUpdate:modelValue": cy.spy().as("update") },
    });
    const color = TAG_COLOR_PALETTE[0];
    cy.get(`.swatch[title="${color}"]`).click();
    cy.get("@update").should("have.been.calledWith", color);
  });

  it("marks the active preset as selected", () => {
    const color = TAG_COLOR_PALETTE[1];
    cy.mount(TagColorPicker, { props: { modelValue: color } });
    cy.get(`.swatch[title="${color}"]`).should("have.class", "selected");
  });

  it("emits a custom color from the native picker", () => {
    cy.mount(TagColorPicker, {
      props: { modelValue: null, "onUpdate:modelValue": cy.spy().as("update") },
    });
    // The native color input normalises to a lowercase 6-digit hex.
    cy.get('input[type="color"]').invoke("val", "#123456").trigger("input");
    cy.get("@update").should("have.been.calledWith", "#123456");
  });
});
