import store from "@/store/index.js";
import AccountSettings from "@/components/AccountSettings.vue";
import { getUserInfo, invalidateCurrentUserCache } from "@/server_fetch_utils.js";

describe("AccountSettings profile submission", () => {
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

  function mountAccountSettings(user, { emailVerification = true } = {}) {
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

    cy.mount(AccountSettings, {
      global: { plugins: [store] },
    });
    cy.wait("@getUser");
    cy.get("#account-name").should("have.value", user.display_name);
  }

  function submit() {
    cy.get("input[type='submit']").click();
  }

  it("only sends changed fields", () => {
    mountAccountSettings(baseUser);

    cy.get("#account-name").clear();
    cy.get("#account-name").type("New Name");
    submit();

    cy.wait("@saveUser").its("request.body").should("deep.equal", { display_name: "New Name" });
  });

  it("does not mutate the cached user while editing the form", () => {
    mountAccountSettings(baseUser);

    cy.get("#account-name").clear();
    cy.get("#account-name").type("Unsaved Name");

    cy.then(() => getUserInfo())
      .its("display_name")
      .should("equal", "Test User");
  });

  it("cannot be saved when nothing changed and the contact email is verified", () => {
    mountAccountSettings(baseUser);

    cy.get("input[type='submit']").should("be.disabled");
  });

  it("warns about and re-sends an unchanged, unverified contact email", () => {
    mountAccountSettings({ ...baseUser, contact_email: "pending@example.org" });

    cy.contains(".alert-warning", "Your contact email is not verified").should("exist");
    // Saving is still allowed with no changes, so that the verification email can be re-sent
    cy.get("input[type='submit']").should("not.be.disabled");
    submit();

    cy.wait("@saveUser")
      .its("request.body")
      .should("deep.equal", { contact_email: "pending@example.org" });
  });

  it("explains that no verification email is sent when verification is disabled", () => {
    mountAccountSettings(
      { ...baseUser, contact_email: "pending@example.org" },
      { emailVerification: false },
    );

    cy.contains(".alert-secondary", "Your contact email is not verified")
      .should("exist")
      .and("contain", "Email verification is not enabled");
    cy.get(".alert-warning").should("not.exist");
  });

  it("offers known emails in the contact email dropdown", () => {
    mountAccountSettings(baseUser);

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
    mountAccountSettings(baseUser);

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
    mountAccountSettings(baseUser);

    cy.get("select#account-email").select("Add a new email address…");
    cy.get("input#account-email").type("new@example.org");
    cy.contains("button", "Cancel").click();

    cy.get("select#account-email").should("have.value", "verified@example.org");
    cy.get("input[type='submit']").should("be.disabled");
  });
});
