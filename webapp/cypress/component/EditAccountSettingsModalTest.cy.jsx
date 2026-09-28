import store from "@/store/index.js";
import EditAccountSettingsModal from "@/components/EditAccountSettingsModal.vue";
import { invalidateCurrentUserCache } from "@/server_fetch_utils.js";

describe("EditAccountSettingsModal profile submission", () => {
  const baseUser = {
    immutable_id: "111111111111111111111111",
    display_name: "Test User",
    contact_email: "verified@example.org",
    role: "user",
    account_status: "active",
    groups: [],
    identities: [
      {
        identity_type: "email",
        identifier: "verified@example.org",
        name: "verified@example.org",
        verified: true,
      },
      {
        identity_type: "email",
        identifier: "pending@example.org",
        name: "pending@example.org",
        verified: false,
      },
    ],
  };

  function mountModal(user, { emailVerification = true } = {}) {
    invalidateCurrentUserCache();
    store.commit("setServerInfo", {
      features: { auth_mechanisms: { email: emailVerification } },
    });
    cy.intercept("GET", "**/get-current-user/", { body: user }).as("getUser");
    cy.intercept("GET", "**/api-keys", { body: { api_keys: [] } });
    cy.intercept("GET", "**/users/*/activity", { body: { status: "success", data: {} } });
    cy.intercept("GET", "https://www.gravatar.com/**", { statusCode: 404 });
    cy.intercept("PATCH", "**/users/*", {
      body: { status: "success", message: "User updated successfully" },
    }).as("saveUser");

    const onUpdate = cy.spy().as("closed");
    // The modal only opens on a change of `modelValue`, so mount closed and then open it
    cy.mount(EditAccountSettingsModal, {
      global: { plugins: [store] },
      props: { modelValue: false, "onUpdate:modelValue": onUpdate },
    }).then(({ wrapper }) => wrapper.setProps({ modelValue: true }));
    // Bootstrap's modal z-index is not loaded in component tests, so hide the backdrop
    // overlay that would otherwise cover the modal and block interactions
    cy.get("#dummyDivForModalBackground").invoke("css", "display", "none");
    cy.wait("@getUser");
    cy.get("#account-name").should("have.value", user.display_name);
  }

  function submit() {
    cy.get("input[type='submit']").click();
  }

  it("only sends changed fields", () => {
    mountModal(baseUser);

    cy.get("#account-name").clear().type("New Name");
    submit();

    cy.wait("@saveUser").its("request.body").should("deep.equal", { display_name: "New Name" });
  });

  it("cannot be saved when nothing changed and the contact email is verified", () => {
    mountModal(baseUser);

    cy.get("input[type='submit']").should("be.disabled");
  });

  it("warns about and re-sends an unchanged, unverified contact email", () => {
    mountModal({ ...baseUser, contact_email: "pending@example.org" });

    cy.contains(".alert-warning", "Your contact email is not verified").should("exist");
    // Saving is still allowed with no changes, so that the verification email can be re-sent
    cy.get("input[type='submit']").should("not.be.disabled");
    submit();

    cy.wait("@saveUser")
      .its("request.body")
      .should("deep.equal", { contact_email: "pending@example.org" });
  });

  it("explains that no verification email is sent when verification is disabled", () => {
    mountModal({ ...baseUser, contact_email: "pending@example.org" }, { emailVerification: false });

    cy.contains(".alert-secondary", "Your contact email is not verified")
      .should("exist")
      .and("contain", "Email verification is not enabled");
    cy.get(".alert-warning").should("not.exist");
  });

  it("offers known emails in the contact email dropdown", () => {
    mountModal(baseUser);

    cy.get("select#account-email").should("have.value", "verified@example.org");
    cy.get("select#account-email option").then((options) => {
      const labels = [...options].map((option) => option.textContent.trim());
      expect(labels).to.deep.equal([
        "No contact email",
        "verified@example.org",
        "pending@example.org (unverified)",
        "Add a new email address…",
      ]);
    });
    cy.contains(".alert-warning", "Your contact email is not verified").should("not.exist");
  });

  it("sends a newly added email address", () => {
    mountModal(baseUser);

    cy.get("select#account-email").select("Add a new email address…");
    cy.get("input#account-email").should("have.value", "");
    cy.get("input[type='submit']").should("be.disabled");

    cy.get("input#account-email").type("new@example.org");
    cy.get("input[type='submit']").should("not.be.disabled");
    submit();

    cy.wait("@saveUser")
      .its("request.body")
      .should("deep.equal", { contact_email: "new@example.org" });
  });

  it("restores the previous contact email when adding is cancelled", () => {
    mountModal(baseUser);

    cy.get("select#account-email").select("Add a new email address…");
    cy.get("input#account-email").type("new@example.org");
    cy.contains("button", "Cancel").click();

    cy.get("select#account-email").should("have.value", "verified@example.org");
    cy.get("input[type='submit']").should("be.disabled");
  });
});
