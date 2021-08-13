// import BootstrapVue from 'bootstrap-vue';

import "bootstrap/dist/css/bootstrap.css";
// import 'bootstrap-vue/dist/bootstrap-vue.css'

import { API_URL } from "@/resources.js";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faSave,
  faChevronRight,
  faArrowUp,
  faArrowDown,
  faTimes,
  faSync,
  faFolderOpen,
  faFolder,
  faHdd,
  faLink,
  faUnlink,
  faExclamationCircle,
} from "@fortawesome/free-solid-svg-icons";
// import { faHdd } from '@fortawesome/free-regular-svg-icons';
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
library.add(
  faSave,
  faChevronRight,
  faArrowUp,
  faArrowDown,
  faTimes,
  faSync,
  faFolder,
  faFolderOpen,
  faHdd,
  faLink,
  faUnlink,
  faExclamationCircle
);

// Import TinyMCE
// eslint-disable-next-line no-unused-vars
import tinymce from "tinymce/tinymce";

import "tinymce/icons/default";
import "tinymce/themes/silver";
import "tinymce/skins/ui/oxide/skin.min.css";
import "tinymce/skins/ui/oxide/content.min.css";
import "tinymce/skins/content/default/content.min.css";
// import "tinymce/plugins/emoticons" // not working for some reason
import "tinymce/plugins/hr";
import "tinymce/plugins/image";
import "tinymce/plugins/link";
import "tinymce/plugins/lists";
import "tinymce/plugins/charmap";
import "tinymce/plugins/table";

// import "@uppy/vue"

// import VueScrollTo from 'vue-scrollto';

// import 'tinymce/plugins/link';
import Editor from "@tinymce/tinymce-vue";
import store from "./store";

const app = createApp(App);

app
  .use(store)
  .use(router)
  .component("font-awesome-icon", FontAwesomeIcon)
  .component("editor", Editor)
  .mount("#app");

console.log(`initializing app with global variable $API_URL = ${API_URL}`);
app.config.globalProperties.$API_URL = API_URL;
