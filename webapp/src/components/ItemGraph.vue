<template>
  <div v-if="showOptions">
    <button
      class="btn btn-default mr-5 mb-2 float-right configure-button"
      @click="optionsDisplayed = !optionsDisplayed"
    >
      configure
    </button>
    <div
      v-show="optionsDisplayed"
      class="card card-body col-lg-4 col-md-5 col-sm-6"
      style="float: right !important"
    >
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
    </div>
  </div>
  <div id="cy" v-bind="$attrs" />
</template>

<script>
import ItemSelect from "@/components/ItemSelect.vue";
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
    };
  },
  computed: {
    filteredGraphData() {
      const ignoredItemIds = this.ignoreItems.map((d) => d.item_id);
      return {
        edges: this.graphData.edges.filter(
          (edge) =>
            !(
              ignoredItemIds.includes(edge.data.source) || ignoredItemIds.includes(edge.data.target)
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
  },
  async mounted() {
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
              "background-color": "#11479e",
              label: "data(id)",
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

<style>
.configure-button {
  position: relative;
  z-index: 99;
}

#flex-container {
  flex-flow: column;
}

#cy {
  width: 100%;
  height: 800px;
  /* display: block;*/
}
</style>
