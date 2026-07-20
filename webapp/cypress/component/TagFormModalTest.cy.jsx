import TagFormModal from "@/components/TagFormModal.vue";
import { DEFAULT_TAG_COLOR } from "@/resources.js";
import { createStore } from "vuex";

// Mount the modal closed, then open it by flipping `modelValue` so the Modal's open watcher
// (and the form's populate/reset watcher) fire as they do in the app. Returns the test-utils
// wrapper aliased as "wrapper" for emitted assertions. `role` sets the current user's role
// (the modal offers the "global" scope only to admins).
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
      props: { modelValue: false, tag },
      global: { plugins: [store] },
    })
    .then(({ wrapper }) => {
      cy.wrap(wrapper).as("wrapper");
      return wrapper.setProps({ modelValue: true });
    });
}

describe("TagFormModal.vue", () => {
  describe("create mode", () => {
    it("creates a personal tag by default (non-admin has no scope choice)", () => {
      cy.intercept("PUT", "**/tags", { statusCode: 201, body: { status: "success", data: {} } }).as(
        "create",
      );
      mountAndOpen();

      // A non-admin cannot choose a scope; the scope field is a disabled "Personal".
      cy.get('[data-testid="tag-scope-select"]').should("not.exist");
      cy.get("#tag-scope").should("be.disabled").and("have.value", "Personal");

      cy.get("#tag-name").type("flammable", { force: true });
      cy.get("#tag-description").type("burns", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      // The color picker is left untouched, so the payload carries the default tag color,
      // and the scope defaults to a personal ("user") tag.
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
      cy.get("@wrapper").should((wrapper) => {
        expect(wrapper.emitted("tag-created")).to.have.length(1);
        // The modal asks its parent to close on success.
        expect(wrapper.emitted("update:modelValue").at(-1)).to.deep.equal([false]);
      });
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
      cy.get("@wrapper").should((wrapper) => {
        expect(wrapper.emitted("tag-created")).to.be.undefined;
      });
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
      cy.get("@wrapper").should((wrapper) => {
        expect(wrapper.emitted("tag-updated")).to.have.length(1);
      });
    });
  });
});
