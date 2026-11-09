import { createStore } from "vuex";
import ConnectedAccounts from "@/components/ConnectedAccounts.vue";

describe("ConnectedAccounts", () => {
  const identities = [
    { identity_type: "github", identifier: "1", name: "gh-user", verified: true },
    { identity_type: "google", identifier: "2", name: "user@gmail.com", verified: true },
    { identity_type: "email", identifier: "other@example.org", name: "other@example.org" },
    { identity_type: "email", identifier: "other@example.org", name: "other@example.org" },
    {
      identity_type: "email",
      identifier: "primary@example.org",
      name: "primary@example.org",
      verified: true,
    },
    { identity_type: "mystery", identifier: "3", name: "mystery-user", verified: true },
  ];

  function mountWith(props, authMechanisms = {}) {
    const store = createStore({
      state: { serverInfo: { features: { auth_mechanisms: authMechanisms } } },
    });
    cy.mount(ConnectedAccounts, { global: { plugins: [store] }, props });
  }

  describe("accounts section", () => {
    it("shows only non-email identities, linking to known profiles", () => {
      mountWith({ identities, section: "accounts" });

      cy.get(".identity-chip").should("have.length", 3);
      cy.get(".identity-chip").should("not.contain", "@example.org");

      cy.contains(".identity-chip", "gh-user")
        .should("match", "a")
        .and("have.attr", "href", "https://github.com/gh-user");
      cy.contains(".identity-chip", "user@gmail.com").should("match", "span");
    });

    it("shows unknown identity types with their type as the label", () => {
      mountWith({ identities, section: "accounts" });

      cy.contains(".identity-chip", "mystery-user").should("have.attr", "title", "mystery");
    });

    it("only offers connect buttons for enabled providers that are not yet connected", () => {
      mountWith(
        { identities, section: "accounts" },
        { github: true, orcid: true, google: true, microsoft: false, email: true },
      );

      // GitHub and Google are already connected, Microsoft is disabled, email is not connectable
      cy.get("a[aria-label^='Connect']").should("have.length", 1);
      cy.contains("a", "Connect ORCID")
        .should("have.attr", "href")
        .and("match", /\/login\/orcid$/);
      cy.contains("a", "Connect GitHub").should("not.exist");
      cy.contains("a", "Connect Google").should("not.exist");
      cy.contains("a", "Connect Microsoft").should("not.exist");
      cy.contains("a", "Connect Email").should("not.exist");
    });

    it("shows a placeholder when there are no accounts", () => {
      mountWith({ identities: [], section: "accounts" });

      cy.contains("No connected accounts.").should("be.visible");
    });
  });

  describe("emails section", () => {
    it("shows each email once, with the primary email first and highlighted", () => {
      mountWith({ identities, section: "emails", primaryEmail: "Primary@example.org" });

      cy.get(".identity-chip").should("have.length", 2);
      cy.get(".identity-chip")
        .first()
        .should("contain", "primary@example.org")
        .and("have.class", "identity-chip-primary")
        .and("contain", "Primary");
      cy.get(".identity-chip")
        .last()
        .should("contain", "other@example.org")
        .and("not.have.class", "identity-chip-primary");
    });

    it("only badges unverified emails", () => {
      mountWith({ identities, section: "emails", primaryEmail: "primary@example.org" });

      cy.contains(".identity-chip", "other@example.org").should("contain", "Unverified");
      cy.contains(".identity-chip", "primary@example.org").should("not.contain", "Unverified");
      cy.contains("Verified").should("not.exist");
    });

    it("never shows connect buttons", () => {
      mountWith({ identities, section: "emails" }, { github: true, orcid: true, google: true });

      cy.get("a[aria-label^='Connect']").should("not.exist");
    });

    it("shows a placeholder when there are no emails", () => {
      mountWith({ identities: identities.slice(0, 2), section: "emails" });

      cy.contains("No email addresses.").should("be.visible");
    });
  });
});
