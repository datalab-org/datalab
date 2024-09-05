import FormattedItemName from "@/components/FormattedItemName.vue";
import { itemTypes } from "@/resources.js";

function hexToRgb(hex) {
  const bigint = parseInt(hex.replace("#", ""), 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgb(${r}, ${g}, ${b})`;
}

describe("FormattedItemName.vue", () => {
  const item_id = "Test";
  const itemType = ["samples", "cells", "starting_materials", "equipment"];

  it("should display item details and apply correct color based on item type", () => {
    itemType.forEach((type) => {
      cy.mount(FormattedItemName, {
        props: {
          item_id,
          itemType: type,
        },
      }).then(() => {
        cy.contains(item_id).should("exist");

        const expectedColorHex = itemTypes[type]?.lightColor || "LightGrey";
        const expectedColorRgb = hexToRgb(expectedColorHex);

        cy.get(".formatted-item-name").should("have.css", "background-color", expectedColorRgb);
      });
    });
  });

  it("should truncate the name when it exceeds maxLength", () => {
    const longName = "This is a very long name for testing";
    const maxLength = 10;

    cy.mount(FormattedItemName, {
      props: {
        item_id: "Test",
        itemType: "samples",
        name: longName,
        maxLength: maxLength,
      },
    });

    cy.contains("This is a ...").should("exist");
  });

  it("should display full name when it's shorter than maxLength", () => {
    const shortName = "Short name";

    cy.mount(FormattedItemName, {
      props: {
        item_id: "Test",
        itemType: "samples",
        name: shortName,
      },
    });

    cy.contains(shortName).should("exist");
  });

  it("should emit 'itemIdClicked' event when item_id is clicked", () => {
    const item_id = "Test";

    cy.window().then((win) => {
      cy.spy(win, "open").as("windowOpen");
    });

    cy.mount(FormattedItemName, {
      props: {
        item_id,
        itemType: "samples",
        enableClick: true,
      },
    });

    cy.get(".formatted-item-name").click();

    cy.get("@windowOpen").should("have.been.calledWith", `/edit/${item_id}`, "_blank");
  });

  it("should emit 'itemIdClicked' event when clicked with Ctrl or Meta key", () => {
    const item_id = "Test";

    cy.window().then((win) => {
      cy.spy(win, "open").as("windowOpen");
    });

    cy.mount(FormattedItemName, {
      props: {
        item_id,
        itemType: "samples",
        enableModifiedClick: true,
      },
    });

    cy.get(".formatted-item-name").click({ ctrlKey: true });

    cy.get("@windowOpen").should("have.been.calledWith", `/edit/${item_id}`, "_blank");
  });

  it("should display chemical formula when chemform is provided", () => {
    cy.mount(FormattedItemName, {
      props: {
        item_id: "Test",
        itemType: "samples",
        chemform: "H2O",
      },
    });

    cy.contains("[ H2O ]").should("exist");
  });
});
