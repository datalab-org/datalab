<template>
  <div>
    <div id="cy" />
  </div>
</template>

<script>
import { getItemGraph } from "@/server_fetch_utils.js";

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
      return this.$store.state.itemGraph;
    },
  },
  methods: {
    generateCyNetworkPlot() {
      cytoscape({
        container: document.getElementById("cy"),
        elements: this.graphData,
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
          infinite: true, // for cola, animate continuously
          // nodeSpacing: () =>  30,
          // flow: { axis: 'y', minSeparation: 70 },
          // edgeJaccardLength: 70,
        },
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
  height: 600px;
  display: block;
}
</style>
