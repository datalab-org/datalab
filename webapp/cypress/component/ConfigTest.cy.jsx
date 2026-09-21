import { SETTINGS, resolveConfig } from "@/config.js";

describe("resolveConfig", () => {
  beforeEach(() => {
    cy.stub(console, "error").as("consoleError");
  });

  it("uses the defaults when nothing is set", () => {
    const config = resolveConfig({}, {});
    expect(config.API_URL).to.equal("http://localhost:5001");
    expect(config.WEBSITE_TITLE).to.equal("datalab");
    expect(config.LOGO_WIDTH).to.equal(100);
    expect(config.EDITABLE_INVENTORY).to.equal(false);
    expect(config.HOMEPAGE_URL).to.equal(undefined);
    cy.get("@consoleError").should("not.have.been.called");
  });

  it("prefers runtime values over build-time values", () => {
    const config = resolveConfig({ WEBSITE_TITLE: "runtime" }, { WEBSITE_TITLE: "build" });
    expect(config.WEBSITE_TITLE).to.equal("runtime");
    expect(resolveConfig({}, { WEBSITE_TITLE: "build" }).WEBSITE_TITLE).to.equal("build");
  });

  it("parses settings into their types", () => {
    const config = resolveConfig({ EDITABLE_INVENTORY: "TRUE", LOGO_WIDTH: "250" }, {});
    expect(config.EDITABLE_INVENTORY).to.equal(true);
    expect(config.LOGO_WIDTH).to.equal(250);
  });

  it("shows collections by default and parses the hide collections setting", () => {
    expect(resolveConfig({}, {}).HIDE_COLLECTIONS).to.equal(false);
    expect(resolveConfig({ HIDE_COLLECTIONS: "TRUE" }, {}).HIDE_COLLECTIONS).to.equal(true);
  });

  it("treats empty values as unset", () => {
    const config = resolveConfig({}, { WEBSITE_TITLE: "", HOMEPAGE_URL: "", API_URL: "" });
    expect(config.WEBSITE_TITLE).to.equal("datalab");
    expect(config.HOMEPAGE_URL).to.equal(undefined);
    expect(config.API_URL).to.equal("http://localhost:5001");
    cy.get("@consoleError").should("not.have.been.called");
  });

  it("reports invalid values and falls back to the default", () => {
    const config = resolveConfig({ API_URL: "/api", LOGO_WIDTH: "100px" }, {});
    expect(config.API_URL).to.equal("http://localhost:5001");
    expect(config.LOGO_WIDTH).to.equal(100);
    cy.get("@consoleError").should("have.been.calledTwice");
  });

  it("accepts values tolerated before settings were validated", () => {
    const config = resolveConfig(
      {
        EDITABLE_INVENTORY: "yes",
        AUTOMATICALLY_GENERATE_ID_DEFAULT: "1",
        HOMEPAGE_URL: "www.example.org",
      },
      {},
    );
    expect(config.EDITABLE_INVENTORY).to.equal(false);
    expect(config.AUTOMATICALLY_GENERATE_ID_DEFAULT).to.equal(false);
    expect(config.HOMEPAGE_URL).to.equal("www.example.org");
    cy.get("@consoleError").should("not.have.been.called");
  });

  it("reports unknown settings and does not pass them on", () => {
    const config = resolveConfig({ WEBSITE_TITEL: "typo" }, {});
    expect(config).to.not.have.property("WEBSITE_TITEL");
    cy.get("@consoleError").should("have.been.calledOnce");
  });

  it("has patterns that can be used in the browser", () => {
    Object.values(SETTINGS).forEach((setting) => {
      if (setting.pattern) {
        expect(() => new RegExp(setting.pattern)).to.not.throw();
      }
    });
  });

  it("has a description and valid default for every setting", () => {
    Object.entries(SETTINGS).forEach(([name, setting]) => {
      expect(setting.description, name).to.be.a("string");
      if (setting.default !== undefined && setting.pattern) {
        expect(setting.default, name).to.match(new RegExp(setting.pattern));
      }
    });
  });

  it("passes every setting through to the production container", () => {
    cy.readFile("../docker-compose.yml").then((compose) => {
      Object.keys(SETTINGS).forEach((name) => expect(compose).to.contain(`- VUE_APP_${name}`));
    });
  });
});
