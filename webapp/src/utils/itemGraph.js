import { defineAsyncComponent } from "vue";

// The graph libraries (cytoscape and its layouts) are large, so `ItemGraph` is loaded on demand,
// in its own chunk. Components that render it immediately start the download alongside their
// graph data request.
export const ItemGraph = defineAsyncComponent(() => import("@/components/ItemGraph.vue"));
