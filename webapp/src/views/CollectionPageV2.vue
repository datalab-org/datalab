<template>
  <div id="topScrollPoint"></div>
  <nav
    class="navbar navbar-expand sticky-top navbar-dark py-0 editor-navbar"
    :style="{ backgroundColor: navbarColor }"
  >
    <span class="navbar-brand clickable" @click="scrollToID($event, 'topScrollPoint')">
      {{ itemTypeEntry?.navbarName || "loading..." }}&nbsp;&nbsp;|&nbsp;&nbsp;
      <FormattedItemName :item_id="collection_id" item-type="collections" />
    </span>
    <div class="navbar-nav">
      <a class="nav-item nav-link" href="/">Home</a>
      <a class="nav-item nav-link" :href="collectionApiUrl" target="_blank">
        <font-awesome-icon icon="code" fixed-width /> View JSON
      </a>
    </div>
    <div class="navbar-nav ml-auto">
      <span v-if="collectionDataLoaded && !savedStatus" class="navbar-text unsaved-warning">
        Unsaved changes
      </span>
      <span v-if="collectionDataLoaded && lastModified" class="navbar-text small mx-2"
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

  <div class="editor-body">
    <div v-if="itemType" class="container-lg">
      <DynamicSchema :item_data="collection_data" @update-item-data="handleCollectionDataUpdate" />
    </div>

    <div class="container-lg">
      <DynamicDataTable
        v-if="tableIsReady"
        :data="children"
        :columns="collectionTableColumns"
        :data-type="'collectionItems'"
        :global-filter-fields="[
          'item_id',
          'name',
          'refcode',
          'blocks',
          'chemform',
          'characteristic_chemical_formula',
        ]"
        :show-buttons="true"
        :collection-id="collection_id"
        @remove-selected-items-from-collection="handleItemsRemovedFromCollection"
      />
    </div>
  </div>
</template>

<script>
import FormattedItemName from "@/components/FormattedItemName";
import DynamicSchema from "@/components/DynamicSchema";
import DynamicDataTable from "@/components/DynamicDataTable";
import { getCollectionData, saveCollection, getCollectionSampleList } from "@/server_fetch_utils";
import { itemTypes } from "@/resources.js";
import { API_URL } from "@/resources.js";
import { formatDistanceToNow } from "date-fns";
import tinymce from "tinymce/tinymce";

export default {
  components: {
    DynamicSchema,
    FormattedItemName,
    DynamicDataTable,
  },
  beforeRouteLeave(to, from, next) {
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
      collection_id: this.$route.params?.id || null,
      collectionDataLoaded: false,
      tableIsReady: false,
      lastModified: null,
      collectionTableColumns: [
        {
          field: "item_id",
          header: "ID",
          body: "FormattedItemName",
          filter: true,
          label: "ID",
        },
        { field: "type", header: "Type", filter: true, label: "Type" },
        { field: "name", header: "Sample name", label: "Sample Name" },
        { field: "chemform", header: "Formula", body: "ChemicalFormula", label: "Formula" },
        { field: "date", header: "Date", label: "Date" },
        { field: "creators", header: "Creators", body: "Creators", label: "Creators" },
        { field: "nblocks", header: "# of blocks", label: "Blocks" },
      ],
    };
  },
  computed: {
    itemType() {
      return this.$store.state.all_collection_data[this.collection_id]?.type || undefined;
    },
    itemTypeEntry() {
      return itemTypes[this.itemType] || undefined;
    },
    navbarColor() {
      return this.itemTypeEntry?.navbarColor || "DarkGrey";
    },
    collection_data() {
      return this.$store.state.all_collection_data[this.collection_id] || {};
    },
    savedStatus() {
      if (!this.collectionDataLoaded) {
        return true;
      }
      return this.$store.state.saved_status_collections[this.collection_id];
    },
    collectionApiUrl() {
      return API_URL + "/collections/" + this.collection_id;
    },
    children() {
      return this.$store.state.all_collection_children[this.collection_id] || [];
    },
  },
  watch: {
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
    this.getCollectionChildren();
    this.interval = setInterval(() => this.setLastModified(), 30000);
  },
  methods: {
    scrollToID(event, id) {
      var element = document.getElementById(id);
      element.scrollIntoView({
        behavior: "smooth",
      });
    },
    handleCollectionDataUpdate(payload) {
      if (payload.item_id && payload.item_data) {
        this.$store.commit("updateCollectionData", payload);
      }
    },
    saveCollectionData() {
      tinymce.editors.forEach((editor) => {
        editor.isDirty() && editor.save();
      });
      saveCollection(this.collection_id);
      this.lastModified = "just now";
      this.savedStatus = true;
    },
    async getCollection() {
      await getCollectionData(this.collection_id);
      this.collectionDataLoaded = true;
      this.setLastModified();
    },
    getCollectionChildren() {
      getCollectionSampleList(this.collection_id).then(() => {
        this.tableIsReady = true;
      });
    },
    handleItemsRemovedFromCollection() {
      this.getCollectionChildren();
    },
    leavePageWarningListener(event) {
      event.preventDefault;
      return (event.returnValue =
        "Unsaved changes present. Would you like to leave without saving?");
    },
    setLastModified() {
      let item_date = this.collection_data.last_modified || this.collection_data.date;
      if (!item_date) {
        this.lastModified = "Unknown";
        return;
      }

      try {
        const save_date = new Date(item_date + "Z");
        if (isNaN(save_date.getTime())) {
          this.lastModified = "Unknown";
        } else {
          this.lastModified = formatDistanceToNow(save_date, { addSuffix: true });
        }
      } catch (error) {
        console.warn("Invalid date format:", item_date, error);
        this.lastModified = "Unknown";
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

::v-deep(.navbar-brand:hover .formatted-item-name) {
  outline: 2px solid rgba(0, 0, 0, 0.3);
}

.unsaved-warning {
  font-weight: 600;
  color: #ffc845;
}
</style>
