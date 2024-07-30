import { createRouter, createWebHistory } from "vue-router";
import Samples from "../views/Samples.vue";
import Equipment from "../views/Equipment.vue";
import SamplePrime from "../views/SamplePrime.vue";
import StartingMaterials from "../views/StartingMaterials.vue";
import StartingMaterialsNext from "../views/StartingMaterialsNext.vue";
import Collections from "@/views/Collections.vue";
import NotFound from "../views/NotFound.vue";
import EditPage from "../views/EditPage.vue";
import CollectionPage from "../views/CollectionPage.vue";
import ExampleGraph from "@/views/ExampleGraph.vue";
import ItemGraphPage from "@/views/ItemGraphPage.vue";
import Admin from "@/views/Admin.vue";
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
  {
    path: "/equipment",
    name: "equipment",
    alias: "/",
    component: Equipment,
  },
  { path: "/next/samples", name: "samples-next", alias: "/next", component: SamplePrime },
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
    path: "/next/starting-materials",
    name: "starting-materials-next",
    component: StartingMaterialsNext,
  },
  {
    path: "/collections",
    name: "collections",
    component: Collections,
  },
  {
    path: "/collections/:id",
    name: "Collection",
    component: CollectionPage,
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
  { path: "/404", name: "notfound", component: NotFound },
  { path: "/:pathMatch(.*)*", component: NotFound },
  {
    path: "/admin",
    name: "admin",
    alias: "/",
    component: Admin,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
