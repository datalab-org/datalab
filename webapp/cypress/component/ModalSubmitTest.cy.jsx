import { h } from "vue";
import Modal from "@/components/Modal.vue";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function mountForm({ onSubmit = null, onFormSubmit = null } = {}) {
  const FormWithModal = {
    render() {
      return h("form", { "data-testid": "form", onSubmit: onFormSubmit }, [
        h(
          Modal,
          { modelValue: true, onSubmit },
          { body: () => h("input", { "data-testid": "field", type: "text" }) },
        ),
        h("input", { "data-testid": "second-field", type: "text" }),
      ]);
    },
  };
  return cy.mount(FormWithModal);
}

describe("Modal.vue submit locking", () => {
  it("runs the submit handler once when the submit button is clicked twice", () => {
    const pending = deferred();
    const onSubmit = cy.stub().as("onSubmit").returns(pending.promise);
    mountForm({ onSubmit });

    cy.get("input[type=submit]").click({ force: true });
    cy.get("input[type=submit]").should("be.disabled");
    cy.get("input[type=submit]").click({ force: true });
    cy.get("@onSubmit").should("have.been.calledOnce");

    cy.then(() => pending.resolve());
    cy.get("input[type=submit]").should("not.be.disabled");
  });

  it("locks submissions made with the Enter key", () => {
    const pending = deferred();
    const onSubmit = cy.stub().as("onSubmit").returns(pending.promise);
    mountForm({ onSubmit });

    cy.get("[data-testid=field]").type("{enter}", { force: true });
    cy.get("input[type=submit]").should("be.disabled");
    cy.get("[data-testid=field]").type("{enter}", { force: true });
    cy.get("@onSubmit").should("have.been.calledOnce");

    cy.then(() => pending.resolve());
  });

  it("unlocks after a failed submission so that it can be retried", () => {
    const failure = deferred();
    const onSubmit = cy.stub().as("onSubmit");
    onSubmit.onFirstCall().returns(failure.promise.catch(() => {}));
    onSubmit.onSecondCall().resolves();
    mountForm({ onSubmit });

    cy.get("input[type=submit]").click({ force: true });
    cy.get("input[type=submit]").should("be.disabled");
    cy.then(() => failure.reject(new Error("API error")));
    cy.get("input[type=submit]").should("not.be.disabled");

    cy.get("input[type=submit]").click({ force: true });
    cy.get("@onSubmit").should("have.been.calledTwice");
  });

  it("leaves submission to the form when no submit handler is given", () => {
    const onFormSubmit = cy.spy((event) => event.preventDefault()).as("onFormSubmit");
    mountForm({ onFormSubmit });

    cy.get("input[type=submit]").click({ force: true });
    cy.get("@onFormSubmit").should("have.been.calledOnce");
    cy.get("input[type=submit]").should("not.be.disabled");
  });
});
