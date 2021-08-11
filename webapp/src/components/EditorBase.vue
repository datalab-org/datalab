<template>
  <div id="topScrollPoint"></div>
  <nav
    class="navbar navbar-expand sticky-top navbar-dark py-0 editor-navbar"
    style="background-color: #0b6093"
  >
    <span class="navbar-brand" @click="scrollToID($event, 'topScrollPoint')"
      >Flask-dl&nbsp;&nbsp;|&nbsp;&nbsp;
      {{ sample_id }}
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
            v-for="(blockKind, id) in blockKinds"
            :key="id"
            class="dropdown-item"
            href="#"
            @click="newBlock($event, id)"
          >
            {{ blockKind.description }}
          </a>
        </div>
      </div>
    </div>
    <div class="navbar-nav ml-auto">
      <span v-if="sample_data_loaded && !savedStatus" class="navbar-text unsaved-warning">
        Unsaved changes
      </span>
      <span v-if="sample_data_loaded" class="navbar-text mx-2"
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

  <!-- The sample-specific information will be put in this slot: -->
  <slot></slot>

  <TableOfContents :display_order="sample_data.display_order" :blocks="blocks" />
  <FileList :file_ids="file_ids" :stored_files="stored_files" />

  <div class="container">
    <hr />
  </div>

  <!-- Display the blocks -->
  <div class="container">
    <div v-for="block_id in sample_data.display_order" :key="block_id">
      <component :is="getBlockDisplayType(block_id)" :sample_id="sample_id" :block_id="block_id" />
    </div>
  </div>

  <FileSelectModal :sample_id="sample_id" />
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
import SelectableFileTree from "@/components/SelectableFileTree";

import TableOfContents from "@/components/TableOfContents";
import FileList from "@/components/FileList";
import Modal from "@/components/Modal";
import FileSelectModal from "@/components/FileSelectModal";
import { getSampleData, addABlock, saveSample, deleteFileFromSample } from "@/server_fetch_utils";

import setupUppy from "@/file_upload.js";

import tinymce from "tinymce/tinymce";

import { blockKinds } from "@/resources.js";
import NotImplementedBlock from "@/components/datablocks/NotImplementedBlock.vue";

export default {
  data() {
    return {
      sample_data_loaded: false,
      isMenuDropdownVisible: false,
      selectedRemoteFiles: [],
      isLoadingRemoteTree: false,
      isLoadingRemoteFiles: false,
    };
  },
  props: {
    sample_id: String,
  },
  methods: {
    async newBlock(event, blockKind, index = null) {
      var block_id = await addABlock(this.sample_id, blockKind, index);
      // close the dropdown scroll to the new block :)
      this.isMenuDropdownVisible = false;
      var new_block_el = document.getElementById(block_id);
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
      let sample_id = this.sample_id;
      let new_data = {
        block_id: 7,
        a_new_field: "foo bar",
      };
      console.log(new_data);
      this.$store.commit("updateBlockData", {
        sample_id,
        block_id,
        block_data: new_data,
      });
      // this.$store.state.all_sample_data[sample_id]
    },
    getBlockDisplayType(block_id) {
      var type = this.blocks[block_id].blocktype;
      if (type in blockKinds) {
        return this.blockKinds[type].component;
      } else {
        return NotImplementedBlock;
      }
    },

    saveSample() {
      // trigger the mce save so that they update the store with their content
      console.log("save sample clicked!");
      tinymce.editors.forEach((editor) => editor.save());
      saveSample(this.sample_id);
    },
    deleteFile(event, file_id) {
      console.log(`delete file button clicked!`);
      console.log(event);
      deleteFileFromSample(this.sample_id, file_id);
      return false;
    },
    async getSampleData() {
      await getSampleData(this.sample_id);
      this.sample_data_loaded = true;
    },
  },
  computed: {
    sample_data() {
      // console.log("hello, here is the sample data", this.$store.state.all_sample_data)
      return this.$store.state.all_sample_data[this.sample_id] || {};
    },
    blocks() {
      return this.sample_data.blocks_obj;
    },
    savedStatus() {
      return this.$store.state.saved_status[this.sample_id];
    },
    lastModified() {
      // if (!this.sample_data.last_modified) { return "" }
      const save_date = new Date(this.sample_data.last_modified);
      // const today = new Date()
      // check if today:
      // if (save_date.toDateString() == today.toDateString()) {
      //    return "today"
      // }
      return save_date.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
      });
    },
    files() {
      return this.sample_data.files;
    },
    file_ids() {
      return this.sample_data.file_ObjectIds;
    },
    stored_files() {
      return this.$store.state.files;
    },
  },
  created() {
    this.getSampleData();
  },
  components: {
    TinyMceInline,
    Modal,
    SelectableFileTree,
    FileList,
    TableOfContents,
    FileSelectModal,
  },
  mounted() {
    this.blockKinds = blockKinds; // bind blockKinds as a NON-REACTIVE object to the this context so that it is accessible by the template.

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
    setupUppy(this.sample_id, "#uppy-trigger", this.stored_files);
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this._keyListener);
  },
};
</script>

<style scoped>
.editor-navbar {
  margin-bottom: 1rem;
  z-index: 900;
}

.nav-link {
  cursor: pointer;
}

.nav-link:hover {
  background-color: black;
  color: white;
}

.navbar-icon {
  width: 2.5rem;
  height: 2.5rem;
  /*padding: 0.3rem;*/
}

.unsaved-warning {
  font-weight: 600;
  color: #ffc845;
}

/* file block styles */
#filearea {
  max-height: 14rem;
  padding: 0.9rem 1.25rem;
}

#uppy-trigger {
  scroll-anchor: auto;
  width: 8rem;
}

.delete-file-button {
  padding-right: 0.5rem;
  color: gray;
  cursor: pointer;
}

.navbar-brand {
  cursor: pointer;
}
</style>
