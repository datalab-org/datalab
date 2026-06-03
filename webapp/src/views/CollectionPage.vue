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
        <FormattedItemName :item_id="collection_id" item-type="collections" />
      </span>
    </span>

    <!-- Always-visible right-side cluster: status + save + hamburger (hamburger only shows below md) -->
    <div class="navbar-right-cluster order-md-last">
      <span
        v-if="data_loaded && !savedStatus"
        class="navbar-text unsaved-warning d-none d-sm-inline"
      >
        Unsaved changes
      </span>
      <span
        v-if="data_loaded && !savedStatus"
        class="unsaved-dot d-sm-none"
        title="Unsaved changes"
      ></span>
      <span v-if="data_loaded && lastModified" class="navbar-text small d-none d-md-inline"
        ><i>Last saved: {{ lastModified }}</i></span
      >
      <font-awesome-icon
        v-show="isNavCollapsed"
        icon="save"
        fixed-width
        class="nav-link navbar-icon"
        :class="{ 'navbar-icon-unsaved': data_loaded && !savedStatus }"
        title="Save"
        @click="saveCollectionData"
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
        <a class="nav-item nav-link" href="/" title="Home">
          <font-awesome-icon icon="home" fixed-width /> Home
        </a>
        <ExportDropdown :collection-id="collection_id" item-type="collections" />
        <a
          v-if="data_loaded"
          class="nav-item nav-link"
          href="#"
          title="Share this collection"
          @click.prevent="isSharingModalVisible = true"
        >
          <font-awesome-icon icon="share-alt" fixed-width /> Share
        </a>
        <a class="nav-item nav-link" :href="collectionApiUrl" target="_blank" title="View JSON">
          <font-awesome-icon icon="code" fixed-width /> View JSON
        </a>
        <a
          v-if="!isNavCollapsed"
          class="nav-item nav-link d-md-none"
          title="Save"
          @click="saveCollectionData"
        >
          <font-awesome-icon icon="save" fixed-width /> Save
        </a>
        <span v-if="data_loaded && lastModified" class="navbar-text small mx-2 d-md-none"
          ><i>Last saved: {{ lastModified }}</i></span
        >
      </div>
    </div>
  </nav>

  <!-- Item-type header information goes here -->
  <div class="editor-body">
    <CollectionInformation v-if="data_loaded" :collection_id="collection_id" />
    <SharingModal v-model="isSharingModalVisible" :collection-id="collection_id" />
  </div>
</template>

<script>
import { DialogService } from "@/services/DialogService";

import CollectionInformation from "@/components/CollectionInformation";
import LoginDetails from "@/components/LoginDetails";
import SharingModal from "@/components/SharingModal.vue";
import { getCollectionData, saveCollection } from "@/server_fetch_utils";
import FormattedItemName from "@/components/FormattedItemName.vue";
import { itemTypes } from "@/resources.js";
import { API_URL } from "@/resources.js";
import { formatDistanceToNow } from "date-fns";

import ExportDropdown from "@/components/ExportDropdown";

export default {
  components: {
    CollectionInformation,
    LoginDetails,
    SharingModal,
    FormattedItemName,
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
      isSharingModalVisible: false,
      isNavCollapsed: true,
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
    async saveCollectionData() {
      saveCollection(this.collection_id);
      this.lastModified = "just now";
    },
    async getCollection() {
      await getCollectionData(this.collection_id);
      this.data_loaded = true;
      // Mark the collection as saved once child components (e.g. the Tiptap
      // description editor) have mounted and emitted their initial v-model
      // normalisation, which would otherwise flip the status to "unsaved" on
      // first load. Mirrors the same guard in EditPage.getSampleData.
      this.$nextTick(() => {
        this.$store.commit("setSavedCollection", {
          collection_id: this.collection_id,
          isSaved: true,
        });
      });
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

.navbar-brand {
  cursor: pointer;
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
    /* flex-basis 0 (not auto) so the brand's long content doesn't drive line
       wrapping — the cluster stays on this row, and the brand grows into the
       leftover space and truncates instead of bumping the cluster to a 2nd row. */
    flex: 1 1 0;
    min-width: 0;
    font-size: 1rem;
    margin-right: 0;
  }
  /* Keep the cluster at its natural width on the right so the save icon and
     hamburger stay on-screen; the brand truncates into the space to their left. */
  .navbar-right-cluster {
    flex: 0 0 auto;
    gap: 0.25rem;
  }
  /* inline-flex is for the <button> toggler; it must NOT be applied to the save
     <svg>, which renders/clips wrong when treated as a flex container. */
  .navbar-right-cluster .navbar-toggler {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    width: 2.25rem;
    height: 2.25rem;
    padding: 0;
  }
  /* Save icon: plain box sizing (like the desktop .navbar-icon, just a touch bigger) */
  .navbar-right-cluster .navbar-icon {
    flex: 0 0 auto;
    width: 2.1rem;
    height: 2.1rem;
    padding: 0.45rem;
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
