import router from "@/router/index.js";
import store from "@/store/index.js";
import { invalidateCurrentUserCache } from "@/server_fetch_utils.js";

describe("Router", () => {
  beforeEach(() => {
    store.state.serverInfo = null;
    invalidateCurrentUserCache();
  });

  it("uses one explicit home route without changing direct routes", () => {
    expect(router.resolve("/").name).to.equal("home");
    expect(router.resolve("/samples").name).to.equal("samples");
    expect(router.resolve("/equipment").name).to.equal("equipment");
    expect(router.resolve("/admin").name).to.equal("admin");
  });

  it("redirects the root path to the configured default route", () => {
    cy.intercept("GET", "**/get-current-user/", {
      immutable_id: "test-user",
      display_name: "Test User",
      role: "user",
      account_status: "active",
    });
    cy.intercept("GET", "**/info", {
      data: {
        attributes: {
          navigation: [
            { view: "samples", default: false },
            { view: "equipment", default: true },
          ],
        },
      },
    });

    cy.then(async () => {
      await router.push("/");
      await router.isReady();

      expect(router.currentRoute.value.name).to.equal("equipment");
      expect(router.currentRoute.value.path).to.equal("/equipment");
    });
  });
});
