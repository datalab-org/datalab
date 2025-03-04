import Navbar from "@/components/Navbar.vue";
import { createRouter, createWebHistory } from "vue-router";
import { createStore } from "vuex";
import LoginDetails from "@/components/LoginDetails.vue";

describe("Navbar", () => {
  let store;
  let router;

  beforeEach(() => {
    store = createStore({
      state: {
        currentUserDisplayName: null,
      },
    });

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/about", name: "About" },
        { path: "/samples", name: "Samples" },
        { path: "/collections", name: "Collections" },
        { path: "/starting-materials", name: "Inventory" },
        { path: "/equipment", name: "Equipment" },
        { path: "/item-graph", name: "GraphView" },
      ],
    });
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
