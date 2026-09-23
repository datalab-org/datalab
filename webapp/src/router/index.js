import { createRouter, createWebHistory } from "vue-router";
import Samples from "../views/Samples.vue";
import Equipment from "../views/Equipment.vue";
import StartingMaterials from "../views/StartingMaterials.vue";
import Collections from "@/views/Collections.vue";
import Tags from "@/views/Tags.vue";
import NotFound from "../views/NotFound.vue";
import EditPage from "../views/EditPage.vue";
import CollectionPage from "../views/CollectionPage.vue";
import ItemGraphPage from "@/views/ItemGraphPage.vue";
import Admin from "@/views/Admin.vue";
import Login from "../views/Login.vue";
import { API_URL, WEBSITE_TITLE } from "@/resources.js";
import { getInfo } from "@/server_fetch_utils.js";
import store from "@/store/index.js";

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
    path: "/login",
    name: "login",
    alias: "/next/login",
    component: Login,
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
    path: "/tags",
    name: "tags",
    component: Tags,
    // Only reachable when the backend reports the tags feature as enabled.
    beforeEnter: async (to, from, next) => {
      const serverInfo = store.state.serverInfo ?? (await getInfo());
      if (serverInfo.features?.tags) {
        next();
      } else {
        next({ path: "/" });
      }
    },
  },
  {
    path: "/collections/:id",
    name: "Collection",
    component: CollectionPage,
  },
  {
    path: "/item-graph/",
    name: "item-graph",
    component: ItemGraphPage,
  },
  {
    path: "/files/:pathMatch(.*)",
    name: "files-redirect",
    beforeEnter: (to) => {
      window.location.href = API_URL + "/files/" + to.params.pathMatch;
      return false;
    },
    component: NotFound,
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

router.beforeEach(async (to, from, next) => {
  if (to.query.token) {
    window.location.href = API_URL + "/login/email?token=" + to.query.token;
    return;
  }

  const { getUserInfo } = await import("@/server_fetch_utils.js");
  const user = await getUserInfo();

  // Let unauthenticated users through to item pages with an access token (`at`)
  // so that sharing links work; the API will reject the request if the token is invalid.
  const hasItemAccessToken = to.name === "edit item" && Boolean(to.query.at);

  if (!user && to.name !== "login" && !hasItemAccessToken) {
    next({ name: "login", query: { next: to.fullPath } });
    return;
  }

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
      ? `${WEBSITE_TITLE} - ${formattedName}: ${to.params.id}`
      : `${WEBSITE_TITLE} - ${formattedName}`
    : WEBSITE_TITLE;

  next();
});

export default router;
