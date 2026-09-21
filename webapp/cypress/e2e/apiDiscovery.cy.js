// Verifies the `x_datalab_api_url` meta tag that external tooling (e.g. the
// datalab-api Python client) scrapes from the served webapp to auto-discover
// the API URL. The meta is injected at build time as the `magic-api-url`
// placeholder and patched to the real URL at container start by
// app_entrypoint.sh, so this e2e check is the only place that exercises the
// full build -> runtime-patch path end to end.
//
// Needs the app served (dev server :8080, or the Docker image at :8081 in CI)
// with VUE_APP_API_URL resolving to Cypress's configured apiUrl (:5001).

describe("API URL discovery", () => {
  it("exposes the resolved API URL via the x_datalab_api_url meta tag", () => {
    cy.visit("/");

    const apiUrl = Cypress.config("apiUrl");
    cy.get('head meta[name="x_datalab_api_url"]').should("have.attr", "content", apiUrl);

    // Guard against the failure mode that matters: the build-time placeholder
    // surviving unpatched into the served app.
    cy.get('head meta[name="x_datalab_api_url"]')
      .should("have.attr", "content")
      .and("not.contain", "magic-api-url");
  });
});
