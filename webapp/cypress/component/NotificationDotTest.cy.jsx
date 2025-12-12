import { createStore } from "vuex";
import NotificationDot from "@/components/NotificationDot.vue";

describe("NotificationDot", () => {
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

        cy.mount(NotificationDot, {
          global: {
            plugins: [store],
          },
        });
      });

      it(`shows the correct tooltip message`, () => {
        if (tooltipText) {
          cy.get(".notification-dot").trigger("mouseenter");
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");
          cy.get("[data-testid='styled-tooltip'] p").contains(tooltipText);
        } else {
          cy.get(".notification-dot").should("not.exist");
          cy.get("[data-testid='styled-tooltip']").should("not.exist");
        }
      });

      it(`shows and hides tooltip on mouseenter and mouseleave`, () => {
        if (tooltipText) {
          cy.get(".notification-dot").trigger("mouseenter");
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");

          cy.get(".notification-dot").trigger("mouseleave");
          cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
        }
      });

      it(`shows and hides tooltip on focus and blur`, () => {
        if (tooltipText) {
          cy.get(".notification-dot").focus();
          cy.get("[data-testid='styled-tooltip']").should("have.attr", "data-show");

          cy.get(".notification-dot").blur();
          cy.get("[data-testid='styled-tooltip']").should("not.have.attr", "data-show");
        }
      });
    });
  });
});
