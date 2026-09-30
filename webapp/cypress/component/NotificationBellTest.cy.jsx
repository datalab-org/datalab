import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faArchive,
  faArrowLeft,
  faBell,
  faCheck,
  faEnvelope,
  faEnvelopeOpen,
  faSpinner,
  faTimes,
  faTrash,
  faUndo,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { createMemoryHistory, createRouter } from "vue-router";

import NotificationBell from "@/components/notifications/NotificationBell.vue";

library.add(
  faArchive,
  faArrowLeft,
  faBell,
  faCheck,
  faEnvelope,
  faEnvelopeOpen,
  faSpinner,
  faTimes,
  faTrash,
  faUndo,
);

const notification = {
  immutable_id: "notification-1",
  recipient_id: "user-1",
  title: "Ingestion warning",
  summary: "The latest ingestion attempt needs attention.",
  message: "The source file could not be parsed.",
  level: "important",
  created_at: "2026-09-30T10:00:00+00:00",
  last_occurred_at: "2026-09-30T10:05:00+00:00",
  occurrence_count: 2,
  read_at: null,
  archived_at: null,
  occurrences: [
    {
      occurred_at: "2026-09-30T10:00:00+00:00",
      summary: "First attempt",
      message: "The first attempt failed.",
      level: "important",
      is_new: true,
    },
    {
      occurred_at: "2026-09-30T10:05:00+00:00",
      summary: "Second attempt",
      message: "The second attempt failed.",
      level: "urgent",
      is_new: true,
    },
  ],
};

function mountBell() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/notifications", component: { template: "<div>All notifications</div>" } }],
  });

  return cy.mount(NotificationBell, {
    global: {
      plugins: [router],
      components: { FontAwesomeIcon },
    },
  });
}

describe("NotificationBell", () => {
  beforeEach(() => {
    let readAt = null;

    cy.intercept("GET", "**/notifications/unread-count", {
      statusCode: 200,
      body: { status: "success", unread_count: 1 },
    }).as("unreadCount");

    cy.intercept("GET", "**/notifications?*", (request) => {
      request.reply({
        statusCode: 200,
        body: {
          status: "success",
          unread_count: readAt ? 0 : 1,
          data: [{ ...notification, read_at: readAt }],
        },
      });
    }).as("notifications");

    cy.intercept("PATCH", "**/notifications/notification-1", (request) => {
      if (request.body.read === true) readAt = "2026-09-30T10:10:00+00:00";
      if (request.body.read === false) readAt = null;
      request.reply({
        statusCode: 200,
        body: {
          status: "success",
          unread_count: readAt ? 0 : 1,
          data: { ...notification, read_at: readAt },
        },
      });
    }).as("updateNotification");
  });

  it("shows the unread count and grouped details", () => {
    mountBell();

    cy.wait("@unreadCount");
    cy.get(".notification-badge").should("contain.text", "1");
    cy.get("[aria-label='Notifications']").click();
    cy.wait("@notifications");
    cy.contains("Ingestion warning").click();
    cy.wait("@updateNotification");

    cy.get(".notification-detail-pane").within(() => {
      cy.contains("First attempt").should("exist");
      cy.contains("Second attempt").should("exist");
      cy.contains("The second attempt failed.").should("exist");
      cy.contains("2 occurrences").should("exist");
    });
    cy.get(".notification-badge").should("not.exist");
  });

  it("keeps the popover inside a narrow viewport and links to the full view", () => {
    cy.viewport(480, 640);
    mountBell();

    cy.get("[aria-label='Notifications']").click();
    cy.wait("@notifications");
    cy.get("[data-testid='notification-popover']").should(($popover) => {
      const bounds = $popover[0].getBoundingClientRect();
      expect(bounds.left).to.be.at.least(0);
      expect(bounds.right).to.be.at.most(480);
      expect(bounds.bottom).to.be.at.most(640);
    });
    cy.contains("View all notifications").should("have.attr", "href", "/notifications");
  });
});
