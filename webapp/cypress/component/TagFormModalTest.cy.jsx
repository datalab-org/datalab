import TagFormModal from "@/components/TagFormModal.vue";
import { DEFAULT_TAG_COLOR } from "@/resources.js";
import { createStore } from "vuex";

// Mount the modal closed, then open it by flipping `modelValue` so the Modal's open watcher
// (and the form's populate/reset watcher) fire as they do in the app. `role` sets the current
// user's role (the modal offers the "global" scope only to admins).
//
// Emitted events are observed through spies passed as listener props (aliased "tagCreated",
// "tagUpdated" and "updateModelValue") rather than through the test-utils `wrapper.emitted()`
// recorder: `emitted()` is fed by Vue's devtools hook, which is compiled out of production
// builds, and CI runs the component specs with NODE_ENV=production. Listener props are called
// by `emit()` itself, so they record events in either build mode.
//
// Note: component tests run without the app's global Bootstrap CSS, so the Modal's backdrop
// overlays the dialog (no .modal z-index). We use { force: true } on interactions to bypass
// that purely-visual actionability check; the request-body and emit assertions are unaffected.
function mountAndOpen({ tag = null, role = "user" } = {}) {
  const store = createStore({
    state() {
      return { currentUserRole: role };
    },
  });
  return cy
    .mount(TagFormModal, {
      props: {
        modelValue: false,
        tag,
        onTagCreated: cy.spy().as("tagCreated"),
        onTagUpdated: cy.spy().as("tagUpdated"),
        "onUpdate:modelValue": cy.spy().as("updateModelValue"),
      },
      global: { plugins: [store] },
    })
    .then(({ wrapper }) => wrapper.setProps({ modelValue: true }));
}

describe("TagFormModal.vue", () => {
  describe("create mode", () => {
    it("creates a user-defined tag by default (non-admin has no scope choice)", () => {
      cy.intercept("PUT", "**/tags", { statusCode: 201, body: { status: "success", data: {} } }).as(
        "create",
      );
      mountAndOpen();

      // A non-admin cannot choose a scope; the scope field is a disabled "User-defined".
      cy.get('[data-testid="tag-scope-select"]').should("not.exist");
      cy.get("#tag-scope").should("be.disabled").and("have.value", "User-defined");

      cy.get("#tag-name").type("flammable", { force: true });
      cy.get("#tag-description").type("burns", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      // The color picker is left untouched, so the payload carries the default tag color,
      // and the scope defaults to a user-defined ("user") tag.
      cy.wait("@create")
        .its("request.body")
        .should("deep.equal", {
          data: {
            name: "flammable",
            description: "burns",
            color: DEFAULT_TAG_COLOR,
            scope: "user",
          },
        });
      cy.get("@tagCreated").should("have.been.calledOnce");
      // The modal asks its parent to close on success.
      cy.get("@updateModelValue").its("lastCall.args").should("deep.equal", [false]);
    });

    it("lets an admin create a global tag", () => {
      cy.intercept("PUT", "**/tags", { statusCode: 201, body: { status: "success", data: {} } }).as(
        "create",
      );
      mountAndOpen({ role: "admin" });

      // An admin can choose the scope. (force: true — see mount note: the Modal
      // backdrop overlays the dialog without the app's global Bootstrap CSS.)
      cy.get('[data-testid="tag-scope-select"]').select("global", { force: true });
      cy.get("#tag-name").type("corrosive", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@create").its("request.body.data.scope").should("equal", "global");
    });

    it("shows a name conflict (409) inline instead of an error dialog", () => {
      cy.intercept("PUT", "**/tags", {
        statusCode: 409,
        body: { status: "error", message: "A tag named 'dup' already exists." },
      }).as("create");
      mountAndOpen();

      cy.get("#tag-name").type("dup", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@create");
      cy.get(".form-error").should("contain", "already exists");
      // The modal stays open on a conflict.
      cy.get("@tagCreated").should("not.have.been.called");
      cy.get("@updateModelValue").should("not.have.been.called");
    });
  });

  describe("edit mode", () => {
    const existingTag = {
      immutable_id: "tag-1",
      name: "old-name",
      description: "desc",
      color: "#abcdef",
    };

    it("pre-fills fields and updates metadata via PATCH /tags/<id>", () => {
      cy.intercept("PATCH", "**/tags/*", { statusCode: 200, body: { status: "success" } }).as(
        "updateTag",
      );
      mountAndOpen({ tag: existingTag });

      cy.get("#tag-name").should("have.value", "old-name");
      cy.get("#tag-name").clear({ force: true });
      cy.get("#tag-name").type("new-name", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@updateTag").its("request.body.data.name").should("equal", "new-name");
      cy.get("@tagUpdated").should("have.been.calledOnce");
    });
  });
});
