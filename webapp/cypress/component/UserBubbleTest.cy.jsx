import UserBubble from "@/components/UserBubble.vue";

describe("UserBubble", () => {
  const creator = {
    gravatar_hash: "0123456789abcdef0123456789abcdef",
    display_name: "Test User",
  };

  beforeEach(() => {
    cy.mount(<UserBubble creator={creator} />);
  });

  it("renders the avatar image with the server-provided gravatar_hash", () => {
    cy.get("img.avatar")
      .should("have.attr", "src")
      .and("include", `https://www.gravatar.com/avatar/${creator.gravatar_hash}`);
  });

  it("uses the default size if not provided", () => {
    cy.get("img.avatar").should("have.attr", "width", "32").and("have.attr", "height", "32");
  });

  it("allows overriding the size via props", () => {
    const size = 64;
    cy.mount(<UserBubble creator={creator} size={size} />);

    cy.get("img.avatar")
      .should("have.attr", "width", size.toString())
      .and("have.attr", "height", size.toString());
  });

  it("sets the correct title attribute to display_name", () => {
    cy.get("img.avatar").trigger("mouseenter");
    cy.get("[data-testid='styled-tooltip']").should("be.visible");
    cy.get("[data-testid='styled-tooltip']").should("contain", creator.display_name);
  });

  it("applies the correct styles to the avatar image", () => {
    cy.get("img.avatar").should("have.css", "border", "2px solid rgb(128, 128, 128)");
    cy.get("img.avatar").should("have.css", "border-radius", "50%");
  });
});
