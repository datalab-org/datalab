<template>
  <div v-if="showOptions" class="sidebar ml-4">
    <button
      class="btn btn-default options-button mb-2"
      @click="optionsDisplayed = !optionsDisplayed"
    >
      configure
    </button>
    <div v-show="optionsDisplayed">
      <label for="graph-style"
        >Graph layout:
        <font-awesome-icon v-show="layoutIsRunning" class="ml-2 text-muted" icon="spinner" spin
      /></label>
      <div id="graph-style" class="btn-group mr-2" role="group">
        <button
          :class="graphStyle == 'euler' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'euler';
            updateAndRunLayout();
          "
        >
          euler
        </button>
        <button
          :class="graphStyle == 'cola' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'cola';
            updateAndRunLayout();
          "
        >
          cola
        </button>
        <button
          :class="graphStyle == 'fcose' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'fcose';
            updateAndRunLayout();
          "
        >
          fCoSE
        </button>
        <button
          :class="graphStyle == 'elk-disco' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'elk-disco';
            updateAndRunLayout();
          "
        >
          pack
        </button>
        <button
          :class="graphStyle == 'random' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'random';
            updateAndRunLayout();
          "
        >
          random
        </button>
        <button
          :class="graphStyle == 'elk-stress' ? 'btn btn-default active' : 'btn btn-default'"
          @click="
            graphStyle = 'elk-stress';
            updateAndRunLayout();
          "
        >
          stress (slow)
        </button>
      </div>

      <label for="ignore-items">Ignore connections to items:</label>
      <ItemSelect
        id="ignore-items"
        v-model="ignoreItems"
        multiple
        @option:selected="removeItemFromGraph"
        @option:deselected="readdItemToGraph"
      />

      <label for="ignore-collections">Ignore connections to collections:</label>
      <CollectionSelect
        id="ignore-collections"
        v-model="ignoreCollections"
        multiple
        @option:selected="removeItemFromGraph"
        @option:deselected="readdItemToGraph"
      />

      <div class="form-group form-check mt-3">
        <input
          id="label-starting-materials-by-name"
          v-model="labelStartingMaterialsByName"
          class="form-check-input"
          type="checkbox"
        />
        <label class="form-check-label" for="label-starting-materials-by-name">
          label starting materials by name</label
        >
      </div>
      <div class="form-group form-check mt-3">
        <input
          id="label-items-by-name"
          v-model="labelItemsByName"
          class="form-check-input"
          type="checkbox"
        />
        <label class="form-check-label" for="label-items-by-name">
          label samples/cells by name</label
        >
      </div>
    </div>
  </div>
  <div id="cy" v-bind="$attrs" />
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";
import CollectionSelect from "@/components/CollectionSelect.vue";
import { itemTypes } from "@/resources.js";
import cytoscape from "cytoscape";
import cola from "cytoscape-cola";
import elk from "cytoscape-elk";
import euler from "cytoscape-euler";
import fcose from "cytoscape-fcose";

cytoscape.use(cola);
cytoscape.use(euler);
cytoscape.use(elk);
cytoscape.use(fcose);

const layoutOptions = {
  "elk-disco": {
    name: "elk",
    animate: true,
    elk: {
      algorithm: "disco",
    },
  },
  random: {
    name: "random",
  },
  "elk-stress": {
    name: "elk",
    elk: {
      algorithm: "stress",
    },
  },
  cola: {
    name: "cola",
    animate: true,
    centerGraph: false,
  },
  euler: {
    name: "euler",
    animate: true,
    pull: 0.002,
  },
  fcose: {
    name: "fcose",
    animate: true,
    randomize: false,
    packComponents: true,
  },
};

export default {
  name: "ItemGraph",
  components: {
    ItemSelect,
    CollectionSelect,
  },
  props: {
    graphData: {
      type: Object,
      default: null,
    },
    defaultGraphStyle: {
      type: String,
      default: "euler",
    },
    showOptions: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      graphStyle: this.defaultGraphStyle,
      optionsDisplayed: false,
      ignoreItems: [],
      removedNodeData: {},
      ignoreCollections: [],
      labelStartingMaterialsByName: true,
      labelItemsByName: false,
      layoutIsRunning: true,
    };
  },
  watch: {
    graphData() {
      this.generateCyNetworkPlot();
    },
    labelStartingMaterialsByName() {
      // update the cytoscape stylesheet. Note: this adds styles, rather than overwriting the existing ones.
      // That seems to be OK for performance.
      this.cy
        .style()
        .selector('node[type = "starting_materials"]')
        .style("label", this.labelStartingMaterialsByName ? "data(name)" : "data(id)")
        .update();
    },
    labelItemsByName() {
      this.cy
        .style()
        .selector('node[type = "samples"], node[type = "cells"]')
        .style("label", this.labelItemsByName ? "data(name)" : "data(id)")
        .update();
    },
  },
  async created() {
    if (typeof this.cy !== "undefined") {
      this.generateCyNetworkPlot();
    }
  },
  methods: {
    removeItemFromGraph(event) {
      const itemToIgnore = event[event.length - 1];
      const id = itemToIgnore.item_id || `Collection: ${itemToIgnore.collection_id}`;
      const node = this.cy.$(`node[id="${id}"]`);
      console.log(event, id, node);
      if (node) {
        this.removedNodeData[id] = this.cy.remove(node.union(node.connectedEdges()));
      }
    },
    readdItemToGraph(event) {
      const id = event.item_id || `Collection: ${event.collection_id}`;
      if (this.removedNodeData && this.removedNodeData[id]) {
        this.removedNodeData[id].restore();
        delete this.removedNodeData[id];
      }
    },
    updateAndRunLayout() {
      this.layout && this.layout.stop();
      this.layoutIsRunning = true;
      this.layout = this.cy.layout(layoutOptions[this.graphStyle]);
      this.layout.run();
    },
    generateCyNetworkPlot() {
      if (!this.graphData) {
        return;
      }
      this.cy = cytoscape({
        container: document.getElementById("cy"),
        elements: this.graphData,
        userPanningEnabled: true,
        minZoom: 0.5,
        maxZoom: 1,
        animatedZooming: false,
        userZoomingEnabled: true,
        wheelSensitivity: 0.2,
        boxSelectionEnabled: false,
        style: [
          {
            selector: "node",
            style: {
              label: "data(id)",
            },
          },
          {
            selector: 'node[type = "starting_materials"]',
            style: {
              label: this.labelStartingMaterialsByName ? "data(name)" : "data(id)",
            },
          },
          {
            selector: 'node[type = "samples"], node[type = "cells"]',
            style: {
              label: this.labelItemsByName ? "data(name)" : "data(id)",
            },
          },
          {
            selector: "edge",
            style: {
              width: 4,
              "target-arrow-shape": "triangle",
              "line-color": "#9dbaea",
              "target-arrow-color": "#9dbaea",
              "curve-style": "bezier",
            },
          },
          {
            selector: 'edge[relation_type = "mentioned"]',
            style: {
              width: 2,
              "line-style": "dashed",
              "line-color": "#9dbaea",
              "target-arrow-color": "#9dbaea",
              "target-arrow-shape": "vee",
            },
          },
        ],
        layout: layoutOptions[this.graphStyle],
      });

      // set colors of each of the nodes by type
      this.cy.nodes().each(function (element) {
        element.style(
          "background-color",
          element.data("special") == 1
            ? itemTypes[element.data("type")].lightColor
            : itemTypes[element.data("type")].navbarColor,
        );
        element.style("border-width", element.data("special") == 1 ? 2 : 0);
        element.style("border-color", "grey");
        element.style("shape"), element.data("shape") == "triangle" ? "triangle" : "ellipse";
      });

      this.cy.on("layoutstart", () => {
        this.layoutIsRunning = true;
      });

      this.cy.on("layoutstop", () => {
        this.layoutIsRunning = false;
      });

      // tapdragover and tapdragout are mouseover and mouseout events
      // that also work with touch screens
      this.cy.on("tapdragover", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 0.8);
        node.style("border-width", 3);
        node.style("border-color", "black");
      });
      this.cy.on("tapdragout", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 1);
        node.style("border-width", node.data("special") == 1 ? 2 : 0);
        node.style("border-color", "grey");
      });
      this.cy.on("click", "node", function (evt) {
        var node = evt.target;
        if (node.data("type") == "collections") {
          window.open(`/collections/${node.data("id").replace("Collection: ", "")}`, "_blank");
        } else {
          window.open(`/edit/${node.data("id")}`, "_blank");
        }
      });
    },
  },
};
</script>

<style scoped>
.sidebar {
  position: fixed;
  max-width: 400px;
  z-index: 100;
  background-color: rgba(255, 255, 255, 0.95);
}

#cy {
  width: 100%;
  height: 90vh;
  /* display: block;*/
}
</style>
