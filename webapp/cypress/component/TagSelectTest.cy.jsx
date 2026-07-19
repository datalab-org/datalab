import TagSelect from "@/components/TagSelect.vue";

describe("TagSelect.vue", () => {
  const tag = {
    type: "tags",
    immutable_id: "0123456789ab0123456789ab",
    name: "test-tag",
    description: "reacts with air",
    color: "#f1c40f",
  };

  beforeEach(() => {
    cy.intercept("GET", "**/search-tags*", {
      body: { status: "success", data: [tag] },
    }).as("searchTags");
  });

  it("searches and emits a reference object when a tag is selected", () => {
    cy.mount(TagSelect, {
      props: { modelValue: [], "onUpdate:modelValue": cy.spy().as("update") },
    });

    cy.get(".vs__search").type("test-man");
    cy.wait("@searchTags");
    // The option shows the tag name and a color swatch.
    cy.get(".vs__dropdown-option").contains("test-tag").should("exist");
    cy.get(".vs__dropdown-option .color-swatch").should("exist");
    cy.get(".vs__dropdown-option").contains("test-tag").click();

    // The reference preserves display fields (color/description).
    cy.get("@update").should("have.been.calledWith", [
      {
        type: "tags",
        immutable_id: tag.immutable_id,
        name: "test-tag",
        color: "#f1c40f",
        description: "reacts with air",
      },
    ]);
  });

  it("does not offer to create a tag for a typed value with no match", () => {
    cy.intercept("GET", "**/search-tags*", {
      body: { status: "success", data: [] },
    }).as("searchTagsEmpty");

    cy.mount(TagSelect, {
      props: { modelValue: [], "onUpdate:modelValue": cy.spy().as("update") },
    });

    cy.get(".vs__search").type("brand-new-tag");
    cy.wait("@searchTagsEmpty");
    // A typed value matching no tag is not selectable (no ad-hoc tag creation).
    cy.get(".vs__dropdown-option").should("not.exist");
    cy.get(".vs__no-options").should("contain", "No matching tags");
  });

  it("renders existing reference tags as selected chips", () => {
    cy.mount(TagSelect, {
      props: { modelValue: [tag] },
    });

    cy.get(".vs__selected").should("contain", "test-tag");
  });
});
