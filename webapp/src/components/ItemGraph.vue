<template>
  <div v-if="showOptions" class="options">
    <button
      class="btn btn-default mr-5 mb-2 dropdown-toggle"
      @click="optionsDisplayed = !optionsDisplayed"
    >
      configure
    </button>
    <div v-show="optionsDisplayed" class="card card-body dropdown-menu">
      <label for="graph-style">Graph layout:</label>
      <div id="graph-style" class="btn-group mr-2" role="group">
        <button
          :class="graphStyle == 'elk-stress' ? 'btn btn-default active' : 'btn btn-default'"
          @click="graphStyle = 'elk-stress'"
        >
          stress
        </button>
        <button
          :class="graphStyle == 'cola' ? 'btn btn-default active' : 'btn btn-default'"
          @click="graphStyle = 'cola'"
        >
          force
        </button>
        <button
          :class="graphStyle == 'elk-layered-down' ? 'btn btn-default active' : 'btn btn-default'"
          @click="graphStyle = 'elk-layered-down'"
        >
          horizontal
        </button>
        <button
          :class="graphStyle == 'elk-layered-right' ? 'btn btn-default active' : 'btn btn-default'"
          @click="graphStyle = 'elk-layered-right'"
        >
          vertical
        </button>
      </div>

      <label for="ignore-items">Ignore connections to items:</label>
      <ItemSelect id="ignore-items" v-model="ignoreItems" multiple />

      <label for="ignore-collections">Ignore connections to collections:</label>
      <CollectionSelect id="ignore-collections" v-model="ignoreCollections" multiple />

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
    </div>
  </div>
  <div id="cy" v-bind="$attrs" />
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";
import CollectionSelect from "@/components/CollectionSelect.vue";
import { itemTypes } from "@/resources.js";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import cola from "cytoscape-cola";
import elk from "cytoscape-elk";

cytoscape.use(dagre);
cytoscape.use(cola);
cytoscape.use(elk);

const layoutOptions = {
  "elk-layered-down": {
    name: "elk",
    elk: {
      algorithm: "layered",
      "elk.direction": "DOWN",
    },
  },
  "elk-layered-right": {
    name: "elk",
    elk: {
      algorithm: "layered",
      "elk.direction": "RIGHT",
    },
  },
  "elk-stress": {
    name: "elk",
    elk: {
      algorithm: "stress",
    },
  },
  cola: {
    name: "cola",
    animate: "true",
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
      default: "elk-stress",
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
      ignoreCollections: [],
      labelStartingMaterialsByName: true,
    };
  },
  computed: {
    filteredGraphData() {
      const ignoredItemIds = this.ignoreItems.map((d) => d.item_id);
      const ignoredCollectionIds = this.ignoreCollections.map(
        (d) => `Collection: ${d.collection_id}`,
      );
      return {
        edges: this.graphData.edges.filter(
          (edge) =>
            !(
              ignoredItemIds.includes(edge.data.source) ||
              ignoredItemIds.includes(edge.data.target) ||
              ignoredCollectionIds.includes(edge.data.source)
            ),
        ),
        nodes: this.graphData.nodes,
      };
    },
  },
  watch: {
    graphData() {
      this.generateCyNetworkPlot();
    },
    graphStyle() {
      console.log("graphStyle changed");
      this.generateCyNetworkPlot();
    },
    ignoreItems() {
      this.generateCyNetworkPlot();
    },
    ignoreCollections() {
      this.generateCyNetworkPlot();
    },
    labelStartingMaterialsByName() {
      this.generateCyNetworkPlot();
    },
  },
  async created() {
    this.generateCyNetworkPlot();
  },
  methods: {
    generateCyNetworkPlot() {
      if (!this.graphData) {
        return;
      }
      var cy = cytoscape({
        container: document.getElementById("cy"),
        elements: this.filteredGraphData,
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
            selector: "edge",
            style: {
              width: 4,
              "target-arrow-shape": "triangle",
              "line-color": "#9dbaea",
              "target-arrow-color": "#9dbaea",
              "curve-style": "bezier",
            },
          },
        ],
        layout: layoutOptions[this.graphStyle],
      });

      // set colors of each of the nodes by type
      cy.nodes().each(function (element) {
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

      // tapdragover and tapdragout are mouseover and mouseout events
      // that also work with touch screens
      cy.on("tapdragover", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 0.8);
        node.style("border-width", 3);
        node.style("border-color", "black");
      });
      cy.on("tapdragout", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 1);
        node.style("border-width", node.data("special") == 1 ? 2 : 0);
        node.style("border-color", "grey");
      });

      cy.on("click", "node", function (evt) {
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
.options {
  position: absolute;
  z-index: 10;
  right: 2rem;
}

#cy {
  width: 100%;
  height: 90vh;
  /* display: block;*/
}
</style>
