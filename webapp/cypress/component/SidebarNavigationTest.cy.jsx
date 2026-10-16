import SidebarNavigation from "@/components/SidebarNavigation.vue";

describe("SidebarNavigation", () => {
  it("preserves the admin sidebar design and highlights the selected item", () => {
    cy.mount(SidebarNavigation, {
      attrs: { "data-testid": "admin-table" },
      props: {
        title: "Admin Menu",
        items: ["Users", "Groups", "Access Tokens"],
        selectedItem: "Users",
      },
    });

    cy.get('[data-testid="admin-table"]').should("contain.text", "Admin Menu");
    cy.contains("button", "Users")
      .should("have.class", "selected")
      .and("have.attr", "aria-current", "page")
      .and("have.css", "font-weight", "700")
      .and("have.css", "text-decoration-line", "underline");
    cy.contains("button", "Groups")
      .should("not.have.class", "selected")
      .and("not.have.attr", "aria-current");
  });

  it("emits the selected sidebar item for mouse and keyboard activation", () => {
    const onItemSelected = cy.spy().as("itemSelected");
    cy.mount(SidebarNavigation, {
      props: {
        title: "Admin Menu",
        items: ["Users", "Groups"],
        selectedItem: "Users",
        onItemSelected,
      },
    });

    cy.contains("button", "Groups").click();
    cy.get("@itemSelected").should("have.been.calledOnceWith", "Groups");

    cy.contains("button", "Users").focus();
    cy.focused().type("{enter}");
    cy.get("@itemSelected").should("have.been.calledWith", "Users");
  });

  it("displays navigation items horizontally on narrow screens", () => {
    cy.viewport(575, 667);
    cy.mount(SidebarNavigation, {
      props: {
        title: "Admin Menu",
        items: ["Users", "Groups", "Access Tokens"],
        selectedItem: "Users",
      },
    });

    cy.get("nav").should("have.css", "border-right-width", "0px");
    cy.get("ul").should("have.css", "display", "flex");
  });
});
