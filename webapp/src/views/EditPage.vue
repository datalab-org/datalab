<template>
  <div id="topScrollPoint"></div>
  <nav
    class="navbar navbar-expand-md sticky-top navbar-dark py-0 editor-navbar"
    :style="{ backgroundColor: navbarColor }"
  >
    <div v-show="false" class="navbar-nav"><LoginDetails /></div>
    <span class="navbar-brand clickable" @click="scrollToID($event, 'topScrollPoint')">
      <span class="navbar-brand-type"
        >{{ itemTypeEntry?.navbarName || "loading..." }}&nbsp;&nbsp;|&nbsp;&nbsp;</span
      >
      <span class="navbar-brand-name">
        <FormattedItemName :item_id="item_id" :item-type="itemType" />
      </span>
    </span>

    <!-- Always-visible right-side cluster: status + save + hamburger (hamburger only shows below md) -->
    <div class="navbar-right-cluster order-md-last">
      <span
        v-if="itemDataLoaded && !savedStatus"
        class="navbar-text unsaved-warning d-none d-sm-inline"
      >
        Unsaved changes
      </span>
      <span
        v-if="itemDataLoaded && !savedStatus"
        class="unsaved-dot d-sm-none"
        title="Unsaved changes"
      ></span>
      <span v-if="itemDataLoaded && lastModified" class="navbar-text small d-none d-md-inline"
        ><i>Last saved: {{ lastModified }}</i></span
      >
      <font-awesome-icon
        v-show="isNavCollapsed"
        icon="save"
        fixed-width
        class="nav-link navbar-icon"
        :class="{ 'navbar-icon-unsaved': itemDataLoaded && !savedStatus }"
        title="Save"
        @click="saveSample"
      />
      <button
        class="navbar-toggler border-0 d-md-none"
        type="button"
        aria-label="Toggle navigation"
        @click="isNavCollapsed = !isNavCollapsed"
      >
        <font-awesome-icon icon="bars" />
      </button>
    </div>

    <div class="collapse navbar-collapse" :class="{ show: !isNavCollapsed }">
      <div class="navbar-nav">
        <router-link class="nav-item nav-link" to="/" title="Home">
          <font-awesome-icon icon="home" fixed-width /> Home
        </router-link>
        <AddBlockDropdown
          variant="navlink"
          key-prefix="nav"
          trigger-testid="add-block-button-top"
          menu-testid="add-block-dropdown"
          :suggested-block-types="suggestedBlockTypes"
          :all-block-types="allBlockTypes"
          @select="newBlock"
        />
        <ExportDropdown
          :item-id="item_id"
          :collection-id="itemType === 'collections' ? item_id : null"
          :item-type="itemType"
        />
        <a
          v-if="itemDataLoaded && refcode"
          class="nav-item nav-link"
          href="#"
          title="Share this item"
          @click.prevent="isSharingModalVisible = true"
        >
          <font-awesome-icon icon="share-alt" fixed-width /> Share
        </a>
        <a class="nav-item nav-link" :href="itemApiUrl" target="_blank" title="View JSON">
          <font-awesome-icon icon="code" fixed-width /> View JSON
        </a>
        <a
          v-if="itemDataLoaded"
          class="nav-item nav-link"
          title="Version History"
          @click="showVersionHistory"
        >
          <font-awesome-icon icon="history" fixed-width /> Versions
        </a>
        <a class="nav-item nav-link d-md-none" title="Save" @click="saveSample">
          <font-awesome-icon icon="save" fixed-width /> Save
        </a>
        <span v-if="itemDataLoaded && lastModified" class="navbar-text small mx-2 d-md-none"
          ><i>Last saved: {{ lastModified }}</i></span
        >
      </div>
    </div>
  </nav>

  <!-- Item-type header information goes here -->
  <div class="editor-body">
    <component
      :is="itemTypeEntry?.itemInformationComponent"
      ref="sampleInformation"
      :item_id="item_id"
    />
    <FileList :item_id="item_id" :stored_files="stored_files" />

    <div class="container">
      <hr />
    </div>

    <!-- Display the blocks -->
    <div v-if="blocksLoaded && blockInfoLoaded" class="container block-container">
      <transition-group name="block-list" tag="div">
        <div v-for="block_id in item_data.display_order" :key="block_id" class="block-list-item">
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

      <div class="mt-4 text-center">
        <AddBlockDropdown
          variant="button"
          direction="up"
          key-prefix="bottom"
          trigger-testid="add-block-button-bottom"
          menu-testid="add-block-dropdown-bottom"
          :suggested-block-types="suggestedBlockTypes"
          :all-block-types="allBlockTypes"
          @select="newBlock"
        />
      </div>
    </div>

    <FileSelectModal :item_id="item_id" />
    <VersionHistoryModal
      v-model="isVersionHistoryVisible"
      :refcode="refcode"
      :item-id="item_id"
      :current-version="item_data.version"
      @version-restored="handleVersionRestored"
    />
    <SharingModal
      v-if="refcode && item_id"
      v-model="isSharingModalVisible"
      :refcode="refcode"
      :item-id="item_id"
    />
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import TiptapInline from "@/components/TiptapInline";
import SelectableFileTree from "@/components/SelectableFileTree";

import FileList from "@/components/FileList";
import FileSelectModal from "@/components/FileSelectModal";
import VersionHistoryModal from "@/components/VersionHistoryModal.vue";
import SharingModal from "@/components/SharingModal.vue";
import {
  getItemData,
  getItemByRefcode,
  addABlock,
  saveItem,
  updateBlockFromServer,
  getBlocksInfos,
} from "@/server_fetch_utils";
import LoginDetails from "@/components/LoginDetails";
import FormattedItemName from "@/components/FormattedItemName";

import setupUppy from "@/file_upload.js";

import { itemTypes, API_URL, customBlockTypes } from "@/resources.js";
import BokehBlock from "@/components/datablocks/BokehBlock.vue";
import ErrorBlock from "@/components/datablocks/ErrorBlock.vue";
import { formatDistanceToNow } from "date-fns";

import AddBlockDropdown from "@/components/AddBlockDropdown";

import ExportDropdown from "@/components/ExportDropdown";

export default {
  components: {
    TiptapInline,
    SelectableFileTree,
    FileList,
    LoginDetails,
    FileSelectModal,
    VersionHistoryModal,
    SharingModal,
    FormattedItemName,
    AddBlockDropdown,
    ExportDropdown,
  },
  provide() {
    return {
      openSharingModal: () => {
        this.isSharingModalVisible = true;
      },
    };
  },
  async beforeRouteLeave(to, from, next) {
    // give warning before leaving the page by the vue router (which would not trigger "beforeunload")
    if (this.savedStatus) {
      next();
    } else {
      const confirmed = await DialogService.confirm({
        title: "Unsaved Changes",
        message: "Unsaved changes present. Would you like to leave without saving?",
        type: "warning",
      });
      if (confirmed) {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: true });
        next();
      } else {
        next(false);
      }
    }
  },
  data() {
    return {
      item_id: this.$route.params?.id || null,
      refcode: this.$route.params?.refcode || null,
      itemDataLoaded: false,
      blockInfoLoaded: false,
      blocksLoaded: false,
      isNavCollapsed: true,
      selectedRemoteFiles: [],
      isLoadingRemoteTree: false,
      isLoadingRemoteFiles: false,
      isLoadingNewBlock: false,
      lastModified: null,
      isVersionHistoryVisible: false,
      isSharingModalVisible: false,
    };
  },
  computed: {
    itemType() {
      return this.$store.state.all_item_data[this.item_id]?.type || undefined;
    },
    itemTypeEntry() {
      return itemTypes[this.itemType] || undefined;
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
      return this.item_data.files || [];
    },
    stored_files() {
      return Object.fromEntries(this.files.map((file) => [file.immutable_id, file]));
    },
    blocksInfos() {
      if (this.blockInfoLoaded) {
        const blocksInfos = Array.from(this.$store.getters.getBlocksInfos.values());
        return [...blocksInfos].sort((a, b) =>
          a?.attributes?.name.localeCompare(b?.attributes?.name),
        );
      }
      return [];
    },
    itemApiUrl() {
      return API_URL + "/items/" + this.refcode;
    },
    uploadedFileExtensions() {
      if (!this.files || this.files.length === 0) {
        return [];
      }
      const extensions = this.files.map((file) => file.extension).filter((ext) => ext);
      return [...new Set(extensions)];
    },
    suggestedBlockTypes() {
      if (this.uploadedFileExtensions.length === 0 || !this.blockInfoLoaded) {
        return [];
      }

      return this.blocksInfos.filter((blockInfo) => {
        if (blockInfo.id === "notsupported") {
          return false;
        }

        const acceptedExtensions = blockInfo.attributes?.accepted_file_extensions;
        if (!acceptedExtensions || acceptedExtensions.length === 0) {
          return false;
        }

        return this.uploadedFileExtensions.some((uploadedExt) =>
          acceptedExtensions.some(
            (acceptedExt) => uploadedExt.toLowerCase() === acceptedExt.toLowerCase(),
          ),
        );
      });
    },
    allBlockTypes() {
      if (!this.blockInfoLoaded) {
        return [];
      }

      return this.blocksInfos.filter((blockInfo) => blockInfo.id !== "notsupported");
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
    // Re-load when the user navigates between edit pages via router.push.
    // Without this, a route param change would leave stale item data on screen.
    "$route.params.id"(newId, oldId) {
      if (newId && newId !== oldId) this.reloadForRoute();
    },
    "$route.params.refcode"(newRefcode, oldRefcode) {
      if (newRefcode && newRefcode !== oldRefcode) this.reloadForRoute();
    },
  },
  created() {
    this.getBlocksInfo();
    this.getSampleData();
    this.interval = setInterval(() => this.setLastModified(), 30000);
  },
  beforeMount() {
    this.customBlockTypes = customBlockTypes; // bind customBlockTypes as a NON-REACTIVE object to the this context so that it is accessible by the template.
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
    setupUppy(this.item_id, "#uppy-trigger", {});
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this._keyListener);
  },
  methods: {
    async newBlock(blockType, index = null) {
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
    getBlockDisplayType(block_id) {
      const block = this.blocks[block_id];

      if (!block || this.$store.state.block_errors[block_id]) {
        return ErrorBlock;
      }

      const type = block.blocktype;

      if (!(type in this.$store.state.blocksInfos)) {
        return ErrorBlock;
      }

      if (type in customBlockTypes) {
        return customBlockTypes[type].component;
      } else {
        return BokehBlock;
      }
    },
    saveSample() {
      saveItem(this.item_id);
      this.lastModified = "just now";
    },
    async getSampleData() {
      const urlParams = new URLSearchParams(window.location.search);
      const accessToken = urlParams.get("at");

      if (this.item_id == null) {
        getItemByRefcode(this.refcode, accessToken)
          .then(() => {
            this.itemDataLoaded = true;
            this.$nextTick(() => {
              this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: true });
            });
            this.item_id = this.$store.state.refcode_to_id[this.refcode];
            this.updateBlocks();
          })
          .catch(() => {
            this.itemDataLoaded = false;
          });
      } else {
        getItemData(this.item_id, accessToken)
          .then(() => {
            this.itemDataLoaded = true;
            this.refcode = this.item_data.refcode;
            this.$nextTick(() => {
              this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: true });
            });
            this.updateBlocks();
          })
          .catch(() => {
            this.itemDataLoaded = false;
          });
      }
    },
    async updateBlocks() {
      if (this.itemDataLoaded && this.item_data && this.item_data.display_order) {
        // update each block asynchronously
        this.item_data.display_order.forEach((block_id) => {
          console.log(`calling update on block ${block_id}`);
          updateBlockFromServer(this.item_id, block_id, this.item_data.blocks_obj[block_id]).catch(
            (error) => {
              console.error(`Error updating block ${block_id}:`, error);
            },
          );
        });
        this.blocksLoaded = true;
        this.setLastModified();
      }
    },
    async getBlocksInfo() {
      if (Object.keys(this.$store.state.blocksInfos).length == 0) {
        await getBlocksInfos();
      }
      this.blockInfoLoaded = true;
    },
    reloadForRoute() {
      this.item_id = this.$route.params?.id || null;
      this.refcode = this.$route.params?.refcode || null;
      this.itemDataLoaded = false;
      this.blocksLoaded = false;
      this.getSampleData();
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
        this.lastModified = formatDistanceToNow(new Date(item_date), { addSuffix: true });
      }
    },
    showVersionHistory() {
      this.isVersionHistoryVisible = true;
    },
    async handleVersionRestored() {
      // Reload the item data after version restoration
      if (this.refcode) {
        await getItemByRefcode(this.refcode);
      } else if (this.item_id) {
        await getItemData(this.item_id);
      }
      // Mark item as saved (restored data is already in DB)
      this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: true });
      // Mark all blocks as saved
      this.item_data.display_order.forEach((block_id) => {
        this.$store.commit("setBlockSaved", { block_id: block_id, isSaved: true });
      });
      // Refresh the blocks
      await this.updateBlocks();
      // Update last modified time
      this.setLastModified();
    },
  },
};
</script>

<style scoped>
.editor-navbar {
  margin-bottom: 1rem;
  z-index: 900;
  /* Match the natural height of a nav-link row so the collapsed (burger) bar
     is the same height as the expanded/desktop navbar. */
  min-height: 2.5rem;
}

/* Brand = item type + item name. Lay them out so the type yields space first:
   as the navbar narrows the type clips away before the item name truncates. */
.editor-navbar .navbar-brand {
  display: flex;
  align-items: baseline;
  min-width: 0;
  overflow: hidden;
}
.navbar-brand-type {
  /* very high shrink factor → gives up width (and disappears) before the name */
  flex: 0 100 auto;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
}
.navbar-brand-name {
  /* protected: only truncates once the type is gone */
  flex: 0 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* On smaller screens (mobile + the icon-only tier) drop the type entirely
   rather than showing a clipped fragment. */
@media (max-width: 1199.98px) {
  .navbar-brand-type {
    display: none;
  }
}

label,
::v-deep(label) {
  font-weight: 500;
  color: v-bind("itemTypeEntry?.labelColor");
}

/* ::v-deep so these also reach the Export link, which is the root of a multi-root
   child component and therefore misses this component's scoped styles. */
.editor-navbar ::v-deep(.nav-link) {
  cursor: pointer;
  /* Keep each label on one line; the brand shrinks first instead */
  white-space: nowrap;
}

.editor-navbar ::v-deep(.nav-link:hover) {
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

.navbar-right-cluster {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

/* Don't let the "Last saved" stamp wrap onto a second line */
.navbar-right-cluster .navbar-text {
  white-space: nowrap;
}

.unsaved-dot {
  display: inline-block;
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 50%;
  background-color: #ffc845;
  box-shadow: 0 0 0 2px rgba(255, 200, 69, 0.3);
}

.navbar-toggler {
  color: white;
  background: transparent;
  padding: 0.25rem 0.5rem;
  font-size: 1.1rem;
  line-height: 1;
}

/* Bootstrap adds a focus box-shadow ring that makes the toggler appear to jump on tap */
.navbar-toggler:focus,
.navbar-toggler:active {
  outline: none;
  box-shadow: none;
}

.navbar-right-cluster .navbar-icon {
  /* keep save icon visually aligned with toggler & text */
  margin: 0;
  /* The cluster sits outside .navbar-nav, so navbar-dark's light link colour
     doesn't reach it — set it explicitly. */
  color: white;
}

/* Save icon doubles as a save-state indicator: amber while there are unsaved changes */
.navbar-right-cluster .navbar-icon-unsaved {
  color: #ffc845;
}

@media (max-width: 767.98px) {
  .editor-navbar {
    flex-wrap: wrap;
  }
  .editor-navbar .navbar-brand {
    /* Only the compact right cluster (dot + save + hamburger) needs reserving now */
    max-width: calc(100% - 6rem);
    font-size: 1rem;
    margin-right: 0;
  }
  /* Tighten and align the always-visible right cluster on small screens */
  .navbar-right-cluster {
    gap: 0.25rem;
  }
  .navbar-right-cluster .navbar-icon,
  .navbar-right-cluster .navbar-toggler {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    width: 2.25rem;
    height: 2.25rem;
    padding: 0;
  }
  .editor-navbar .navbar-collapse {
    width: 100%;
    flex-basis: 100%;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    margin-top: 0.25rem;
  }
  .editor-navbar .navbar-collapse .navbar-nav {
    flex-direction: column;
    width: 100%;
    padding: 0.25rem 0;
  }
  .editor-navbar .navbar-collapse ::v-deep(.nav-link) {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    padding: 0.65rem 0.5rem;
    border-radius: 0.25rem;
  }
  /* Keep the leading icons a consistent width so the labels line up down the menu. */
  .editor-navbar .navbar-collapse ::v-deep(.nav-link .svg-inline--fa) {
    flex: 0 0 auto;
  }
  /* Subtle dividers between top-level entries so the menu is easier to scan */
  .editor-navbar .navbar-collapse .navbar-nav > ::v-deep(.nav-item:not(:last-child)),
  .editor-navbar .navbar-collapse .navbar-nav > ::v-deep(.nav-link:not(:last-child)) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
}

/* Between md and xl the inline bar gets tight, so drop the text labels and show
   icons only (hover/title tooltips still convey the label). */
@media (min-width: 768px) and (max-width: 1199.98px) {
  .editor-navbar .navbar-nav ::v-deep(.nav-link) {
    font-size: 0;
  }
  .editor-navbar .navbar-nav ::v-deep(.svg-inline--fa) {
    font-size: 1rem;
  }
}
</style>
