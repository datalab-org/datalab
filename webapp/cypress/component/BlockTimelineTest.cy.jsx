import BlockTimeline from "@/components/BlockTimeline.vue";
import { createStore } from "vuex";
import { h } from "vue";

const ITEM_ID = "test-item";

const BlockStub = {
  props: ["item_id", "block_id"],
  render() {
    return h("div", { class: "stub-block", "data-block-id": this.block_id }, this.block_id);
  },
};

const mountTimeline = (displayOrder, blocksObj) => {
  const store = createStore({
    state: {
      all_item_data: { [ITEM_ID]: { display_order: displayOrder, blocks_obj: blocksObj } },
    },
  });
  cy.mount(BlockTimeline, {
    props: { item_id: ITEM_ID, blockComponent: () => BlockStub },
    global: { plugins: [store], stubs: { "font-awesome-icon": true } },
  });
};

describe("BlockTimeline.vue", () => {
  it("renders blocks chronologically under one divider per day", () => {
    mountTimeline(["late", "early", "undated"], {
      late: { created_at: "2026-11-06T09:00:00Z" },
      early: { metadata: { measured_at: "2023-10-23T12:00:00Z" } },
      undated: {},
    });

    cy.get(".stub-block").then((blocks) => {
      expect([...blocks].map((b) => b.dataset.blockId)).to.deep.equal(["early", "late", "undated"]);
    });
    cy.get('[data-testid="timeline-divider"]').should("have.length", 3);
    cy.get('[data-testid="timeline-divider"]').last().should("contain", "Date unknown");
  });

  it("renders nothing but an empty container when there are no blocks", () => {
    mountTimeline([], {});
    cy.get('[data-testid="block-timeline"]').should("exist");
    cy.get('[data-testid="timeline-divider"]').should("not.exist");
  });
});
