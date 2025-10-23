describe("Authenticated sample tests", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("test-user@example.com", "user");
    cy.visit("/");
  });

  afterEach(() => {
    cy.logout();
  });

  it("Creates a sample as authenticated user", () => {
    cy.createSample("auth-test-1", "Sample created by authenticated user");
    cy.verifySample("auth-test-1", "Sample created by authenticated user");

    cy.findByText("auth-test-1").click();
    cy.contains("test-user@example.com").should("exist");

    cy.visit("/");
    cy.deleteSample("auth-test-1");
  });

  it("Shows correct user info when logged in", () => {
    cy.get(".alert-info").should("not.exist");

    cy.contains("test-user@example.com").should("exist");
  });
});

describe("Admin-specific functionality", () => {
  beforeEach(() => {
    cy.loginViaTestMagicLink("admin-user@example.com", "admin");
    cy.visit("/admin");
  });

  afterEach(() => {
    cy.logout();
  });

  it("Accesses admin dashboard", () => {
    cy.visit("/admin");
    cy.url().should("include", "/admin");
    cy.contains("Admin Menu").should("exist");
    cy.get('[data-testid="admin-table"]').should("exist");
  });
});

describe("Multi-user sample visibility", () => {
  const user1Email = "user1@example.com";
  const user2Email = "user2@example.com";
  const user1SampleId = "user1-sample";
  const user2SampleId = "user2-sample";

  it("User 1 creates a sample", () => {
    cy.loginViaTestMagicLink(user1Email, "user");
    cy.visit("/");

    cy.createSample(user1SampleId, "User 1's sample");
    cy.verifySample(user1SampleId, "User 1's sample");

    cy.logout();
  });

  it("User 2 creates a different sample", () => {
    cy.loginViaTestMagicLink(user2Email, "user");
    cy.visit("/");

    cy.createSample(user2SampleId, "User 2's sample");
    cy.verifySample(user2SampleId, "User 2's sample");

    cy.logout();
  });

  it("User 1 can see their own sample", () => {
    cy.loginViaTestMagicLink(user1Email, "user");
    cy.visit("/");

    cy.verifySample(user1SampleId, "User 1's sample");

    cy.logout();
  });

  it("User 2 can see their own sample", () => {
    cy.loginViaTestMagicLink(user2Email, "user");
    cy.visit("/");

    cy.verifySample(user2SampleId, "User 2's sample");

    cy.logout();
  });

  it("User 1 cannot see User 2's sample", () => {
    cy.loginViaTestMagicLink(user1Email, "user");
    cy.visit("/");

    cy.get("[data-testid=sample-table]").should("not.contain", user2SampleId);

    cy.logout();
  });

  it("User 2 cannot see User 1's sample", () => {
    cy.loginViaTestMagicLink(user2Email, "user");
    cy.visit("/");

    cy.get("[data-testid=sample-table]").should("not.contain", user1SampleId);

    cy.logout();
  });

  after(() => {
    cy.loginViaTestMagicLink(user1Email, "user");
    cy.visit("/");
    cy.deleteSample(user1SampleId);
    cy.logout();

    cy.loginViaTestMagicLink(user2Email, "user");
    cy.visit("/");
    cy.deleteSample(user2SampleId);
    cy.logout();
  });
});
