import DataTableRowActions from "@/components/DataTableRowActions.vue";
import DataTableHeaderActions from "@/components/DataTableHeaderActions.vue";
import DynamicDataTable from "@/components/DynamicDataTable.vue";
import PrimeVue from "primevue/config";
import { createStore } from "vuex";
import { ITEM_ID_COLUMN } from "@/utils/tableColumns.js";
import {
  DELETE_ACTION,
  ITEM_ACTIONS,
  batchActionsFor,
  rowActionsFor,
} from "@/utils/itemActions.js";

const ROW = { item_id: "sample1", refcode: "test:sample1", type: "samples" };

describe("Item action descriptors", () => {
  it("offers row deletion of tags only from their own actions column", () => {
    expect(batchActionsFor("tags")).to.deep.equal([DELETE_ACTION]);
    expect(rowActionsFor("tags")).to.deep.equal([]);
  });

  it("offers every item action on samples", () => {
    expect(batchActionsFor("samples")).to.deep.equal(ITEM_ACTIONS);
    expect(rowActionsFor("samples")).to.deep.equal(ITEM_ACTIONS);
  });

  it("offers no item actions on users", () => {
    expect(batchActionsFor("users")).to.deep.equal([]);
    expect(rowActionsFor("users")).to.deep.equal([]);
  });
});

describe("DataTableRowActions", () => {
  it("emits an action request for its row", () => {
    const onActionRequest = cy.spy().as("actionRequest");
    cy.mount(DataTableRowActions, { props: { row: ROW, actions: ITEM_ACTIONS, onActionRequest } });

    cy.get('[data-testid="row-delete-button"]').click();
    cy.get("@actionRequest").should("have.been.calledOnceWith", {
      action: "delete",
      items: [ROW],
      source: "row",
    });
  });

  it("names the row in each button's accessible label", () => {
    cy.mount(DataTableRowActions, { props: { row: ROW, actions: ITEM_ACTIONS } });

    cy.get('[data-testid="row-add-to-collection-button"]')
      .should("have.attr", "aria-label", "Add to collection sample1")
      .and("have.attr", "type", "button");
    cy.get('[data-testid="row-share-button"]').should("have.attr", "aria-label", "Share sample1");
    cy.get('[data-testid="row-delete-button"]').should("have.attr", "aria-label", "Delete sample1");
  });
});

describe("DataTableHeaderActions", () => {
  it("is disabled while no filter is active", () => {
    cy.mount(DataTableHeaderActions, { props: { hasActiveFilters: false } });
    cy.get('[data-testid="clear-filters-button"]').should("be.disabled");
  });

  it("requests the filters be cleared", () => {
    const onClearFilters = cy.spy().as("clearFilters");
    cy.mount(DataTableHeaderActions, { props: { hasActiveFilters: true, onClearFilters } });
    cy.get('[data-testid="clear-filters-button"]').should("not.be.disabled").click();
    cy.get("@clearFilters").should("have.been.calledOnce");
  });
});

describe("DynamicDataTable actions column", () => {
  let wrapper;

  const mountTable = (dataType) => {
    const store = createStore({
      state() {
        return {
          currentUserID: "self",
          datatablePaginationSettings: { [dataType]: { page: 0, rows: 20 } },
        };
      },
      getters: { isAdminSuperUserModeActive: () => false },
      mutations: { setPage() {}, setRows() {} },
    });
    cy.mount(DynamicDataTable, {
      props: {
        columns: [ITEM_ID_COLUMN],
        data: [ROW, { ...ROW, item_id: "sample2", refcode: "test:sample2" }],
        dataType,
        globalFilterFields: ["item_id"],
      },
      global: { plugins: [store, PrimeVue] },
    }).then((mounted) => {
      wrapper = mounted.wrapper;
    });
  };

  beforeEach(() => {
    localStorage.clear();
  });

  it("shows the row actions on every row", () => {
    mountTable("samples");
    cy.get(".p-datatable-tbody > tr").each((row) => {
      cy.wrap(row).find(".row-action-button").should("have.length", ITEM_ACTIONS.length);
    });
  });

  it("clears the column filters but keeps the global search", () => {
    mountTable("samples");
    cy.get('[data-testid="clear-filters-button"]').should("be.disabled");

    cy.then(() => {
      const table = wrapper.vm;
      table.filters.item_id.constraints[0].value = "sample1";
      table.filters.global.value = "sample";
      return table.$nextTick();
    });
    cy.get('[data-testid="clear-filters-button"]').should("not.be.disabled").click();

    cy.then(() => {
      expect(wrapper.vm.filters.item_id.constraints[0].value).to.equal(null);
      expect(wrapper.vm.filters.global.value).to.equal("sample");
    });
    cy.get('[data-testid="clear-filters-button"]').should("be.disabled");
  });
});
