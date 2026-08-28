import ItemGraph from "@/components/ItemGraph.vue";
import { createStore } from "vuex";

// Minimal store to avoid errors from child components
const store = createStore({
  state: {
    itemGraphData: null,
    itemGraphIsLoading: false,
  },
});

const singleNode = {
  nodes: [{ data: { id: "SAMPLE1", name: "Test Sample", type: "samples", special: false } }],
  edges: [],
};

const twoConnectedNodes = {
  nodes: [
    { data: { id: "SAMPLE1", name: "Test Sample", type: "samples", special: false } },
    {
      data: {
        id: "SM1",
        name: "Starting Material 1",
        type: "starting_materials",
        special: false,
      },
    },
  ],
  edges: [{ data: { id: "SM1->SAMPLE1", source: "SM1", target: "SAMPLE1", value: 1 } }],
};

const graphWithSpecialNode = {
  nodes: [
    { data: { id: "SAMPLE1", name: "Test Sample", type: "samples", special: true } },
    { data: { id: "SAMPLE2", name: "Parent Sample", type: "samples", special: false } },
  ],
  edges: [{ data: { id: "SAMPLE2->SAMPLE1", source: "SAMPLE2", target: "SAMPLE1", value: 1 } }],
};

const disconnectedNodes = {
  nodes: [
    { data: { id: "SAMPLE1", name: "Sample A", type: "samples", special: false } },
    { data: { id: "SAMPLE2", name: "Sample B", type: "samples", special: false } },
    { data: { id: "SAMPLE3", name: "Sample C", type: "samples", special: false } },
  ],
  edges: [],
};

const mixedTypeGraph = {
  nodes: [
    { data: { id: "SAMPLE1", name: "My Sample", type: "samples", special: false } },
    { data: { id: "CELL1", name: "My Cell", type: "cells", special: false } },
    {
      data: { id: "SM1", name: "Starting Material", type: "starting_materials", special: false },
    },
    { data: { id: "EQUIP1", name: "Furnace", type: "equipment", special: false } },
  ],
  edges: [
    { data: { id: "SM1->SAMPLE1", source: "SM1", target: "SAMPLE1", value: 1 } },
    { data: { id: "SAMPLE1->CELL1", source: "SAMPLE1", target: "CELL1", value: 1 } },
  ],
};

const selfLoopGraph = {
  nodes: [{ data: { id: "SAMPLE1", name: "Self-ref Sample", type: "samples", special: false } }],
  edges: [{ data: { id: "SAMPLE1->SAMPLE1", source: "SAMPLE1", target: "SAMPLE1", value: 1 } }],
};

const danglingEdgeGraph = {
  nodes: [{ data: { id: "SAMPLE1", name: "Test Sample", type: "samples", special: false } }],
  edges: [{ data: { id: "MISSING->SAMPLE1", source: "MISSING", target: "SAMPLE1", value: 1 } }],
};

const mountGraph = (graphData, opts = {}) => {
  cy.mount(ItemGraph, {
    props: {
      graphData,
      showOptions: opts.showOptions ?? false,
      defaultGraphStyle: opts.defaultGraphStyle ?? "elk-stress",
    },
    global: {
      plugins: [store],
    },
  });
};

// Helper to access the cytoscape instance from the Vue component
const getCyInstance = () => cy.wrap(null).then(() => Cypress.vueWrapper.vm.cy);

describe("ItemGraph", () => {
  it("renders a single node", () => {
    mountGraph(singleNode);
    getCyInstance().then((cyInstance) => {
      expect(cyInstance.nodes().length).to.equal(1);
      expect(cyInstance.edges().length).to.equal(0);
      expect(cyInstance.nodes('[id="SAMPLE1"]').length).to.equal(1);
    });
  });

  it("renders two connected nodes with an edge", () => {
    mountGraph(twoConnectedNodes);
    getCyInstance().then((cyInstance) => {
      expect(cyInstance.nodes().length).to.equal(2);
      expect(cyInstance.edges().length).to.equal(1);
      expect(cyInstance.edges()[0].data("source")).to.equal("SM1");
      expect(cyInstance.edges()[0].data("target")).to.equal("SAMPLE1");
    });
  });

  it("renders disconnected nodes without errors", () => {
    mountGraph(disconnectedNodes);
    getCyInstance().then((cyInstance) => {
      expect(cyInstance.nodes().length).to.equal(3);
      expect(cyInstance.edges().length).to.equal(0);
    });
  });

  it("renders a graph with mixed item types", () => {
    mountGraph(mixedTypeGraph);
    getCyInstance().then((cyInstance) => {
      expect(cyInstance.nodes().length).to.equal(4);
      expect(cyInstance.edges().length).to.equal(2);
      expect(cyInstance.nodes('[type="samples"]').length).to.equal(1);
      expect(cyInstance.nodes('[type="cells"]').length).to.equal(1);
      expect(cyInstance.nodes('[type="starting_materials"]').length).to.equal(1);
      expect(cyInstance.nodes('[type="equipment"]').length).to.equal(1);
    });
  });

  it("renders a graph with a self-loop", () => {
    mountGraph(selfLoopGraph);
    getCyInstance().then((cyInstance) => {
      expect(cyInstance.nodes().length).to.equal(1);
      expect(cyInstance.edges().length).to.equal(1);
      expect(cyInstance.edges()[0].data("source")).to.equal("SAMPLE1");
      expect(cyInstance.edges()[0].data("target")).to.equal("SAMPLE1");
    });
  });

  it("highlights the special node with a border", () => {
    mountGraph(graphWithSpecialNode);
    getCyInstance().then((cyInstance) => {
      const specialNode = cyInstance.nodes('[id="SAMPLE1"]');
      const normalNode = cyInstance.nodes('[id="SAMPLE2"]');
      expect(specialNode.data("special")).to.equal(true);
      expect(normalNode.data("special")).to.equal(false);
      expect(specialNode.style("border-width")).to.not.equal("0px");
      expect(normalNode.style("border-width")).to.equal("0px");
    });
  });

  it("nodes have distinct colors per type", () => {
    mountGraph(mixedTypeGraph);
    getCyInstance().then((cyInstance) => {
      const colors = new Set();
      cyInstance.nodes().forEach((node) => {
        colors.add(node.style("background-color"));
      });
      expect(colors.size).to.equal(4);
    });
  });

  it("shows options panel when showOptions is true", () => {
    mountGraph(twoConnectedNodes, { showOptions: true });
    cy.contains("configure").should("be.visible");
  });

  it("hides options panel when showOptions is false", () => {
    mountGraph(twoConnectedNodes, { showOptions: false });
    cy.contains("configure").should("not.exist");
  });

  it("handles an edge referencing a non-existent node", () => {
    mountGraph(danglingEdgeGraph);
    getCyInstance().then((cyInstance) => {
      // cytoscape silently drops edges with missing source/target
      expect(cyInstance.nodes().length).to.equal(1);
      expect(cyInstance.edges().length).to.equal(0);
    });
  });

  describe("layout algorithms", () => {
    const layouts = ["euler", "cola", "fcose", "elk-stress", "elk-disco", "random"];
    layouts.forEach((layout) => {
      it(`renders and settles with the ${layout} layout`, () => {
        mountGraph(twoConnectedNodes, { defaultGraphStyle: layout });
        // Wait for the layout run to finish before asserting (and before the
        // teardown unmount, which must not happen mid-run)
        cy.get('#cy[data-layout-running="false"]', { timeout: 10000 });
        getCyInstance().then((cyInstance) => {
          expect(cyInstance.nodes().length).to.equal(2);
          expect(cyInstance.edges().length).to.equal(1);
          cyInstance.nodes().forEach((node) => {
            expect(Number.isFinite(node.position("x")), `${node.id()} x position`).to.equal(true);
            expect(Number.isFinite(node.position("y")), `${node.id()} y position`).to.equal(true);
          });
          expect(cyInstance.nodes().boundingBox().w).to.be.greaterThan(0);
        });
      });
    });
  });
});
