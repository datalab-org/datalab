import store from "@/store/index.js";
import AccountSettings from "@/components/AccountSettings.vue";
import { getUserInfo, invalidateCurrentUserCache } from "@/server_fetch_utils.js";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { DialogService } from "@/services/DialogService";

describe("AccountSettings profile submission", () => {
  let mountedAccountSettings;

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

  function mountAccountSettings(
    user,
    { emailVerification = true, apiKeys = [], active = true } = {},
  ) {
    const persistedUser = { ...user };
    invalidateCurrentUserCache();
    store.commit("setServerInfo", {
      features: { auth_mechanisms: { email: emailVerification } },
    });
    cy.intercept("GET", "**/get-current-user/", (request) => {
      request.reply({ body: persistedUser });
    }).as("getUser");
    cy.intercept("GET", "**/api-keys", { body: { api_keys: apiKeys } });
    cy.intercept("GET", "**/users/*/activity", { body: { status: "success", data: {} } });
    cy.intercept("GET", "https://www.gravatar.com/**", { statusCode: 404 });
    cy.intercept("PATCH", "**/users/*", (request) => {
      Object.assign(persistedUser, request.body);
      const message = Object.prototype.hasOwnProperty.call(request.body, "contact_email")
        ? `Verification email sent to ${request.body.contact_email}`
        : "User updated successfully";
      request.reply({ body: { status: "success", message } });
    }).as("saveUser");

    cy.mount(AccountSettings, {
      global: { plugins: [store] },
      props: { active },
    }).then(({ wrapper }) => {
      mountedAccountSettings = wrapper;
    });
    cy.wait("@getUser");
    cy.get("#account-name").should("have.value", user.display_name);
  }

  function submit() {
    cy.get("[data-testid='profile-save']").click();
  }

  it("shows a save icon and label in the Profile toolbar", () => {
    mountAccountSettings(baseUser);

    cy.get("[data-testid='profile-save']")
      .should("contain.text", "Save")
      .and("have.class", "btn-info")
      .and("be.disabled");
    cy.then(() => {
      expect(mountedAccountSettings.findComponent(FontAwesomeIcon).props("icon")).to.equal("save");
    });
  });

  it("marks Profile and the save button when there are unsaved changes", () => {
    mountAccountSettings(baseUser);

    let cleanTabWidth;
    cy.get("#account-tab-profile").then(($tab) => {
      cleanTabWidth = $tab[0].getBoundingClientRect().width;
    });
    cy.get("#account-name").clear();
    cy.get("#account-name").type("Unsaved Name");

    cy.get("#account-tab-profile").should("have.attr", "aria-label", "Profile, unsaved changes");
    cy.get("#account-tab-profile .profile-unsaved-dot").should("be.visible");
    cy.get("#account-tab-profile").should(($tab) => {
      expect($tab[0].getBoundingClientRect().width).to.be.closeTo(cleanTabWidth, 0.5);
    });
    cy.get("[data-testid='profile-save']")
      .should("have.class", "btn-warning")
      .and("not.be.disabled");

    cy.get("#account-tab-api-keys").click();
    cy.get("#account-tab-profile").should("have.attr", "aria-label", "Profile, unsaved changes");
    cy.get("[data-testid='profile-save']").should("not.exist");

    cy.get("#account-tab-activity").click();
    cy.get("#account-tab-profile").should("have.attr", "aria-label", "Profile, unsaved changes");
  });

  it("clears the unsaved state after saving", () => {
    mountAccountSettings(baseUser);

    cy.get("#account-name").clear();
    cy.get("#account-name").type("New Name");
    submit();

    cy.wait("@saveUser");
    cy.get("#account-name").should("have.value", "New Name");
    cy.get("#account-tab-profile").should("have.attr", "aria-label", "Profile");
    cy.get("[data-testid='profile-save']").should("have.class", "btn-info");
  });

  it("only sends changed fields", () => {
    mountAccountSettings(baseUser);

    cy.get("#account-name").clear();
    cy.get("#account-name").type("New Name");
    submit();

    cy.wait("@saveUser").its("request.body").should("deep.equal", { display_name: "New Name" });
  });

  it("saves valid profile changes with Ctrl+S", () => {
    mountAccountSettings(baseUser);

    cy.get("#account-name").clear();
    cy.get("#account-name").type("Keyboard Save");
    cy.document().then((document) => {
      const event = new KeyboardEvent("keydown", {
        key: "s",
        ctrlKey: true,
        bubbles: true,
        cancelable: true,
      });
      document.dispatchEvent(event);
      expect(event.defaultPrevented).to.be.true;
    });

    cy.wait("@saveUser")
      .its("request.body")
      .should("deep.equal", { display_name: "Keyboard Save" });
  });

  it("does not handle Ctrl+S while Account settings is inactive", () => {
    mountAccountSettings(baseUser, { active: false });

    cy.get("#account-name").clear();
    cy.get("#account-name").type("Unsaved Name");
    cy.document().then((document) => {
      const event = new KeyboardEvent("keydown", {
        key: "s",
        ctrlKey: true,
        bubbles: true,
        cancelable: true,
      });
      document.dispatchEvent(event);
      expect(event.defaultPrevented).to.be.false;
    });
    cy.get("@saveUser.all").should("have.length", 0);
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

    cy.get("[data-testid='profile-save']").should("be.disabled");
  });

  it("warns about an unchanged, unverified contact email without re-sending", () => {
    mountAccountSettings({ ...baseUser, contact_email: "pending@example.org" });

    cy.contains(".alert-warning", "Your contact email is not verified").should("exist");
    cy.get("[data-testid='profile-save']").should("be.disabled");
    cy.get("@saveUser.all").should("have.length", 0);
  });

  it("does not re-send verification when saving another profile field", () => {
    cy.stub(DialogService, "alert").as("verificationAlert");
    mountAccountSettings({ ...baseUser, contact_email: "pending@example.org" });

    cy.get("#account-name").clear();
    cy.get("#account-name").type("New Name");
    submit();

    cy.wait("@saveUser").its("request.body").should("deep.equal", { display_name: "New Name" });
    cy.get("@verificationAlert").should("not.have.been.called");
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
    cy.stub(DialogService, "alert").as("verificationAlert");
    mountAccountSettings(baseUser);

    cy.get("select#account-email").select("Add a new email address…");
    cy.get("input#account-email").should("have.value", "");
    cy.get("[data-testid='profile-save']").should("be.disabled");

    cy.get("input#account-email").type("new@example.org");
    cy.get("[data-testid='profile-save']").should("not.be.disabled");
    submit();

    cy.wait("@saveUser")
      .its("request.body")
      .should("deep.equal", { contact_email: "new@example.org" });
    cy.get("@verificationAlert").should(
      "have.been.calledOnceWith",
      Cypress.sinon.match({ title: "Verification Email Sent" }),
    );
  });

  it("restores the previous contact email when adding is cancelled", () => {
    mountAccountSettings(baseUser);

    cy.get("select#account-email").select("Add a new email address…");
    cy.get("input#account-email").type("new@example.org");
    cy.contains("button", "Cancel").click();

    cy.get("select#account-email").should("have.value", "verified@example.org");
    cy.get("[data-testid='profile-save']").should("be.disabled");
  });

  it("uses Bootstrap classes to keep the save toolbar responsive", () => {
    mountAccountSettings(baseUser);

    cy.get(".account-toolbar").should("have.class", "d-sm-flex");
    cy.get(".account-save")
      .should("have.class", "justify-content-end")
      .and("have.class", "ml-sm-3");
  });

  it("wraps API key details within a narrow viewport", () => {
    cy.viewport(375, 667);
    mountAccountSettings(baseUser, {
      apiKeys: [
        {
          _id: "key-1",
          name: "Laptop key",
          digest: "abcd...wxyz",
          created_at: "2026-01-02T12:00:00Z",
        },
      ],
    });

    cy.get("#account-tab-api-keys").click();
    cy.then(() => {
      mountedAccountSettings.vm.apiKey = "secret-key";
      mountedAccountSettings.vm.apiKeys[0].show = true;
    });
    cy.get(".api-key-header").should("not.be.visible");
    cy.get('input[aria-label="Generated API key"]').should("exist");
    cy.get('button[aria-label="Copy API key"]').should("exist");
    cy.get(".api-key-row")
      .should("have.css", "flex-wrap", "wrap")
      .then(($row) => {
        const row = $row[0].getBoundingClientRect();
        cy.get(".api-key-row .api-key-middle").should(($middle) => {
          const middle = $middle[0].getBoundingClientRect();
          expect(middle.left).to.be.at.least(row.left - 1);
          expect(middle.right).to.be.at.most(row.right + 1);
        });
      });
  });
});
