import { createRouter, createWebHistory } from "vue-router";
import Samples from "../views/Samples.vue";
import Equipments from "../views/Equipments.vue";
import StartingMaterials from "../views/StartingMaterials.vue";
import Collections from "@/views/Collections.vue";
import NotFound from "../views/NotFound.vue";
import EditPage from "../views/EditPage.vue";
import CollectionPage from "../views/CollectionPage.vue";
import ExampleGraph from "@/views/ExampleGraph.vue";
import ItemGraphPage from "@/views/ItemGraphPage.vue";
import Admin from "@/views/Admin.vue";

import OldSample from "../views/OldSamples.vue";
import OldEquipment from "../views/OldEquipments.vue";

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
    path: "/equipments",
    name: "equipments",
    alias: "/",
    component: Equipments,
  },
  {
    path: "/edit/:id",
    name: "edit",
    component: EditPage,
  },
  {
    path: "/items/:refcode",
    name: "edit item",
    component: EditPage,
  },
  {
    path: "/starting-materials",
    name: "starting-materials",
    component: StartingMaterials,
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
  {
    path: "/old-sample",
    name: "old-sample",
    alias: "/",
    component: OldSample,
  },
  {
    path: "/old-equipment",
    name: "old-equipment",
    alias: "/",
    component: OldEquipment,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
