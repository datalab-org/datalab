import Navbar from "@/components/Navbar.vue";
import { createRouter, createWebHistory } from "vue-router";
import { createStore } from "vuex";
import LoginDetails from "@/components/LoginDetails.vue";
import { NAVIGATION_VIEWS } from "@/navigation.js";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faProjectDiagram, faVials } from "@fortawesome/free-solid-svg-icons";

library.add(faProjectDiagram, faVials);

describe("Navbar", () => {
  let store;
  let router;

  beforeEach(() => {
    store = createStore({
      state: {
        currentUserDisplayName: null,
        serverInfo: {
          navigation: [
            { view: "about" },
            { view: "samples" },
            { view: "collections" },
            { view: "starting-materials" },
            { view: "equipment" },
            { view: "item-graph", icon: "project-diagram" },
          ],
        },
      },
    });

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/about", name: "About" },
        { path: "/samples", name: "samples" },
        { path: "/collections", name: "collections" },
        { path: "/starting-materials", name: "starting-materials" },
        { path: "/equipment", name: "equipment" },
        { path: "/item-graph", name: "item-graph" },
      ],
    });
  });

  afterEach(() => {
    delete NAVIGATION_VIEWS.collections.isAvailable;
  });

  it("renders logo image when logo_url is provided", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
      data() {
        return {
          logo_url: "https://example.com/logo.png",
          homepage_url: "https://example.com",
        };
      },
    });

    cy.get(".logo-banner").should("exist");
    cy.get(".logo-banner").should("have.attr", "src", "https://example.com/logo.png");
  });

  it("renders logo image without link when homepage_url is not provided", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
      data() {
        return {
          logo_url: "https://example.com/logo.png",
          homepage_url: null,
        };
      },
    });

    cy.get(".logo-banner").should("exist");
    cy.get(".logo-banner.a").should("not.exist");
  });

  it("renders LoginDetails component", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
        components: {
          LoginDetails,
        },
      },
    });

    cy.get("[data-testid=navbar-logindetails]")
      .should("exist")
      .within(() => {
        cy.contains("Login").should("exist");
        cy.contains("Register").should("exist");
      });
  });

  it("closes the login dropdown when clicking outside", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get('[data-testid="login-dropdown-button"]').click();
    cy.get('[data-testid="login-dropdown-menu"]').should("be.visible");
    cy.get('[data-testid="navbar-navigation"]').click();
    cy.get('[data-testid="login-dropdown-menu"]').should("not.be.visible");
  });

  it("renders all navigation links with correct URLs", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get("#nav").within(() => {
      cy.contains("About").should("have.attr", "href", "/about");
      cy.contains("Samples").should("have.attr", "href", "/samples");
      cy.contains("Collections").should("have.attr", "href", "/collections");
      cy.contains("Inventory").should("have.attr", "href", "/starting-materials");
      cy.contains("Equipment").should("have.attr", "href", "/equipment");
      cy.contains("Graph View").should("have.attr", "href", "/item-graph");
    });
  });

  it("renders configured links in order with custom labels and icons", () => {
    store.state.serverInfo.navigation = [
      { view: "equipment" },
      { view: "starting-materials", label: "Starting Materials", icon: "vials" },
      { view: "about", label: "About this deployment" },
    ];

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get("#nav a").then(($links) => {
      expect([...$links].map((link) => link.textContent.trim())).to.deep.equal([
        "Equipment",
        "Starting Materials",
        "About this deployment",
      ]);
    });
    cy.get('[data-testid="navbar-link-starting-materials"]')
      .should("have.attr", "href", "/starting-materials")
      .find('font-awesome-icon[icon="vials"]')
      .should("exist");
    cy.get("#nav .nav-separator").should("have.length", 2);
  });

  it("supports an explicitly empty navigation", () => {
    store.state.serverInfo.navigation = [];

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get("#nav a").should("not.exist");
    cy.get("#nav .nav-separator").should("not.exist");
  });

  it("uses the legacy navigation when loaded server metadata has no navigation", () => {
    store.state.serverInfo = {};

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get("#nav a").should("have.length", 6);
    cy.get('[data-testid="navbar-link-item-graph"] font-awesome-icon').should("exist");
  });

  it("does not render links before server metadata is loaded", () => {
    store.state.serverInfo = null;

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
        stubs: {
          LoginDetails: true,
        },
      },
    });

    cy.get("#nav a").should("not.exist");
    cy.get("#nav .nav-separator").should("not.exist");
  });

  it("skips unknown views and icons without affecting valid links", () => {
    store.state.serverInfo.navigation = [
      { view: "missing-view" },
      { view: "constructor" },
      { view: "__proto__" },
      { view: "samples", icon: "missing-icon" },
      { view: "about" },
    ];

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get("#nav a").should("have.length", 2);
    cy.get('[data-testid="navbar-link-samples"] font-awesome-icon').should("not.exist");
    cy.get("#nav .nav-separator").should("have.length", 1);
  });

  it("hides a configured view when its catalog availability predicate returns false", () => {
    NAVIGATION_VIEWS.collections.isAvailable = (serverInfo) => serverInfo.features.test_enabled;
    store.state.serverInfo = {
      features: { test_enabled: false },
      navigation: [{ view: "samples" }, { view: "collections" }, { view: "equipment" }],
    };

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get('[data-testid="navbar-link-collections"]').should("not.exist");
    cy.get("#nav a").should("have.length", 2);
    cy.get("#nav .nav-separator").should("have.length", 1);
  });

  it("only hides omitted links and leaves their routes registered", () => {
    store.state.serverInfo.navigation = [{ view: "samples" }];

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.get('[data-testid="navbar-link-collections"]').should("not.exist");
    expect(router.hasRoute("collections")).to.equal(true);
  });

  it("navigates to the correct route on link click", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
    });

    cy.contains("About").click();
    cy.url().should("include", "/about");

    cy.contains("Samples").click();
    cy.url().should("include", "/samples");

    cy.contains("Collections").click();
    cy.url().should("include", "/collections");

    cy.contains("Inventory").click();
    cy.url().should("include", "/starting-materials");

    cy.contains("Equipment").click();
    cy.url().should("include", "/equipment");

    cy.contains("Graph View").click();
    cy.url().should("include", "/item-graph");
  });

  it("shows login message when user is not logged in", () => {
    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
      data() {
        return {
          logo_url: "https://example.com/logo.png",
          homepage_url: "https://example.com",
        };
      },
    });

    cy.get(".alert-info").should("exist");
    cy.get(".alert-info").should("contain.text", "Please login to view or create items.");
  });

  it("does not show login message when user is logged in", () => {
    store.state.currentUserDisplayName = "Test User";

    cy.mount(Navbar, {
      global: {
        plugins: [store, router],
      },
      data() {
        return {
          logo_url: "https://example.com/logo.png",
          homepage_url: "https://example.com",
        };
      },
    });

    cy.get(".alert-info").should("not.exist");
  });
});
