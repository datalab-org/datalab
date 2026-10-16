import { library } from "@fortawesome/fontawesome-svg-core";
import { faSpinner, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";

import NotificationTable from "@/components/notifications/NotificationTable.vue";
import { DialogService } from "@/services/DialogService.js";

library.add(faSpinner, faTrash);

const notification = {
  immutable_id: "notification-1",
  recipient_id: "user-1",
  recipient_info: {
    immutable_id: "user-1",
    display_name: "Test User",
    gravatar_hash: "",
  },
  created_by_info: {
    immutable_id: "admin-1",
    display_name: "Test Admin",
    gravatar_hash: "",
  },
  title: "Planned maintenance",
  summary: "A short service interruption.",
  message: "The service will restart at noon.",
  level: "important",
  created_at: "2026-09-30T10:00:00+00:00",
  last_occurred_at: "2026-09-30T10:00:00+00:00",
  occurrence_count: 1,
  read_at: null,
  archived_at: null,
};

function mountTable({ adminMode = false } = {}) {
  const store = createStore({
    state() {
      return {
        datatablePaginationSettings: {
          notifications: { page: 0, rows: 20 },
          adminNotifications: { page: 0, rows: 20 },
        },
      };
    },
    getters: { isAdminSuperUserModeActive: () => false },
  });

  return cy.mount(NotificationTable, {
    props: {
      notifications: [notification],
      adminMode,
      onRowClick: cy.spy().as("rowClick"),
      onNotificationDeleted: cy.spy().as("notificationDeleted"),
    },
    global: {
      plugins: [store, PrimeVue],
      components: { FontAwesomeIcon },
    },
  });
}

describe("NotificationTable", () => {
  it("uses recipient mode without recipient or action columns", () => {
    mountTable();

    cy.get("[data-testid='notification-table']").should("exist");
    cy.get(".p-datatable-column-title").should("not.contain.text", "Recipient");
    cy.get(".p-datatable-column-title").should("not.contain.text", "Actions");
    cy.contains("Planned maintenance").click();
    cy.get("@rowClick").should("have.been.calledOnce");
  });

  it("shows recipient and individual deletion in admin mode", () => {
    cy.stub(DialogService, "confirm").resolves(true);
    cy.intercept("DELETE", "**/admin/notifications/notification-1", {
      statusCode: 200,
      body: { status: "success", deleted_count: 1 },
    }).as("deleteNotification");
    mountTable({ adminMode: true });

    cy.get("[data-testid='admin-notification-table']").should("exist");
    cy.get(".p-datatable-column-title").should("contain.text", "Recipient");
    cy.contains("Test User").should("exist");
    cy.get("[aria-label='Delete notification delivery']").click();
    cy.wait("@deleteNotification");
    cy.get("@notificationDeleted").should("have.been.calledOnce");
  });
});
