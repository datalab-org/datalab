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
function mountAndOpen({ tag = null, role = "user", userId = null } = {}) {
  const store = createStore({
    state() {
      return { currentUserRole: role, currentUserID: userId };
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

  describe("group tags", () => {
    const groups = [
      { immutable_id: "g1", display_name: "Demo Group", group_id: "demo" },
      { immutable_id: "g2", display_name: "Other Group", group_id: "other" },
    ];

    function interceptGroups(data) {
      cy.intercept("GET", "**/tags/manageable-groups*", {
        statusCode: 200,
        body: { status: "success", data },
      }).as("manageableGroups");
    }

    it("lets a group manager create a group tag (no global option)", () => {
      interceptGroups([groups[0]]);
      cy.intercept("PUT", "**/tags", { statusCode: 201, body: { status: "success", data: {} } }).as(
        "create",
      );
      mountAndOpen();
      cy.wait("@manageableGroups");

      // A non-admin managing a group can choose between user-defined and group tags.
      cy.get('[data-testid="tag-scope-select"] option').then((options) => {
        expect([...options].map((o) => o.value)).to.deep.equal(["user", "group"]);
      });
      cy.get('[data-testid="tag-scope-select"]').select("group", { force: true });
      // With a single manageable group, it is preselected.
      cy.get('[data-testid="tag-group-select"]').should("have.value", "g1");
      // The super-user-mode hint is for admins only.
      cy.get('[data-testid="tag-group-admin-hint"]').should("not.exist");

      cy.get("#tag-name").type("team", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@create")
        .its("request.body.data")
        .should("deep.include", { name: "team", scope: "group", owner: "g1" });
    });

    it("requires a group to be chosen when several are available", () => {
      interceptGroups(groups);
      cy.intercept("PUT", "**/tags", { statusCode: 201, body: { status: "success", data: {} } }).as(
        "create",
      );
      mountAndOpen({ role: "admin" });
      cy.wait("@manageableGroups");

      cy.get('[data-testid="tag-scope-select"] option').then((options) => {
        expect([...options].map((o) => o.value)).to.deep.equal(["user", "group", "global"]);
      });
      cy.get('[data-testid="tag-scope-select"]').select("group", { force: true });
      cy.get("#tag-name").type("team", { force: true });
      cy.get('[data-testid="tag-group-admin-hint"]').should("contain", "super-user mode");

      // No group chosen yet: the form cannot be submitted.
      cy.get('input[type="submit"]').should("be.disabled");

      cy.get('[data-testid="tag-group-select"]').select("g2", { force: true });
      cy.get('input[type="submit"]').should("not.be.disabled").click({ force: true });

      cy.wait("@create").its("request.body.data.owner").should("equal", "g2");
    });

    it("shows a group tag's scope and group read-only when editing", () => {
      mountAndOpen({
        tag: {
          immutable_id: "tag-g",
          name: "team",
          scope: "group",
          owner: "g1",
          owner_name: "Demo Group",
        },
      });

      cy.get('[data-testid="tag-scope-select"]').should("not.exist");
      cy.get("#tag-scope").should("be.disabled").and("have.value", "Group: Demo Group");
    });
  });

  describe("edit mode (scope)", () => {
    const usersTag = {
      immutable_id: "tag-u",
      name: "theirs",
      scope: "user",
      owner: "someone",
      owner_name: "Alice",
    };
    const groups = [
      { immutable_id: "g1", display_name: "Demo Group", group_id: "demo" },
      { immutable_id: "g2", display_name: "Other Group", group_id: "other" },
    ];

    beforeEach(() => {
      cy.intercept("GET", "**/tags/manageable-groups*", {
        statusCode: 200,
        body: { status: "success", data: groups },
      }).as("manageableGroups");
      cy.intercept("PATCH", "**/tags/*", { statusCode: 200, body: { status: "success" } }).as(
        "updateTag",
      );
    });

    it("shows the scope (with the owner) read-only to non-admins", () => {
      // E.g. a user editing their own tag. (Admins could only see this before they could
      // change the scope here.)
      mountAndOpen({ tag: { ...usersTag, owner_name: "Bob" } });

      cy.get('[data-testid="tag-scope-select"]').should("not.exist");
      cy.get("#tag-scope").should("be.disabled").and("have.value", "User-defined: Bob");
    });

    it("lets an admin promote a user's tag, warning that the owner loses access", () => {
      mountAndOpen({ role: "admin", tag: usersTag });
      cy.wait("@manageableGroups");

      // The current scope is kept by default; a tag cannot be moved to another user.
      cy.get('[data-testid="tag-scope-select"] option').then((options) => {
        expect([...options].map((o) => o.value)).to.deep.equal(["user", "group", "global"]);
        expect(options[0].text).to.contain("User-defined: Alice (current)");
      });
      cy.get('[data-testid="tag-scope-select"]').should("have.value", "user");
      cy.get('[data-testid="tag-scope-warning"]').should("not.exist");

      cy.get('[data-testid="tag-scope-select"]').select("global", { force: true });
      cy.get('[data-testid="tag-scope-warning"]').should(
        "contain",
        "Alice will no longer be able to edit or delete this tag",
      );
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@updateTag").then(({ request }) => {
        expect(request.url).to.match(/\/tags\/tag-u$/);
        expect(request.body.data).to.include({ name: "theirs", scope: "global" });
        expect(request.body.data).not.to.have.property("owner");
      });
      cy.get("@tagUpdated").should("have.been.calledOnce");
    });

    it("does not warn an admin that they lose access to their own tag", () => {
      mountAndOpen({ role: "admin", userId: "someone", tag: usersTag });
      cy.wait("@manageableGroups");

      cy.get('[data-testid="tag-scope-select"]').select("global", { force: true });
      cy.get('[data-testid="tag-scope-warning"]')
        .should("contain", "Items that already have the tag keep it")
        .and("not.contain", "no longer");
    });

    it("lets an admin move a tag to a chosen group", () => {
      mountAndOpen({ role: "admin", tag: usersTag });
      cy.wait("@manageableGroups");

      cy.get('[data-testid="tag-scope-select"]').select("group", { force: true });
      // Several groups: one must be chosen before submitting.
      cy.get('input[type="submit"]').should("be.disabled");
      cy.get('[data-testid="tag-group-select"]').select("g2", { force: true });
      cy.get('input[type="submit"]').should("not.be.disabled").click({ force: true });

      cy.wait("@updateTag")
        .its("request.body.data")
        .should("deep.include", { scope: "group", owner: "g2" });
    });

    it("does not send the scope when an admin leaves it unchanged", () => {
      mountAndOpen({ role: "admin", tag: usersTag });
      cy.wait("@manageableGroups");

      cy.get("#tag-description").type("updated", { force: true });
      cy.get('input[type="submit"]').click({ force: true });

      cy.wait("@updateTag").its("request.body.data").should("not.have.property", "scope");
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
