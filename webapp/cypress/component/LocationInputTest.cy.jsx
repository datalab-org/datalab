import LocationInput from "@/components/LocationInput.vue";
import PrimeVue from "primevue/config";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faChevronRight, faTimes } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faChevronRight, faTimes);

// The tree this component receives is the `nested_locations` returned by
// `GET /locations` (via the `locations_list` Vuex state), i.e. the flat
// locations 'Lab A > Fridge 1 > Shelf 2', 'Lab A > Fridge 1 > Shelf 3',
// 'Lab A > Glovebox', 'Lab B > Fridge 1' and 'Store room'.
const HIERARCHY = {
  "Lab A": {
    "Fridge 1": { "Shelf 2": {}, "Shelf 3": {} },
    Glovebox: {},
  },
  "Lab B": { "Fridge 1": {} },
  "Store room": {},
};

function mountLocationInput(props = {}) {
  return cy.mount(LocationInput, {
    props,
    global: {
      plugins: [PrimeVue],
      components: { "font-awesome-icon": FontAwesomeIcon },
    },
  });
}

function selectOption(text) {
  // the option list is shown on focus and re-filtered as you type, so match on
  // the text rather than a position that a pending re-render could shift
  cy.contains(".p-autocomplete-option", new RegExp(`^${text}$`)).click();
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
    mountLocationInput({ modelValue: "", hierarchy: HIERARCHY });
    cy.get(".location-display").click();
  });

  it("shows the top-level options on focus, before anything is typed", () => {
    cy.get(".location-segment-input").eq(0).should("have.focus").and("have.value", "");
    cy.get(".p-autocomplete-option").should("have.length", 3);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Lab A");
    cy.get(".p-autocomplete-option").eq(1).should("have.text", "Lab B");
    cy.get(".p-autocomplete-option").eq(2).should("have.text", "Store room");
  });

  it("filters the options by the typed query", () => {
    cy.get(".location-segment-input").eq(0).type("store");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Store room");
  });

  it("opens the next segment with its options when an option is selected", () => {
    selectOption("Lab A");

    // no '+' click needed: the next level opens itself
    cy.get(".location-segment-input").should("have.length", 2);
    cy.get(".location-segment-input").eq(1).should("have.focus").and("have.value", "");
    cy.get(".p-autocomplete-option").should("have.length", 2);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Fridge 1");
    cy.get(".p-autocomplete-option").eq(1).should("have.text", "Glovebox");
  });

  it("steps down level by level as options are selected", () => {
    selectOption("Lab A");
    selectOption("Fridge 1");

    cy.get(".location-segment-input").should("have.length", 3);
    cy.get(".location-segment-input").eq(2).should("have.focus");
    cy.get(".p-autocomplete-option").should("have.length", 2);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Shelf 2");
    cy.get(".p-autocomplete-option").eq(1).should("have.text", "Shelf 3");
  });

  it("does not open a further segment when a leaf is selected", () => {
    selectOption("Store room");

    cy.get(".location-segment-input").should("have.length", 1).and("have.value", "Store room");
    cy.get(".location-inline").should("exist");
  });

  it("restricts later segments to children of the chosen parent", () => {
    selectOption("Lab A");
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}F");

    // only 'Fridge 1' sits under 'Lab A'; 'Lab B > Fridge 1' must not leak in
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Fridge 1");
  });

  it("offers no child options for a leaf location", () => {
    selectOption("Store room");
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}a");
    cy.get(".p-autocomplete-option").should("not.exist");
  });

  it("offers nothing below a segment that is not in the hierarchy", () => {
    cy.get(".location-segment-input").eq(0).type("Somewhere new");
    cy.get(".add-btn").click();
    cy.get(".location-segment-input").eq(1).type("{selectall}{backspace}a");
    cy.get(".p-autocomplete-option").should("not.exist");
  });

  it("drops deeper segments that do not exist under a newly chosen parent", () => {
    selectOption("Lab A");
    selectOption("Glovebox");
    cy.get(".location-segment-input").eq(0).should("have.value", "Lab A");
    cy.get(".location-segment-input").eq(1).should("have.value", "Glovebox");

    // 'Lab B' has no 'Glovebox', so the stale child must not survive the switch
    cy.get(".location-segment-input").eq(0).type("{selectall}{backspace}Lab B");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").first().click();

    cy.get(".location-segment-input").eq(0).should("have.value", "Lab B");
    cy.get(".location-segment-input").eq(1).should("have.value", "");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").first().should("have.text", "Fridge 1");
  });

  it("keeps deeper segments that are still valid under the new parent", () => {
    selectOption("Lab A");
    selectOption("Fridge 1");
    selectOption("Shelf 2");
    cy.get(".location-segment-input").should("have.length", 3);

    // 'Lab B' also has a 'Fridge 1', so that level survives the switch, but it
    // has no 'Shelf 2' below it, so only the deepest segment is dropped
    cy.get(".location-segment-input").eq(0).type("{selectall}{backspace}Lab B");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").first().click();

    cy.get(".location-segment-input").should("have.length", 2);
    cy.get(".location-segment-input").eq(0).should("have.value", "Lab B");
    cy.get(".location-segment-input").eq(1).should("have.value", "Fridge 1");
  });

  it("shows the children of a typed parent as soon as a segment is added", () => {
    // typing the parent rather than picking it, so '+' is still needed
    cy.get(".location-segment-input").eq(0).type("Lab A");
    cy.get(".add-btn").click();

    cy.get(".location-segment-input").eq(1).should("have.focus");
    cy.get(".p-autocomplete-option").should("have.length", 2);
    cy.get(".p-autocomplete-option").eq(0).should("have.text", "Fridge 1");
    cy.get(".p-autocomplete-option").eq(1).should("have.text", "Glovebox");
  });
});

describe("LocationInput accessibility", () => {
  it("names the collapsed control from the external label", () => {
    mountLocationInput({ modelValue: "Lab A", labelledBy: "samp-location-label" });
    cy.get(".location-display")
      .should("have.attr", "role", "button")
      .and("have.attr", "aria-labelledby", "samp-location-label");
  });

  it("does not present a readonly control as a button", () => {
    mountLocationInput({ modelValue: "Lab A", readonly: true });
    cy.get(".location-display").should("not.have.attr", "role");
  });

  it("names the editing row and each of its segments", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox", labelledBy: "samp-location-label" });
    cy.get(".location-display").click();

    cy.get(".location-inline")
      .should("have.attr", "role", "group")
      .and("have.attr", "aria-labelledby", "samp-location-label");
    cy.get(".location-segment-input").eq(0).should("have.attr", "aria-label", "Location level 1");
    cy.get(".location-segment-input").eq(1).should("have.attr", "aria-label", "Location level 2");
  });

  it("gives the icon-only buttons accessible names", () => {
    mountLocationInput({ modelValue: "Lab A > Glovebox" });
    cy.get(".location-display").click();

    cy.get(".remove-btn").eq(1).should("have.attr", "aria-label", "Remove location level 2");
    cy.get(".add-btn").should("have.attr", "aria-label", "Add location level");
  });
});

describe("LocationInput hierarchy pruning", () => {
  it("emits the pruned value when a stale child is dropped", () => {
    const onUpdate = cy.spy().as("pruneSpy");
    mountLocationInput({ modelValue: "", hierarchy: HIERARCHY, "onUpdate:modelValue": onUpdate });
    cy.get(".location-display").click();

    selectOption("Lab A");
    selectOption("Glovebox");
    cy.get("@pruneSpy").should("have.been.calledWith", "Lab A > Glovebox");

    cy.get(".location-segment-input").eq(0).type("{selectall}{backspace}Lab B");
    cy.get(".p-autocomplete-option").should("have.length", 1);
    cy.get(".p-autocomplete-option").first().click();

    cy.get("@pruneSpy").should("have.been.calledWith", "Lab B");
  });
});
