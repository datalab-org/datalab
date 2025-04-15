import { createRouter, createWebHistory } from "vue-router";
import Samples from "../views/Samples.vue";
import Equipment from "../views/Equipment.vue";
import StartingMaterials from "../views/StartingMaterials.vue";
import Collections from "@/views/Collections.vue";
import NotFound from "../views/NotFound.vue";
import EditPage from "../views/EditPage.vue";
import CollectionPage from "../views/CollectionPage.vue";
import ExampleGraph from "@/views/ExampleGraph.vue";
import ItemGraphPage from "@/views/ItemGraphPage.vue";
import Admin from "@/views/Admin.vue";
import Login from "../views/Login.vue";
import Login2 from "../views/Login2.vue";
import Login3 from "../views/Login3.vue";

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
    path: "/next/login",
    name: "login",
    alias: "/",
    component: Login,
  },
  {
    path: "/next/login2",
    name: "login2",
    alias: "/",
    component: Login2,
  },
  {
    path: "/next/login3",
    name: "login3",
    alias: "/",
    component: Login3,
  },
  {
    path: "/equipment",
    name: "equipment",
    alias: "/",
    component: Equipment,
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
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const websiteTitle = process.env.VUE_APP_WEBSITE_TITLE || "datalab";

  const capitalizeFirstLetter = (string) => {
    return string ? string.charAt(0).toUpperCase() + string.slice(1) : "";
  };

  const nameMapping = {
    "starting-materials": "Inventory",
    "item-graph": "Graph View",
  };

  let formattedName = nameMapping[to.name] || capitalizeFirstLetter(to.name);

  document.title = to.name
    ? to.params.id
      ? `${websiteTitle} - ${formattedName}: ${to.params.id}`
      : `${websiteTitle} - ${formattedName}`
    : websiteTitle;

  next();
});

export default router;
