<template>
  <h3>Test of data tree</h3>
  <!-- 	<div style="border: dashed 2px blue; padding:0.5rem">
		<tree-menu
			:nodes="treeData.nodes"
			:depth="0"
			:label="treeData.label"
		>
		</tree-menu>
	</div> -->
  <button class="btn btn-default my-4" @click="getRemoteTree">Get Remote Tree</button>
  <!-- 	<div style="border: dashed 2px grey; padding:0.5rem; height: 10rem; overflow: auto;">
		{{ remoteTree }}
	</div> -->
  <div class="form-row">
    <div class="col-md-4">
      <input class="form-control" type="text" placeholder="Search" v-model="searchTerm" />
    </div>
  </div>

  <TreeMenu
    v-for="toplevel in remoteTree"
    :key="toplevel.name"
    :entry="toplevel"
    :depth="0"
    :selectedEntries="selectedEntries"
    :searchTerm="searchTerm"
    @setSelectedEntry="setSelectedEntry($event, toplevel.name)"
    @appendToSelectedEntries="appendToSelectedEntries($event, toplevel.name)"
  >
  </TreeMenu>

  <p>Selected files:</p>
  <div
    class="selected-entry mr-4"
    v-for="selectedEntry in selectedEntries"
    :key="selectedEntry.relative_path"
  >
    <p class="mb-1 selected-file">
      {{ selectedEntry.name }}
      <span class="selected-size">[{{ selectedEntry.size }}b]</span>
    </p>
    <p class="mb-1 ml-4">
      &#8627; <span class="selected-info-name">modified:</span>
      <span class="selected-modified-time">{{ selectedEntry.time }}</span>
    </p>
    <p class="mb-0 ml-4">
      &#8627; <span class="selected-info-name">location:</span>
      <span class="selected-toplevel">{{ selectedEntry.toplevel_name }}</span>
      <span class="selected-relpath">{{ selectedEntry.relative_path }}</span>
    </p>
  </div>
  <p>_______</p>
</template>

<script>
import TreeMenu from "@/components/TreeMenu.vue";
import { fetchRemoteTree } from "@/server_fetch_utils.js";

export default {
  data() {
    return {
      selectedEntries: [],
      searchTerm: "",
    };
  },
  computed: {
    remoteTree() {
      return this.$store.state.remoteDirectoryTree;
    },
  },
  methods: {
    getRemoteTree() {
      fetchRemoteTree();
    },
    setSelectedEntry(entry, toplevel_name) {
      entry.toplevel_name = toplevel_name;
      this.selectedEntries = [entry];
    },
    appendToSelectedEntries(entry, toplevel_name) {
      const index = this.selectedEntries.indexOf(entry);
      console.log("appending entry:");
      console.log(entry);
      console.log("to list of selected entries:");
      console.log(this.selectedEntries);
      if (index == -1) {
        entry.toplevel_name = toplevel_name;
        this.selectedEntries.push(entry);
      } else this.selectedEntries.splice(index, 1);
    },
  },
  components: {
    TreeMenu,
  },
};
</script>

<style scoped>
.selected-entry {
  padding: 0.75rem 0.75rem;
  margin-bottom: 1rem;
  border: solid 1px lightgrey;
  border-radius: 0.2rem;
}

.selected-info-name {
  font-weight: 600;
  color: #676767;
  font-variant: small-caps;
}
.selected-size {
  font-family: "Andalé Mono", monospace;
  color: #777;
}

.selected-file {
  font-weight: 600;
  /*	border: solid 1px teal;
	padding: 0.1rem 0.25rem;
	border-radius: 0.2rem;*/
  display: inline-block;
}

.selected-modified-time {
  font-weight: 500;
}

.selected-relpath {
  font-family: "Andalé Mono", monospace;
  font-style: italic;
  color: #555;
}

.selected-toplevel {
  font-family: "Andalé Mono", monospace;
  font-weight: 400;
  /*font-style: italic;*/
  color: teal;
  border: solid 1px teal;
  padding: 0.1rem 0.25rem;
  border-radius: 0.2rem;
}
</style>
