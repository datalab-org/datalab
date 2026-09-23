// E2E coverage for the router's login guard: unauthenticated users are sent to
// the login page, except when opening an item page with an access token (`at`).

const API_URL = Cypress.config("apiUrl");
const item_id = "login_redirect_token_sample";

let refcode;
let accessToken;

before(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
  cy.request({
    method: "POST",
    url: API_URL + "/delete-sample/",
    body: { item_id },
    failOnStatusCode: false,
  });
  cy.request({
    method: "POST",
    url: API_URL + "/new-sample/",
    body: { new_sample_data: { type: "samples", item_id, name: "Sample for token access" } },
  }).then((response) => {
    refcode = response.body.sample_list_entry.refcode;
    cy.request({
      method: "POST",
      url: API_URL + `/items/${refcode}/issue-access-token`,
    }).then((tokenResponse) => {
      accessToken = tokenResponse.body.token;
    });
  });
});

after(() => {
  cy.loginViaTestMagicLink("test-user@example.com", "user");
  cy.request({
    method: "POST",
    url: API_URL + "/delete-sample/",
    body: { item_id },
    failOnStatusCode: false,
  });
});

describe("Login redirect for unauthenticated users", () => {
  beforeEach(() => {
    cy.clearAllCookies();
  });

  it("redirects a protected route to the login page with `next` set", () => {
    cy.visit("/samples");
    cy.location("pathname").should("eq", "/login");
    cy.location("search").should((search) => {
      expect(new URLSearchParams(search).get("next")).to.eq("/samples");
    });
  });

  it("loads an item page with a valid access token without redirecting to login", () => {
    cy.intercept("GET", `${API_URL}/items/*`).as("tokenFetch");
    cy.visit(`/items/${refcode}?at=${accessToken}`);

    cy.wait("@tokenFetch").then(({ request, response }) => {
      expect(new URL(request.url).searchParams.get("at")).to.eq(accessToken);
      expect(response.statusCode).to.eq(200);
    });
    cy.location("pathname").should("not.eq", "/login");
    cy.location("search").should("contain", `at=${accessToken}`);
    cy.get(".navbar-brand-name").should("contain", item_id);
  });
});
