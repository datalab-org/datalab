import { library } from "@fortawesome/fontawesome-svg-core";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

import NotificationComposer from "@/components/notifications/NotificationComposer.vue";

library.add(faSpinner);

function mountAndOpen({ allowSendAll = true } = {}) {
  return cy
    .mount(NotificationComposer, {
      props: {
        modelValue: false,
        allowSendAll,
        onSent: cy.spy().as("sent"),
        "onUpdate:modelValue": cy.spy().as("updateModelValue"),
      },
      global: { components: { FontAwesomeIcon } },
    })
    .then(({ wrapper }) => wrapper.setProps({ modelValue: true }).then(() => wrapper));
}

describe("NotificationComposer", () => {
  it("sends an all-user notification with plain text fields", () => {
    cy.intercept("POST", "**/notifications", {
      statusCode: 201,
      body: { status: "success", created_count: 3, grouped_count: 0 },
    }).as("createNotification");
    mountAndOpen();

    cy.get("#notification-send-all").check({ force: true });
    cy.get("#notification-title").type("Planned maintenance", { force: true });
    cy.get("#notification-level").select("important", { force: true });
    cy.get("#notification-summary").type("Short interruption", { force: true });
    cy.get("#notification-message").type("The service will restart at noon.", { force: true });
    cy.contains("button", "Send").click({ force: true });

    cy.wait("@createNotification").its("request.body").should("deep.equal", {
      send_all_users: true,
      title: "Planned maintenance",
      level: "important",
      summary: "Short interruption",
      message: "The service will restart at noon.",
    });
    cy.get("@sent").should("have.been.calledOnce");
    cy.get("@updateModelValue").its("lastCall.args").should("deep.equal", [false]);
  });

  it("can be reused without the all-user option", () => {
    mountAndOpen({ allowSendAll: false }).then((wrapper) =>
      wrapper.setData({
        selectedUsers: [{ immutable_id: "user-1", display_name: "Test User" }],
      }),
    );
    cy.intercept("POST", "**/notifications", {
      statusCode: 201,
      body: { status: "success", created_count: 1, grouped_count: 0 },
    }).as("createNotification");

    cy.get("#notification-send-all").should("not.exist");
    cy.get("#notification-title").type("Direct notification", { force: true });
    cy.contains("button", "Send").click({ force: true });

    cy.wait("@createNotification")
      .its("request.body.recipient_ids")
      .should("deep.equal", ["user-1"]);
  });

  it("preserves the form after a failed request", () => {
    cy.intercept("POST", "**/notifications", {
      statusCode: 400,
      body: { status: "error", message: "Invalid notification" },
    }).as("createNotification");
    mountAndOpen();

    cy.get("#notification-send-all").check({ force: true });
    cy.get("#notification-title").type("Keep this title", { force: true });
    cy.contains("button", "Send").click({ force: true });
    cy.wait("@createNotification");

    cy.get("#notification-title").should("have.value", "Keep this title");
    cy.contains("Unable to send notification").should("exist");
    cy.get("@updateModelValue").should("not.have.been.called");
  });
});
