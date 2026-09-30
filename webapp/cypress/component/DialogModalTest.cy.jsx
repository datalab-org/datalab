import DialogModal from "@/components/DialogModal.vue";

describe("DialogModal", () => {
  it("renders the title and message", () => {
    cy.mount(DialogModal, {
      props: { isVisible: true, title: "Hello", message: "A plain message" },
    });
    cy.get(".modal-title").should("have.text", "Hello");
    cy.get(".modal-body").should("contain.text", "A plain message");
  });

  it("keeps benign formatting tags", () => {
    cy.mount(DialogModal, {
      props: { isVisible: true, message: "Delete <strong>Test User</strong>?" },
    });
    cy.get(".modal-body strong").should("have.text", "Test User");
  });

  // Regression tests for stored XSS: dialog messages are built from user- and
  // server-provided strings (display names, error text, etc.) and rendered with
  // `v-html`, so they must be sanitised before insertion.
  describe("sanitises malicious messages", () => {
    beforeEach(() => {
      cy.window().then((win) => {
        win.__xss_fired = false;
      });
    });

    it("does not execute an injected img/onerror payload", () => {
      const payload = `Delete <img src=x onerror="window.__xss_fired = true"> now`;
      cy.mount(DialogModal, { props: { isVisible: true, message: payload } });
      cy.get(".modal-body").find("img").should("not.exist");
      cy.window().its("__xss_fired").should("be.false");
    });

    it("does not render an injected script tag", () => {
      const payload = `<script>window.__xss_fired = true</script>hello`;
      cy.mount(DialogModal, { props: { isVisible: true, message: payload } });
      cy.get(".modal-body").find("script").should("not.exist");
      cy.window().its("__xss_fired").should("be.false");
    });

    it("strips event-handler attributes from otherwise-allowed tags", () => {
      const payload = `<strong onmouseover="window.__xss_fired = true">name</strong>`;
      cy.mount(DialogModal, { props: { isVisible: true, message: payload } });
      cy.get(".modal-body strong").should("exist").and("not.have.attr", "onmouseover");
      cy.window().its("__xss_fired").should("be.false");
    });
  });

  it("emits confirm and hides when the confirm button is clicked", () => {
    const onConfirm = cy.stub().as("confirm");
    const onVisible = cy.stub().as("visible");
    cy.mount(DialogModal, {
      props: {
        isVisible: true,
        message: "Proceed?",
        showCancelButton: true,
        onConfirm: onConfirm,
        "onUpdate:isVisible": onVisible,
      },
    });
    cy.contains("button", "OK").click();
    cy.get("@confirm").should("have.been.calledOnce");
    cy.get("@visible").should("have.been.calledWith", false);
  });

  it("emits cancel when the cancel button is clicked", () => {
    const onCancel = cy.stub().as("cancel");
    cy.mount(DialogModal, {
      props: {
        isVisible: true,
        message: "Proceed?",
        showCancelButton: true,
        onCancel: onCancel,
      },
    });
    cy.contains("button", "Cancel").click();
    cy.get("@cancel").should("have.been.calledOnce");
  });
});
