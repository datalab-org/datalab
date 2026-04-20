import { createStore } from "vuex";
import UserBubbleLogin from "@/components/UserBubbleLogin.vue";
import NotificationDot from "@/components/NotificationDot.vue";
describe("UserBubbleLogin", () => {
  const creator = {
    gravatar_hash: "0123456789abcdef0123456789abcdef",
    display_name: "Test User",
  };

  const testCases = [
    {
      isUnverified: true,
      hasUnverifiedUser: true,
      tooltipText: "There is an unverified user in the database",
    },
    {
      isUnverified: true,
      hasUnverifiedUser: false,
      tooltipText: "Your account is currently unverified, please contact an administrator.",
    },
    {
      isUnverified: false,
      hasUnverifiedUser: true,
      tooltipText: "There is an unverified user in the database",
    },
    { isUnverified: false, hasUnverifiedUser: false, tooltipText: "" },
  ];

  testCases.forEach(({ isUnverified, hasUnverifiedUser, tooltipText }) => {
    describe(`when isUnverified is ${isUnverified} and hasUnverifiedUser is ${hasUnverifiedUser}`, () => {
      let store;

      beforeEach(() => {
        store = createStore({
          getters: {
            getCurrentUserIsUnverified: () => isUnverified,
            getHasUnverifiedUser: () => hasUnverifiedUser,
          },
        });
      });

      it("renders the avatar image with the server-provided gravatar_hash", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });
        cy.get("img.avatar")
          .should("have.attr", "src")
          .and("include", `https://www.gravatar.com/avatar/${creator.gravatar_hash}`);
      });

      it("uses the default size if not provided", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });
        cy.get("img.avatar").should("have.attr", "width", "32").and("have.attr", "height", "32");
      });

      it("allows overriding the size via props", () => {
        const size = 64;
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
            size,
          },
        });

        cy.get("img.avatar")
          .should("have.attr", "width", size.toString())
          .and("have.attr", "height", size.toString());
      });

      it("sets the correct title attribute to display_name", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });
        cy.get("img.avatar").trigger("mouseenter");
        cy.get("[data-testid='styled-tooltip']").should("be.visible");
        cy.get("[data-testid='styled-tooltip']").should("contain", creator.display_name);
      });

      it("applies the correct styles to the avatar image", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });
        cy.get("img.avatar").should("have.css", "border", "2px solid rgb(128, 128, 128)");
        cy.get("img.avatar").should("have.css", "border-radius", "50%");
      });

      it("renders NotificationDot component", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
            components: {
              NotificationDot,
            },
          },
          props: {
            creator,
          },
        });
        if (tooltipText) {
          cy.get(".notification-dot").should("exist");
        } else {
          cy.get(".notification-dot").should("not.exist");
        }
      });

      it("shows the correct tooltip message", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });

        if (tooltipText) {
          cy.get(".notification-dot").trigger("mouseenter");
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");
          cy.get("[data-testid='styled-tooltip'] p").contains(tooltipText);
        } else {
          cy.get(".notification-dot").should("not.exist");
          cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
        }
      });

      it("shows and hides tooltip on mouseenter and mouseleave", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });

        if (tooltipText) {
          cy.get(".notification-dot").trigger("mouseenter");
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");

          cy.get(".notification-dot").trigger("mouseleave");
          cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
        }
      });

      it("shows and hides tooltip on focus and blur", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });

        if (tooltipText) {
          cy.get(".notification-dot").focus();
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");

          cy.get(".notification-dot").blur();
          cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
        }
      });

      it("computes the correct gravatar URL", () => {
        cy.mount(UserBubbleLogin, {
          global: {
            plugins: [store],
          },
          props: {
            creator,
          },
        });

        cy.get("img.avatar")
          .should("have.attr", "src")
          .then((src) => {
            const expectedUrl = `https://www.gravatar.com/avatar/${creator.gravatar_hash}?d=${
              UserBubbleLogin.data().gravatar_style
            }`;
            expect(src).to.include(expectedUrl);
          });
      });
    });
  });
});
