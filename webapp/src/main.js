// import BootstrapVue from 'bootstrap-vue';

import "bootstrap/dist/css/bootstrap.css";
// import 'bootstrap-vue/dist/bootstrap-vue.css'

import { API_URL } from "@/resources.js";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faBarcode,
  faBars,
  faHome,
  faSave,
  faCloudUploadAlt,
  faRedo,
  faUndo,
  faPen,
  faFile,
  faCode,
  faEnvelope,
  faCog,
  faCubes,
  faFileExport,
  faHistory,
  faQrcode,
  faUsersCog,
  faUsers,
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
  faExclamationTriangle,
  faExclamationCircle,
  faListOl,
  faSearch,
  faSpinner,
  faEllipsisH,
  faCopy,
  faInfoCircle,
  faPlus,
  faCheck,
  faCheckCircle,
  faBold,
  faItalic,
  faUnderline,
  faStrikethrough,
  faListUl,
  faImage,
  faTable,
  faMinus,
  faPalette,
  faRemoveFormat,
  faTrash,
  faMarker,
  faQuoteRight,
  faLaptopCode,
  faSquareRootAlt,
  faShareAlt,
  faUserFriends,
  faCaretDown,
  faLock,
  faFlask,
  faLayerGroup,
} from "@fortawesome/free-solid-svg-icons";
import { faPlusSquare } from "@fortawesome/free-regular-svg-icons";
import { faGithub, faOrcid, faGoogle, faMicrosoft } from "@fortawesome/free-brands-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
library.add(
  faBarcode,
  faBars,
  faHome,
  faSave,
  faPen,
  faRedo,
  faUndo,
  faCloudUploadAlt,
  faFile,
  faCode,
  faQrcode,
  faEnvelope,
  faCog,
  faCubes,
  faFileExport,
  faHistory,
  faUsersCog,
  faUsers,
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
  faGoogle,
  faMicrosoft,
  faVials,
  faSync,
  faFolder,
  faFolderOpen,
  faHdd,
  faLink,
  faUnlink,
  faExclamationTriangle,
  faExclamationCircle,
  faListOl,
  faSearch,
  faPlusSquare,
  faPlus,
  faSpinner,
  faEllipsisH,
  faCopy,
  faInfoCircle,
  faCheck,
  faCheckCircle,
  faBold,
  faItalic,
  faUnderline,
  faStrikethrough,
  faListUl,
  faImage,
  faTable,
  faMinus,
  faPalette,
  faRemoveFormat,
  faTrash,
  faMarker,
  faQuoteRight,
  faLaptopCode,
  faSquareRootAlt,
  faShareAlt,
  faUserFriends,
  faCaretDown,
  faLock,
  faFlask,
  faLayerGroup,
);

// import "@uppy/vue"

// import VueScrollTo from 'vue-scrollto';

import store from "./store";

// css for vue-select
import "vue-select/dist/vue-select.css";

// import "primevue";
import PrimeVue from "primevue/config";
import DatalabPreset from "./primevue-theme-preset.js";

const app = createApp(App);

app
  .use(store)
  .use(router)
  .use(PrimeVue, {
    theme: DatalabPreset,
  })
  .component("font-awesome-icon", FontAwesomeIcon)
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
