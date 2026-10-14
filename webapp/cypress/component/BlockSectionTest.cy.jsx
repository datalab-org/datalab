import { createStore } from "vuex";
import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faChevronRight,
  faFolderOpen,
  faSpinner,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import BlockSection from "@/components/BlockSection.vue";
import {
  blockIdsOf,
  createSection,
  groupDisplayOrder,
  isSection,
  sectionIdOfBlock,
} from "@/utils/displayOrderSections.js";

library.add(faChevronRight, faFolderOpen, faSpinner, faTimes);

const SECTION = {
  type: "section",
  section_id: "section_sem",
  title: "SEM images",
  description: null,
};
const DISPLAY_ORDER = ["block_a", SECTION, "block_b", "block_c"];

function mountSection(props = {}) {
  const store = createStore({
    state: { all_item_data: { item_1: { display_order: DISPLAY_ORDER } } },
    mutations: { updateSection() {}, removeSection() {} },
  });
  const onToggle = cy.spy().as("toggle");
  return cy.mount(BlockSection, {
    props: { itemId: "item_1", sectionId: "section_sem", blockCount: 2, onToggle, ...props },
    slots: { default: () => <div class="slotted-block">a block</div> },
    global: {
      plugins: [store],
      components: { "font-awesome-icon": FontAwesomeIcon },
      stubs: { TiptapInline: true },
    },
  });
}

describe("BlockSection", () => {
  it("shows the title and block count in the header", () => {
    mountSection();
    cy.get(".section-title").should("have.value", "SEM images");
    cy.get(".section-block-count").should("contain", "2 blocks");
  });

  it("uses the singular for a single block", () => {
    mountSection({ blockCount: 1 });
    cy.get(".section-block-count").should("contain", "1 block").and("not.contain", "blocks");
  });

  it("hides its content when collapsed", () => {
    mountSection({ expanded: false });
    cy.get(".section-body").should("not.be.visible");
    cy.get(".section-header").should("not.have.class", "expanded");
  });

  it("shows its content when expanded", () => {
    mountSection({ expanded: true });
    cy.get(".section-body").should("be.visible");
    cy.get(".slotted-block").should("be.visible");
    cy.get(".section-header").should("have.class", "expanded");
  });

  it("asks its parent to toggle it instead of toggling itself", () => {
    mountSection({ expanded: false });
    cy.get(".collapse-arrow").click();
    cy.get("@toggle").should("have.been.calledOnce");
    cy.get(".section-body").should("not.be.visible");
  });

  it("shows a spinner while blocks are still loading", () => {
    mountSection({ expanded: true, loading: true });
    cy.get(".section-loading-indicator").should("be.visible");
  });

  it("hides the spinner once all blocks are loaded", () => {
    mountSection({ expanded: true, loading: false });
    cy.get(".section-loading-indicator").should("not.exist");
  });
});

describe("displayOrderSections utilities", () => {
  it("tells section markers apart from block IDs", () => {
    expect(isSection(SECTION)).to.equal(true);
    expect(isSection("block_a")).to.equal(false);
    expect(isSection(null)).to.equal(false);
  });

  it("creates collapsible section markers with unique IDs", () => {
    const first = createSection("One");
    const second = createSection("Two");
    expect(first).to.include({ type: "section", title: "One", description: null });
    expect(first.section_id).to.match(/^section_/);
    expect(first.section_id).not.to.equal(second.section_id);
  });

  it("groups the blocks that follow a section under it", () => {
    expect(groupDisplayOrder(DISPLAY_ORDER)).to.deep.equal([
      { type: "block", block_id: "block_a" },
      { type: "section", section: SECTION, block_ids: ["block_b", "block_c"] },
    ]);
  });

  it("handles a missing display order", () => {
    expect(groupDisplayOrder(undefined)).to.deep.equal([]);
    expect(blockIdsOf(undefined)).to.deep.equal([]);
  });

  it("lists only the block IDs", () => {
    expect(blockIdsOf(DISPLAY_ORDER)).to.deep.equal(["block_a", "block_b", "block_c"]);
  });

  it("finds the section a block belongs to", () => {
    expect(sectionIdOfBlock(DISPLAY_ORDER, "block_c")).to.equal("section_sem");
    expect(sectionIdOfBlock(DISPLAY_ORDER, "block_a")).to.equal(null);
    expect(sectionIdOfBlock(DISPLAY_ORDER, "missing")).to.equal(null);
  });
});
