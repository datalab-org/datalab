import BlockTooltip from "@/components/BlockTooltip.vue";

describe("BlockTooltip", () => {
  describe("with icon mode (showIcon=true)", () => {
    const blockInfoWithAttributes = {
      attributes: {
        name: "Example Block",
        description: "This is an example block description.",
        version: "1.2.3",
        accepted_file_extensions: [".pdf", ".docx", ".xlsx"],
      },
    };

    it("renders the tooltip with correct content on hover", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoWithAttributes, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.contains(blockInfoWithAttributes.attributes.name).should("be.visible");
          cy.contains(blockInfoWithAttributes.attributes.description).should("be.visible");
          cy.contains("Block implementation version: 1.2.3").should("be.visible");
          cy.contains(".pdf").should("be.visible");
          cy.contains(".docx").should("be.visible");
          cy.contains(".xlsx").should("be.visible");
        });
    });

    it("hides the tooltip on mouseleave", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoWithAttributes, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });
      cy.get(".info-icon").trigger("mouseleave", { force: true });

      cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
    });

    it("shows and hides tooltip on focus and blur", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoWithAttributes, showIcon: true },
      });

      cy.get(".info-icon").focus();
      cy.get("[data-testid='styled-tooltip']").should("be.visible");

      cy.get(".info-icon").blur();
      cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
    });

    it("handles blockInfo without version gracefully", () => {
      const blockInfoNoVersion = {
        attributes: {
          name: "Block Without Version",
          description: "This block has no version.",
          accepted_file_extensions: [".txt"],
        },
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoNoVersion, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.contains("Version:").should("not.exist");
          cy.contains(blockInfoNoVersion.attributes.name).should("be.visible");
        });
    });
  });

  describe("without icon mode (showIcon=false - dropdown)", () => {
    const blockInfoDirect = {
      name: "Sample Block",
      description: "This is a sample block description.",
      version: "2.0.0",
      accepted_file_extensions: [".jpg", ".png", ".gif"],
    };

    it("renders the tooltip with correct content on hover", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoDirect, showIcon: false },
      });

      cy.get("a.dropdown-item").trigger("mouseenter");

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.contains(blockInfoDirect.name).should("be.visible");
          cy.contains(blockInfoDirect.description).should("be.visible");
          cy.contains("Block implementation version: 2.0.0").should("be.visible");
          cy.contains("Accepted file extensions:").should("be.visible");
          cy.contains(".jpg, .png, .gif").should("be.visible");
        });
    });

    it("hides the tooltip on mouseleave", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoDirect, showIcon: false },
      });

      cy.get("a.dropdown-item").trigger("mouseenter");
      cy.get("a.dropdown-item").trigger("mouseleave");

      cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
    });

    it("shows and hides tooltip on focus and blur", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoDirect, showIcon: false },
      });

      cy.get("a.dropdown-item").focus();
      cy.get("[data-testid='styled-tooltip']").should("be.visible");

      cy.get("a.dropdown-item").blur();
      cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
    });

    it("displays block name in dropdown item", () => {
      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoDirect, showIcon: false },
      });

      cy.get("a.dropdown-item").should("contain.text", blockInfoDirect.name);
    });
  });

  describe("with both data formats", () => {
    it("handles blockInfo.attributes format correctly", () => {
      const blockInfoWithAttributes = {
        attributes: {
          name: "Attributes Format",
          description: "Using attributes format",
          version: "1.0.0",
        },
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoWithAttributes, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });
      cy.get("[data-testid='styled-tooltip']").should("contain.text", "Attributes Format");
    });

    it("handles direct blockInfo format correctly", () => {
      const blockInfoDirect = {
        name: "Direct Format",
        description: "Using direct format",
        version: "2.0.0",
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo: blockInfoDirect, showIcon: false },
      });

      cy.get("a.dropdown-item").trigger("mouseenter");
      cy.get("[data-testid='styled-tooltip']").should("contain.text", "Direct Format");
    });
  });

  describe("accepted file extensions", () => {
    it("displays extensions as list when showIcon=true", () => {
      const blockInfo = {
        attributes: {
          name: "Block With Extensions",
          description: "Test extensions",
          accepted_file_extensions: [".csv", ".tsv"],
        },
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.get("ul li").should("have.length", 2);
          cy.contains(".csv").should("be.visible");
          cy.contains(".tsv").should("be.visible");
        });
    });

    it("displays extensions inline when showIcon=false", () => {
      const blockInfo = {
        name: "Block With Extensions",
        description: "Test extensions",
        accepted_file_extensions: [".csv", ".tsv"],
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo, showIcon: false },
      });

      cy.get("a.dropdown-item").trigger("mouseenter");

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.contains(".csv, .tsv").should("be.visible");
        });
    });

    it("does not show extensions section when none provided", () => {
      const blockInfo = {
        attributes: {
          name: "No Extensions Block",
          description: "No extensions",
        },
      };

      cy.mount(BlockTooltip, {
        propsData: { blockInfo, showIcon: true },
      });

      cy.get(".info-icon").trigger("mouseenter", { force: true });

      cy.get("[data-testid='styled-tooltip']")
        .should("be.visible")
        .within(() => {
          cy.contains("Accepted file extensions").should("not.exist");
        });
    });
  });
});
