<template>
  <div id="topScrollPoint"></div>
  <nav
    class="d-flex navbar navbar-expand-md navbar-dark py-lg-0 px-3 editor-navbar"
    :style="{ backgroundColor: navbarColor }"
  >
    <div class="d-flex align-items-center">
      <button
        class="navbar-toggler me-4"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarContent"
        aria-controls="navbarContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
        Menu
      </button>

      <div id="navbarContent" class="collapse navbar-collapse">
        <div class="navbar-nav me-auto">
          <span class="navbar-brand" @click="scrollToID($event, 'topScrollPoint')">
            {{ itemTypeEntry?.navbarName || "loading..." }}&nbsp;&nbsp;|&nbsp;&nbsp;
            <FormattedItemName :item_id="collection_id" item-type="collections" />
          </span>
          <router-link class="nav-item nav-link" to="/">Home</router-link>

          <a class="nav-item nav-link" :href="collectionApiUrl" target="_blank">
            <font-awesome-icon icon="code" fixed-width /> View JSON
          </a>
        </div>
      </div>
    </div>
    <div class="navbar-nav d-flex flex-row ms-auto align-items-center">
      <span v-if="data_loaded && !savedStatus" class="navbar-text unsaved-warning me-2">
        Unsaved changes
      </span>
      <span v-if="data_loaded && lastModified" class="navbar-text me-2 d-flex align-items-center">
        <i class="small">Last saved: {{ lastModified }}</i>
      </span>
      <font-awesome-icon
        icon="save"
        fixed-width
        class="nav-item nav-link navbar-icon"
        @click="saveCollectionData"
      />
    </div>
  </nav>

  <!-- Item-type header information goes here -->
  <div class="editor-body">
    <CollectionInformation :collection_id="collection_id" />
  </div>
</template>

<script>
import CollectionInformation from "@/components/CollectionInformation";
import { getCollectionData, saveCollection } from "@/server_fetch_utils";
import FormattedItemName from "@/components/FormattedItemName.vue";
import tinymce from "tinymce/tinymce";
import { itemTypes } from "@/resources.js";
import { API_URL } from "@/resources.js";
import { formatDistanceToNow } from "date-fns";

export default {
  components: {
    CollectionInformation,
    FormattedItemName,
  },
  beforeRouteLeave(to, from, next) {
    // give warning before leaving the page by the vue router (which would not trigger "beforeunload")
    if (this.savedStatus) {
      next();
    } else {
      if (window.confirm("Unsaved changes present. Would you like to leave without saving?")) {
        next();
      } else {
        next(false);
      }
    }
  },
  data() {
    return {
      collection_id: this.$route.params.id,
      data_loaded: false,
      isMenuDropdownVisible: false,
      isLoadingNewBlock: false,
      lastModified: null,
    };
  },
  computed: {
    itemTypeEntry() {
      return itemTypes.collections;
    },
    navbarColor() {
      return this.itemTypeEntry?.navbarColor || "DarkGrey";
    },
    collection_data() {
      return this.$store.state.all_collection_data[this.collection_id] || {};
    },
    savedStatus() {
      return this.$store.state.saved_status_collections[this.collection_id];
    },
  },
  watch: {
    // add a warning before leaving page if unsaved
    savedStatus(newValue) {
      if (!newValue) {
        window.addEventListener("beforeunload", this.leavePageWarningListener, true);
      } else {
        window.removeEventListener("beforeunload", this.leavePageWarningListener, true);
      }
    },
  },
  created() {
    this.getCollection();
    this.interval = setInterval(() => this.setLastModified(), 30000);
  },
  beforeMount() {
    this.collectionApiUrl = API_URL + "/collections/" + this.collection_id;
  },
  mounted() {
    // overwrite ctrl-s and cmd-s to save the page
    this._keyListener = function (e) {
      if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault(); // present "Save Page" from getting triggered.
        this.saveCollectionData();
      }
    };
    document.addEventListener("keydown", this._keyListener.bind(this));
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this._keyListener);
  },
  methods: {
    scrollToID(event, id) {
      var element = document.getElementById(id);
      element.scrollIntoView({
        behavior: "smooth",
      });
    },
    saveCollectionData() {
      // trigger the mce save so that they update the store with their content
      console.log("save clicked!");
      tinymce.editors.forEach((editor) => editor.save());
      saveCollection(this.collection_id);
      this.lastModified = "just now";
    },
    async getCollection() {
      await getCollectionData(this.collection_id);
      this.data_loaded = true;
      this.setLastModified();
    },
    leavePageWarningListener(event) {
      event.preventDefault;
      return (event.returnValue =
        "Unsaved changes present. Would you like to leave without saving?");
    },
    setLastModified() {
      let item_date = this.collection_data.last_modified || this.collection_data.date;
      if (item_date == null) {
        this.lastModified = "Unknown";
      } else {
        this.lastModified = formatDistanceToNow(new Date(item_date), { addSuffix: true });
      }
    },
  },
};
</script>

<style scoped>
.editor-navbar {
  margin-bottom: 1rem;
  z-index: 900;
}

label,
::v-deep(label) {
  font-weight: 500;
  color: v-bind("itemTypeEntry?.labelColor");
}

.nav-link {
  cursor: pointer;
}

.nav-link:hover {
  background-color: black;
  color: white;
}

.navbar-icon {
  width: 1.9rem;
  height: 1.9rem;
  padding: 0.3rem;
}

.unsaved-warning {
  font-weight: 600;
  color: #ffc845;
}

.navbar-brand {
  cursor: pointer;
}
</style>
