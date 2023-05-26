<template>
  <div id="topScrollPoint"></div>
  <nav
    class="navbar navbar-expand sticky-top navbar-dark py-0 editor-navbar"
    :style="{ backgroundColor: navbarColor }"
  >
    <span class="navbar-brand" @click="scrollToID($event, 'topScrollPoint')"
      >{{ itemTypeEntry?.navbarName || "loading..." }}&nbsp;&nbsp;|&nbsp;&nbsp;
      {{ collection_id }}
    </span>
    <div class="navbar-nav">
      <a class="nav-item nav-link" href="/">Home</a>
      <div class="nav-item dropdown">
        <a
          class="nav-link dropdown-toggle ml-2"
          id="navbarDropdown"
          role="button"
          data-toggle="dropdown"
          aria-haspopup="true"
          aria-expanded="false"
          @click="isMenuDropdownVisible = !isMenuDropdownVisible"
        >
          Add a block
        </a>
        <div
          class="dropdown-menu"
          style="display: block"
          aria-labelledby="navbarDropdown"
          v-show="isMenuDropdownVisible"
        >
          <a
            v-for="(blockType, id) in blockTypes"
            :key="id"
            class="dropdown-item"
            @click="newBlock($event, id)"
          >
            {{ blockType.description }}
          </a>
        </div>
      </div>
      <a class="nav-item nav-link" :href="this.collectionApiUrl" target="_blank">
        <font-awesome-icon icon="code" fixed-width /> View JSON
      </a>
    </div>
    <div class="navbar-nav ml-auto">
      <span v-if="data_loaded && !savedStatus" class="navbar-text unsaved-warning">
        Unsaved changes
      </span>
      <span v-if="data_loaded" class="navbar-text mx-2"
        ><i>Last saved: {{ lastModified }}</i></span
      >
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

    <div class="container">
      <hr />
    </div>
  </div>
</template>

<script>
import CollectionInformation from "@/components/CollectionInformation";
import { getCollectionData, saveCollection, addACollectionBlock } from "@/server_fetch_utils";
import tinymce from "tinymce/tinymce";
import { blockTypes, itemTypes } from "@/resources.js";
import { API_URL } from "@/resources.js";

export default {
  data() {
    return {
      collection_id: this.$route.params.id,
      data_loaded: false,
      isMenuDropdownVisible: false,
      isLoadingNewBlock: false,
    };
  },
  methods: {
    async newBlock(event, blockType, index = null) {
      this.isMenuDropdownVisible = false;
      this.isLoadingNewBlock = true;
      this.$refs.blockLoadingIndicator.scrollIntoView({
        behavior: "smooth",
      });
      var block_id = await addACollectionBlock(this.item_id, blockType, index);
      // close the dropdown and scroll to the new block
      var new_block_el = document.getElementById(block_id);
      this.isLoadingNewBlock = false;
      new_block_el.scrollIntoView({
        behavior: "smooth",
      });
    },
    saveCollectionData() {
      // trigger the mce save so that they update the store with their content
      console.log("save clicked!");
      tinymce.editors.forEach((editor) => editor.save());
      saveCollection(this.collection_id);
    },
    async getCollection() {
      await getCollectionData(this.collection_id);
      this.data_loaded = true;
    },
    leavePageWarningListener(event) {
      event.preventDefault;
      return (event.returnValue =
        "Unsaved changes present. Would you like to leave without saving?");
    },
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
    lastModified() {
      // if (!this.item_data.last_modified) { return "" }
      let item_date = this.collection_data.last_modified;
      const save_date = new Date(item_date);
      return save_date.toLocaleString("en-GB");
    },
  },
  created() {
    this.getCollection();
  },
  components: {
    CollectionInformation,
  },
  beforeMount() {
    this.collectionApiUrl = API_URL + "/collections/" + this.collection_id;
    this.blockTypes = blockTypes; // bind blockTypes as a NON-REACTIVE object to the this context so that it is accessible by the template.
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

.block-container {
  padding-bottom: 100px;
  position: relative;
}

.block-list-item {
  transition: all 0.6s ease;
  /*display: inline-block;*/
  width: 100%;
  position: relative;
}

.block-list-enter-from,
.block-list-leave-to {
  opacity: 0;
  /*transform: translateX(-100px);*/
}

.block-list-leave-active {
  position: absolute;
  max-width: calc(100% - 30px);
}

.dropdown-menu {
  cursor: pointer;
}
</style>
