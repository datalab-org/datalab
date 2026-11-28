import BlockOrderToggle from "@/components/BlockOrderToggle.vue";
import PrimeVue from "primevue/config";

const STORAGE_KEY = "datalab-block-order-mode";

describe("BlockOrderToggle.vue", () => {
  beforeEach(() => {
    window.localStorage.removeItem(STORAGE_KEY);
  });

  const mountToggle = (modelValue = "manual") => {
    const onUpdate = cy.spy().as("onUpdate");
    cy.mount(BlockOrderToggle, {
      props: { modelValue, "onUpdate:modelValue": onUpdate },
      global: { plugins: [PrimeVue] },
    });
  };

  it("renders both ordering options", () => {
    mountToggle();
    cy.get('[data-testid="block-order-toggle"]').should("exist");
    cy.contains("Manual").should("exist");
    cy.contains("Timeline").should("exist");
  });

  it("emits and remembers the selected mode", () => {
    mountToggle();
    cy.contains("Timeline").click();
    cy.get("@onUpdate").should("have.been.calledWith", "timeline");
    cy.window().then((win) => {
      expect(win.localStorage.getItem(STORAGE_KEY)).to.equal("timeline");
    });
  });

  it("restores the remembered mode on mount", () => {
    window.localStorage.setItem(STORAGE_KEY, "timeline");
    mountToggle();
    cy.get("@onUpdate").should("have.been.calledWith", "timeline");
  });

  it("ignores invalid remembered values", () => {
    window.localStorage.setItem(STORAGE_KEY, "garbage");
    mountToggle();
    cy.get("@onUpdate").should("not.have.been.called");
  });
});
