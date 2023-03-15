import { createRouter, createWebHistory } from "vue-router";
// import Home from '../views/Home.vue'
// import Test from '../views/Test.vue'
import Samples from "../views/Samples.vue";
import SamplesNext from "../views/SamplesNext.vue";
import StartingMaterials from "../views/StartingMaterials.vue";
import NotFound from "../views/NotFound.vue";
import EditPage from "../views/EditPage.vue";
import Test from "@/components/Test.vue";
import TestTree from "@/components/TestTree.vue";
import CycleParameterTable from "@/components/CycleParameterTable.vue";
import ExampleGraph from "@/views/ExampleGraph.vue";
import ItemGraphPage from "@/views/ItemGraphPage.vue";
const routes = [
  {
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
  {
    path: "/samples",
    name: "samples",
    alias: "/",
    component: Samples,
  },
  { path: "/next/samples", name: "samples-next", alias: "/next", component: SamplesNext },
  {
    path: "/edit/:id",
    name: "edit",
    component: EditPage,
  },
  {
    path: "/starting-materials",
    name: "starting-materials",
    component: StartingMaterials,
  },
  {
    path: "/test/",
    name: "test",
    component: Test,
  },
  {
    path: "/test-tree/",
    name: "test-tree",
    component: TestTree,
  },
  {
    path: "/test-graph/",
    name: "test-graph",
    component: ExampleGraph,
  },
  {
    path: "/item-graph/",
    name: "item-graph",
    component: ItemGraphPage,
  },
  {
    path: "/test-cycle-parameter-table/",
    name: "test-cycle-parameter-table",
    component: CycleParameterTable,
  },
  { path: "/404", name: "notfound", component: NotFound },
  { path: "/:pathMatch(.*)*", component: NotFound },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
