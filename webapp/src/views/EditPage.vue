<template>
  <div id="topScrollPoint"></div>
  <nav
    class="navbar navbar-expand sticky-top navbar-dark py-0 editor-navbar"
    :style="{ backgroundColor: navbarColor }"
  >
    <span class="navbar-brand clickable" @click="scrollToID($event, 'topScrollPoint')"
      >{{ itemTypeEntry?.navbarName || "loading..." }}&nbsp;&nbsp;|&nbsp;&nbsp;
      <FormattedItemName :item_id="item_id" :itemType="itemType" />
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
          <template v-for="blockInfo in blocksInfos" :key="blockInfo.id">
            <span v-if="blockInfo.id !== 'notsupported'" @click="newBlock($event, blockInfo.id)">
              <StyledBlockHelp :blockInfo="blockInfo.attributes" />
            </span>
          </template>
        </div>
      </div>
      <a class="nav-item nav-link" :href="this.itemApiUrl" target="_blank">
        <font-awesome-icon icon="code" fixed-width /> View JSON
      </a>
    </div>
    <div class="navbar-nav ml-auto">
      <span v-if="itemDataLoaded && !savedStatus" class="navbar-text unsaved-warning">
        Unsaved changes
      </span>
      <span v-if="itemDataLoaded && lastModified" class="navbar-text small mx-2"
        ><i>Last saved: {{ lastModified }}</i></span
      >
      <font-awesome-icon
        icon="save"
        fixed-width
        class="nav-item nav-link navbar-icon"
        @click="saveSample"
      />
    </div>
  </nav>

  <!-- Item-type header information goes here -->
  <div class="editor-body">
    <component :is="itemTypeEntry?.itemInformationComponent" :item_id="item_id" />

    <FileList :item_id="item_id" :file_ids="file_ids" :stored_files="stored_files" />

    <div class="container">
      <hr />
    </div>

    <!-- Display the blocks -->
    <div class="container block-container">
      <transition-group name="block-list" tag="div">
        <div class="block-list-item" v-for="block_id in item_data.display_order" :key="block_id">
          <component :is="getBlockDisplayType(block_id)" :item_id="item_id" :block_id="block_id" />
        </div>
      </transition-group>
      <div ref="blockLoadingIndicator" class="text-center">
        <font-awesome-icon
          v-if="isLoadingNewBlock"
          icon="spinner"
          class="fa-spin mx-auto"
          fixed-width
          style="color: gray"
          size="2x"
        />
      </div>
    </div>

    <FileSelectModal :item_id="item_id" />
  </div>
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
import SelectableFileTree from "@/components/SelectableFileTree";

import FileList from "@/components/FileList";
import FileSelectModal from "@/components/FileSelectModal";
import {
  getItemData,
  addABlock,
  saveItem,
  updateBlockFromServer,
  getBlocksInfos,
} from "@/server_fetch_utils";
import FormattedItemName from "@/components/FormattedItemName";

import setupUppy from "@/file_upload.js";

import tinymce from "tinymce/tinymce";

import { blockTypes, itemTypes } from "@/resources.js";
import NotImplementedBlock from "@/components/datablocks/NotImplementedBlock.vue";
import { API_URL } from "@/resources.js";
import { formatDistanceToNow } from "date-fns";

import StyledBlockHelp from "@/components/StyledBlockHelp";

export default {
  data() {
    return {
      item_id: this.$route.params.id,
      itemDataLoaded: false,
      isMenuDropdownVisible: false,
      selectedRemoteFiles: [],
      isLoadingRemoteTree: false,
      isLoadingRemoteFiles: false,
      isLoadingNewBlock: false,
      lastModified: null,
    };
  },
  methods: {
    async newBlock(event, blockType, index = null) {
      this.isMenuDropdownVisible = false;
      this.isLoadingNewBlock = true;
      this.$refs.blockLoadingIndicator.scrollIntoView({
        behavior: "smooth",
      });
      var block_id = await addABlock(this.item_id, blockType, index);
      // close the dropdown and scroll to the new block
      var new_block_el = document.getElementById(block_id);
      this.isLoadingNewBlock = false;
      new_block_el.scrollIntoView({
        behavior: "smooth",
      });
    },
    scrollToID(event, id) {
      var element = document.getElementById(id);
      element.scrollIntoView({
        behavior: "smooth",
      });
    },
    change_a_block(event, block_id) {
      let item_id = this.item_id;
      let new_data = {
        block_id: 7,
        a_new_field: "foo bar",
      };
      console.log(new_data);
      this.$store.commit("updateBlockData", {
        item_id,
        block_id,
        block_data: new_data,
      });
    },
    getBlockDisplayType(block_id) {
      var type = this.blocks[block_id].blocktype;
      if (type in blockTypes) {
        return blockTypes[type].component;
      } else {
        return NotImplementedBlock;
      }
    },
    saveSample() {
      // trigger the mce save so that they update the store with their content
      console.log("save sample clicked!");
      tinymce.editors.forEach((editor) => {
        editor.isDirty() && editor.save();
      });
      saveItem(this.item_id);
      this.lastModified = "just now";
    },
    getSampleData() {
      getItemData(this.item_id).then(() => {
        this.itemDataLoaded = true;

        // update each block asynchronously
        this.item_data.display_order.forEach((block_id) => {
          console.log(`calling update on block ${block_id}`);
          updateBlockFromServer(this.item_id, block_id, this.item_data.blocks_obj[block_id]);
        });
        this.setLastModified();
      });
    },
    leavePageWarningListener(event) {
      event.preventDefault;
      return (event.returnValue =
        "Unsaved changes present. Would you like to leave without saving?");
    },
    setLastModified() {
      let item_date = this.item_data.last_modified || this.item_data.date;
      if (item_date == null) {
        this.lastModified = "Unknown";
      } else {
        // API dates are in UTC but missing Z suffix
        const save_date = new Date(item_date + "Z");
        this.lastModified = formatDistanceToNow(save_date, { addSuffix: true });
      }
    },
  },
  computed: {
    itemType() {
      return this.$store.state.all_item_data[this.item_id]?.type;
    },
    itemTypeEntry() {
      return itemTypes[this.itemType] || null;
    },
    navbarColor() {
      return this.itemTypeEntry?.navbarColor || "DarkGrey";
    },
    item_data() {
      return this.$store.state.all_item_data[this.item_id] || {};
    },
    blocks() {
      return this.item_data.blocks_obj;
    },
    savedStatus() {
      if (!this.itemDataLoaded) {
        return true;
      }
      let allSavedStatusBlocks = this.$store.state.saved_status_blocks;
      let allBlocksAreSaved = this.item_data.display_order.every(
        (block_id) => allSavedStatusBlocks[block_id] !== false,
      );
      return allBlocksAreSaved && this.$store.state.saved_status_items[this.item_id];
    },
    files() {
      return this.item_data.files;
    },
    file_ids() {
      return this.item_data.file_ObjectIds;
    },
    stored_files() {
      return this.$store.state.files;
    },
    blocksInfos() {
      return this.$store.state.blocksInfos;
    },
  },
  created() {
    getBlocksInfos();
    this.getSampleData();
    this.interval = setInterval(() => this.setLastModified(), 30000);
  },
  components: {
    TinyMceInline,
    SelectableFileTree,
    FileList,
    FileSelectModal,
    FormattedItemName,
    StyledBlockHelp,
  },
  beforeMount() {
    this.blockTypes = blockTypes; // bind blockTypes as a NON-REACTIVE object to the this context so that it is accessible by the template.
    this.itemApiUrl = API_URL + "/get-item-data/" + this.item_id;
  },
  mounted() {
    // overwrite ctrl-s and cmd-s to save the page
    this._keyListener = function (e) {
      if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault(); // present "Save Page" from getting triggered.
        this.saveSample();
      }
    };
    document.addEventListener("keydown", this._keyListener.bind(this));

    // Retreive the cached file tree
    // this.loadCachedTree()
    // this.updateRemoteTree()

    // setup the uppy instsance
    setupUppy(this.item_id, "#uppy-trigger", this.stored_files);
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

::v-deep(.navbar-brand:hover .formatted-item-name) {
  outline: 2px solid rgba(0, 0, 0, 0.3);
}

.unsaved-warning {
  font-weight: 600;
  color: #ffc845;
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
