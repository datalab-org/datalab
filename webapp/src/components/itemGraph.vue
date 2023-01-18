<template>
  <div id="cy" />
</template>

<script>
import { getItemGraph } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";
import cytoscape from "cytoscape";
// import dagre from "cytoscape-dagre";
import cola from "cytoscape-cola";
// import klay from "cytoscape-klay";

// cytoscape.use(dagre);
cytoscape.use(cola);
// cytoscape.use(klay);

export default {
  computed: {
    graphData() {
      return this.$store.state.itemGraphData;
    },
  },
  methods: {
    generateCyNetworkPlot() {
      var cy = cytoscape({
        container: document.getElementById("cy"),
        elements: this.graphData,
        userPanningEnabled: false,
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
        layout: {
          name: "cola", //"klay", //"cola",// "dagre"
          animate: true,
          infinite: false, // for cola, animate continuously
          // nodeSpacing: () =>  30,
          // flow: { axis: 'y', minSeparation: 70 },
          // edgeJaccardLength: 70,
        },
      });

      cy.nodes().each(function (element, i, elements) {
        console.log(i);
        console.log(elements);
        element.style("background-color", itemTypes[element.data("type")].navbarColor);
      });

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
  async mounted() {
    await getItemGraph();
    this.generateCyNetworkPlot();
  },
};
</script>

<style>
#cy {
  width: 100%;
  height: 800px;
  display: block;
}
</style>
