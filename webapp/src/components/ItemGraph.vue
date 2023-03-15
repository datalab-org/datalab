<template>
  <div class="dflex text-right">
    <div class="btn-group mr-2" role="group">
      <button class="btn btn-default active" @click="graphStyle = 'elk-stress'">stress</button>
      <button class="btn btn-default" @click="graphStyle = 'cola'">force</button>
      <button class="btn btn-default" @click="graphStyle = 'elk-layered-down'">horizontal</button>
      <button class="btn btn-default" @click="graphStyle = 'elk-layered-right'">vertical</button>
    </div>
  </div>
  <div id="cy" v-bind="$attrs" />
</template>

<script>
// import { getItemGraph } from "@/server_fetch_utils.js";
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
  props: {
    graphData: Object,
  },
  data() {
    return {
      graphStyle: "elk-stress",
    };
  },
  methods: {
    generateCyNetworkPlot() {
      if (!this.graphData) {
        return;
      }
      var cy = cytoscape({
        container: document.getElementById("cy"),
        elements: this.graphData,
        userPanningEnabled: true,
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
        element.style("background-color", itemTypes[element.data("type")].navbarColor);
      });

      cy.nodes().each(function (element) {
        element.style("border-width", element.data("special") == 1 ? 4 : 0);
        element.style("border-color", "grey");
      });

      // tapdragover and tapdragout are mouseover and mouseout events
      // that also work with touch screens
      cy.on("tapdragover", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 0.5);
      });
      cy.on("tapdragout", "node", function (evt) {
        var node = evt.target;
        node.style("opacity", 1);
      });

      cy.on("click", "node", function (evt) {
        var node = evt.target;
        window.open(`/edit/${node.data("id")}`, "_blank");
      });
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
  },
  async mounted() {
    this.generateCyNetworkPlot();
  },
};
</script>

<style scoped>
#flex-container {
  flex-flow: column;
}

#cy {
  width: 100%;
  height: 800px;
  /*  display: block;*/
}
</style>
