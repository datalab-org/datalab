import LocationInput from "@/components/LocationInput.vue";
import PrimeVue from "primevue/config";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faChevronRight, faTimes } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faChevronRight, faTimes);

// The suggestions this component receives are the `flat_locations` returned by
// `GET /locations` (via the `locations_list` Vuex state), i.e. a flat list of
// ' > '-delimited paths.
const SUGGESTIONS = [
  "Lab A > Fridge 1 > Shelf 2",
  "Lab A > Fridge 1 > Shelf 3",
  "Lab A > Glovebox",
  "Lab B > Fridge 1",
  "Store room",
];

function mountLocationInput(props = {}) {
  return cy.mount(LocationInput, {
    props,
    global: {
      plugins: [PrimeVue],
      components: { "font-awesome-icon": FontAwesomeIcon },
    },
  });
}

describe("LocationInput display mode", () => {
  it("shows a placeholder when no location is set", () => {
    mountLocationInput({ modelValue: "" });
    cy.get(".location-display .placeholder-text").should("contain.text", "Add location");
  });

  it("shows the current location and applies the inputId", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox", inputId: "samp-location" });
    cy.get("#samp-location").should("contain.text", "Lab A > Glovebox");
  });

  it("enters edit mode on click", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox" });
    cy.get(".location-display").click();
    cy.get(".location-inline").should("exist");
  });

  it("enters edit mode on enter keypress", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox" });
    cy.get(".location-display").focus().type("{enter}");
    cy.get(".location-inline").should("exist");
  });

  it("does not enter edit mode when readonly", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox", readonly: true });
    cy.get(".location-display").should("have.class", "location-display--readonly");
    cy.get(".location-display").click();
    cy.get(".location-inline").should("not.exist");
  });
});

describe("LocationInput segment editing", () => {
  it("splits an existing location into one input per segment", () => {
    mountLocationInput({ modelValue: "Lab A > Fridge 1 > Shelf 2" });
    cy.get(".location-display").click();

    cy.get(".location-segment-input").should("have.length", 3);
    cy.get(".location-segment-input").eq(0).should("have.value", "Lab A");
    cy.get(".location-segment-input").eq(1).should("have.value", "Fridge 1");
    cy.get(".location-segment-input").eq(2).should("have.value", "Shelf 2");

    // one chevron between each pair of segments
    cy.get(".location-chevron").should("have.length", 2);
  });

  it("renders a single empty input for an empty location", () => {
    mountLocationInput({ modelValue: "" });
    cy.get(".location-display").click();
    cy.get(".location-segment-input").should("have.length", 1).and("have.value", "");
    cy.get(".remove-btn").should("not.exist");
  });

  it("emits the ' > '-joined value when a segment is edited", () => {
    const onUpdate = cy.spy().as("updateSpy");
    mountLocationInput({ modelValue: "Lab A > Glovebox", "onUpdate:modelValue": onUpdate });

    cy.get(".location-display").click();
    cy.get(".location-segment-input").eq(1).clear().type("Fridge 1");

    cy.get("@updateSpy").should("have.been.calledWith", "Lab A > Fridge 1");
  });

  it("adds a new segment and includes it in the emitted value", () => {
    const onUpdate = cy.spy().as("updateSpy");
    mountLocationInput({ modelValue: "Lab A", "onUpdate:modelValue": onUpdate });

    cy.get(".location-display").click();
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").should("have.length", 2);

    cy.get(".location-segment-input").eq(1).type("Glovebox");
    cy.get("@updateSpy").should("have.been.calledWith", "Lab A > Glovebox");
  });

  it("removes a segment and emits the shortened value", () => {
    const onUpdate = cy.spy().as("updateSpy");
    mountLocationInput({
      modelValue: "Lab A > Fridge 1 > Shelf 2",
      "onUpdate:modelValue": onUpdate,
    });

    cy.get(".location-display").click();
    cy.get(".remove-btn").eq(2).click();

    cy.get("@updateSpy").should("have.been.calledWith", "Lab A > Fridge 1");
  });

  it("emits an empty value when the last filled segment is removed", () => {
    const onUpdate = cy.spy().as("updateSpy");
    mountLocationInput({ modelValue: "Lab A", "onUpdate:modelValue": onUpdate });

    cy.get(".location-display").click();
    // a lone segment offers no remove button, so add a second one first
    cy.get(".add-btn").click();
    cy.get(".remove-btn").eq(0).click();

    cy.get("@updateSpy").should("have.been.calledWith", "");
  });

  it("leaves edit mode when a segment is removed, since the clicked button is unmounted", () => {
    mountLocationInput({ modelValue: "Lab A > Fridge 1 > Shelf 2" });

    cy.get(".location-display").click();
    cy.get(".remove-btn").eq(2).click();

    // focusout fires with no surviving focus target inside the component
    cy.get(".location-inline").should("not.exist");
    cy.get(".location-display").should("exist");
  });
});

describe("LocationInput suggestions", () => {
  beforeEach(() => {
    mountLocationInput({ modelValue: "", suggestions: SUGGESTIONS });
    cy.get(".location-display").click();
  });

  it("suggests the distinct top-level locations for the first segment", () => {
    cy.get(".location-segment-input").eq(0).type("La");
    cy.get(".p-autocomplete-option").should("have.length", 2);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Lab A");
    cy.get(".p-autocomplete-option").eq(1).should("have.text", "Lab B");
  });

  it("filters suggestions by the typed query", () => {
    cy.get(".location-segment-input").eq(0).type("store");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Store room");
  });

  it("restricts later segments to children of the chosen parent", () => {
    cy.get(".location-segment-input").eq(0).type("Lab A");
    cy.get(".p-autocomplete-option").first().click();

    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}F");

    // only 'Fridge 1' sits under 'Lab A'; 'Lab B > Fridge 1' must not leak in
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Fridge 1");
  });

  it("deduplicates repeated segment names across sibling paths", () => {
    cy.get(".location-segment-input").eq(0).type("Lab A");
    cy.get(".p-autocomplete-option").first().click();
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}Fridge 1");
    cy.get(".p-autocomplete-option").first().click();

    // 'Shelf 2' and 'Shelf 3' both hang off 'Lab A > Fridge 1'
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(2).type("{selectall}{backspace}Shelf");
    cy.get(".p-autocomplete-option").should("have.length", 2);
  });

  it("offers no child suggestions for a leaf location", () => {
    cy.get(".location-segment-input").eq(0).type("Store room");
    cy.get(".p-autocomplete-option").first().click();
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}a");
    cy.get(".p-autocomplete-option").should("not.exist");
  });
});
