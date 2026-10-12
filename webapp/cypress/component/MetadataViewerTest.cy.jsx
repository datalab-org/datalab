import MetadataViewer from "@/components/MetadataViewer.vue";

describe("MetadataViewer", () => {
  const computedData = {
    n_peaks: 3,
    avast_metrics: {
      field_one: 0.6687006950378418,
      first_charge_capacity_mAh: 126.34762603468491,
      discharge_capacity_c3_mAh: null,
    },
  };

  it("renders nested computed results as titled sections, omitting null fields", () => {
    cy.mount(MetadataViewer, { props: { computedData } });

    cy.contains(".metadata-title", "Computed").should("be.visible");
    cy.contains(".metadata-title", "Metadata").should("not.exist");

    cy.contains("dt", "N peaks").next("dd").should("have.text", "3");

    cy.contains(".computed-section-title", "Avast metrics").should("be.visible");
    cy.contains("dt", "Field one").next("dd").should("have.text", "0.6687");
    cy.contains("dt", "First charge capacity mAh").next("dd").should("have.text", "126.35");
    cy.contains("dt", "Discharge capacity c3 mAh").should("not.exist");
  });

  it("copies the full-precision computed results as JSON", () => {
    cy.mount(MetadataViewer, { props: { computedData } });
    cy.window().then((win) => {
      cy.stub(win.navigator.clipboard, "writeText").as("writeText").resolves();
    });

    cy.get("[aria-label='Copy computed data as JSON']").click();
    cy.get("@writeText").should("have.been.calledOnceWith", JSON.stringify(computedData, null, 2));
  });

  it("shows computed and metadata sections side by side", () => {
    cy.mount(MetadataViewer, {
      props: { computedData, metadata: { instrument: "BioLogic" } },
    });

    cy.contains(".metadata-title", "Computed").should("be.visible");
    cy.contains(".metadata-title", "Metadata").should("be.visible");
    cy.contains("dt", "Instrument").next("dd").should("have.text", "BioLogic");
  });
});
