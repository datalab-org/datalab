import { library } from "@fortawesome/fontawesome-svg-core";
import { fas } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import store from "@/store/index.js";
import BlockList from "@/components/BlockList.vue";

library.add(fas);

const ITEM_ID = "item_1";

function commentBlock(block_id) {
  return { block_id, blocktype: "comment", title: `Block ${block_id}`, item_id: ITEM_ID };
}

function seedStore(displayOrder, blockIds) {
  store.state.currentUserID = "user_1";
  store.state.currentUserInfoLoading = false;
  store.commit("setBlocksInfos", [{ id: "comment", attributes: { name: "Comment" } }]);
  store.state.all_item_data = {
    [ITEM_ID]: {
      item_id: ITEM_ID,
      display_order: displayOrder,
      blocks_obj: Object.fromEntries(blockIds.map((id) => [id, commentBlock(id)])),
    },
  };
}

function section(section_id, title) {
  return { type: "section", section_id, title, description: null };
}

function mountList() {
  cy.intercept("POST", "**/update-block/", (req) => {
    req.reply({
      delay: 200,
      body: {
        status: "success",
        new_block_data: req.body.block_data,
        saved_successfully: true,
      },
    });
  }).as("updateBlock");
  return cy.mount(BlockList, {
    props: { item_id: ITEM_ID },
    global: {
      plugins: [store],
      components: { "font-awesome-icon": FontAwesomeIcon },
    },
  });
}

function expectRequestedBlockIds(assertion) {
  cy.get("@updateBlock.all").should((calls) => {
    assertion(calls.map((call) => call.request.body.block_id));
  });
}

describe("BlockList", () => {
  beforeEach(() => {
    seedStore(
      ["block_top", section("section_sem", "SEM images"), "block_sem_1", "block_sem_2"],
      ["block_top", "block_sem_1", "block_sem_2"],
    );
  });

  it("only loads ungrouped blocks on mount", () => {
    mountList();
    cy.wait("@updateBlock");
    cy.get("#block_top").should("exist");
    cy.get("#block_sem_1").should("not.exist");
    cy.get("#block_sem_2").should("not.exist");
    cy.wait(500);
    expectRequestedBlockIds((ids) => expect(ids).to.deep.equal(["block_top"]));
  });

  it("starts sections collapsed", () => {
    mountList();
    cy.get("#section_sem .section-body").should("not.be.visible");
    cy.get("#section_sem .section-block-count").should("contain", "2 blocks");
    cy.wait("@updateBlock");
  });

  it("loads a section's blocks one at a time once it is expanded", () => {
    mountList();
    cy.wait("@updateBlock");
    cy.get("#section_sem > .section-header .collapse-arrow").click();

    cy.get("#section_sem .section-loading-indicator").should("be.visible");
    cy.get("#section_sem .data-block").should("have.length", 1);
    cy.get("#block_sem_1").should("exist");
    cy.get("#block_sem_2").should("not.exist");

    cy.get("#section_sem .data-block").should("have.length", 2);
    cy.get("#section_sem .section-loading-indicator").should("not.exist");
    expectRequestedBlockIds((ids) =>
      expect(ids).to.deep.equal(["block_top", "block_sem_1", "block_sem_2"]),
    );
  });

  it("does not reload a section's blocks when it is collapsed and expanded again", () => {
    mountList();
    cy.get("#section_sem > .section-header .collapse-arrow").click();
    cy.get("#section_sem .data-block").should("have.length", 2);
    cy.get("#section_sem .section-loading-indicator").should("not.exist");

    cy.get("#section_sem > .section-header .collapse-arrow").click();
    cy.get("#section_sem .section-body").should("not.be.visible");
    cy.get("#section_sem > .section-header .collapse-arrow").click();
    cy.get("#section_sem .data-block").should("have.length", 2);
    cy.wait(500);
    expectRequestedBlockIds((ids) => expect(ids).to.have.length(3));
  });

  it("expands a collapsed section when a block is added to it", () => {
    mountList();
    cy.wait("@updateBlock");
    cy.then(() => {
      const item = store.state.all_item_data[ITEM_ID];
      item.blocks_obj.block_new = commentBlock("block_new");
      item.display_order.push("block_new");
    });

    cy.get("#section_sem .section-body").should("be.visible");
    cy.get("#block_new").should("exist");
    cy.get("#section_sem .data-block").should("have.length", 3);
    expectRequestedBlockIds((ids) => expect(ids).not.to.include("block_new"));
  });

  it("expands a collapsed section when a block is moved into it", () => {
    mountList();
    cy.wait("@updateBlock");
    cy.then(() => {
      store.commit("swapBlockDisplayOrder", { item_id: ITEM_ID, index1: 0, index2: 1 });
    });

    cy.get("#section_sem .section-body").should("be.visible");
    cy.get("#block_top").should("be.visible");
  });

  it("collapses sections again when the blocks are reloaded", () => {
    mountList().then(({ component }) => {
      cy.get("#section_sem > .section-header .collapse-arrow").click();
      cy.get("#section_sem .section-body").should("be.visible");
      cy.then(() => component.reloadBlocks());
      cy.get("#section_sem .section-body").should("not.be.visible");
    });
  });

  it("shows newly added sections expanded", () => {
    mountList();
    cy.then(() => {
      store.state.all_item_data[ITEM_ID].display_order.push(section("section_new", "New"));
    });
    cy.get("#section_new .section-body").should("be.visible");
    cy.get("#section_sem .section-body").should("not.be.visible");
  });

  it("loads the blocks of a removed section", () => {
    mountList();
    cy.wait("@updateBlock");
    cy.then(() => {
      store.commit("removeSection", { item_id: ITEM_ID, section_id: "section_sem" });
    });

    cy.get("#block_sem_1").should("exist");
    cy.get("#block_sem_2").should("exist");
    expectRequestedBlockIds((ids) =>
      expect(ids).to.include.members(["block_sem_1", "block_sem_2"]),
    );
  });
});
