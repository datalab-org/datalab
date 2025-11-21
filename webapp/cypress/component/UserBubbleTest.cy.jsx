import UserBubble from "@/components/UserBubble.vue";
import { md5 } from "js-md5";

describe("UserBubble", () => {
  const creator = {
    contact_email: "test@contact.email",
    display_name: "Test User",
  };

  beforeEach(() => {
    cy.mount(<UserBubble creator={creator} />);
  });

  it("renders the avatar image with correct gravatar URL based on contact_email", () => {
    const expectedHash = md5(creator.contact_email);
    cy.get("img.avatar")
      .should("have.attr", "src")
      .and("include", `https://www.gravatar.com/avatar/${expectedHash}`);
  });

  it("renders the avatar image with correct gravatar URL based on display_name when contact_email is not provided", () => {
    const creatorWithoutEmail = {
      display_name: "Test User",
    };

    cy.mount(<UserBubble creator={creatorWithoutEmail} />);

    const expectedHash = md5(creatorWithoutEmail.display_name);
    cy.get("img.avatar")
      .should("have.attr", "src")
      .and("include", `https://www.gravatar.com/avatar/${expectedHash}`);
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
