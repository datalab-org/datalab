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
  faPen,
  faCode,
  faEnvelope,
  faCog,
  faChevronRight,
  faArrowUp,
  faArrowDown,
  faProjectDiagram,
  faSatelliteDish,
  faBook,
  faSignInAlt,
  faSignOutAlt,
  faVial,
  faVials,
  faTimes,
  faSync,
  faFolderOpen,
  faFolder,
  faHdd,
  faQuestionCircle,
  faLink,
  faUnlink,
  faExclamationCircle,
  faListOl,
  faSearch,
  faSpinner,
  faEllipsisH,
} from "@fortawesome/free-solid-svg-icons";
import { faPlusSquare } from "@fortawesome/free-regular-svg-icons";
import { faGithub, faOrcid } from "@fortawesome/free-brands-svg-icons";
// import { faHdd } from '@fortawesome/free-regular-svg-icons';
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
library.add(
  faSave,
  faPen,
  faCode,
  faEnvelope,
  faCog,
  faChevronRight,
  faProjectDiagram,
  faArrowUp,
  faArrowDown,
  faSatelliteDish,
  faTimes,
  faBook,
  faSignInAlt,
  faSignOutAlt,
  faQuestionCircle,
  faVial,
  faGithub,
  faOrcid,
  faVials,
  faSync,
  faFolder,
  faFolderOpen,
  faHdd,
  faLink,
  faUnlink,
  faExclamationCircle,
  faListOl,
  faSearch,
  faPlusSquare,
  faSpinner,
  faEllipsisH,
);

// Import TinyMCE
// eslint-disable-next-line no-unused-vars
import tinymce from "tinymce/tinymce";

import "tinymce/icons/default";
import "tinymce/themes/silver";
import "tinymce/skins/ui/oxide/skin.min.css";
import "tinymce/skins/ui/oxide/content.min.css";
import "tinymce/skins/content/default/content.min.css";
import "tinymce/plugins/hr";
import "tinymce/plugins/image";
import "tinymce/plugins/link";
import "tinymce/plugins/lists";
import "tinymce/plugins/charmap";
import "tinymce/plugins/table";
import "tinymce/plugins/emoticons";
import "tinymce/plugins/emoticons/js/emojis";

// import "@uppy/vue"

// import VueScrollTo from 'vue-scrollto';

// import 'tinymce/plugins/link';
import Editor from "@tinymce/tinymce-vue";
import store from "./store";

// css for vue-select
import "vue-select/dist/vue-select.css";

const app = createApp(App);

app
  .use(store)
  .use(router)
  .component("font-awesome-icon", FontAwesomeIcon)
  .component("editor", Editor)
  .mount("#app");

console.log(`initializing app with global variable $API_URL = ${API_URL}`);
app.config.globalProperties.$API_URL = API_URL;
app.config.globalProperties.$filters = {
  IsoDatetimeToDate(isodatetime) {
    if (isodatetime) {
      return isodatetime.substring(0, 10);
    }
    return isodatetime; // if isodatetime is null or empty, don't do anything
  },
};
