<template>
  <div class="container-fluid">
    <div class="row">
      <div class="col-lg-6 col-xl-6 tree-column" style="border-right: 1px solid #ccc">
        <input v-model="searchTerm" class="form-control" type="text" placeholder="Search" />

        <TreeMenu
          v-for="toplevel in remoteTree"
          :key="toplevel.name"
          :entry="toplevel"
          :depth="0"
          :selected-entries="selectedEntries"
          :search-term="searchTerm"
          @set-selected-entry="setSelectedEntry($event, toplevel.name)"
          @append-to-selected-entries="appendToSelectedEntries($event, toplevel.name)"
        />
      </div>

      <div class="col-lg-6 col-xl-6 selected-entries-column">
        <p>Selected files:</p>
        <div
          v-for="selectedEntry in selectedEntries"
          :key="selectedEntry.relative_path"
          class="selected-entry"
        >
          <p class="mb-1 selected-file">
            {{ selectedEntry.name }}
            <span class="selected-size">[{{ prettyBytes(selectedEntry.size) }}]</span>
          </p>
          <button
            type="button"
            class="close"
            aria-label="Close"
            @click="unselectEntry($event, selectedEntry)"
          >
            <span aria-hidden="true">&times;</span>
          </button>
          <p class="mb-1">
            &#8627; <span class="selected-info-name">modified:</span>
            <span class="selected-modified-time">{{
              // convert unix timestamp in seconds to JavaScript localised date string
              timestampToLocaleDate(selectedEntry.time)
            }}</span>
          </p>
          <p class="mb-0">
            &#8627; <span class="selected-info-name">location:</span>
            <span class="selected-toplevel">{{ selectedEntry.toplevel_name }}</span>
            <span class="selected-relpath">{{ selectedEntry.relative_path }}</span>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TreeMenu from "@/components/TreeMenu.vue";

export default {
  components: {
    TreeMenu,
  },
  props: {
    defaultSearchTerm: {
      type: String,
      default: "",
    },
  },
  emits: ["update:selectedEntries"],
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
  watch: {
    selectedEntries: {
      deep: true, // watch elements of the array, not just the array itself. unclear how well this is working.
      handler(val) {
        console.log("emitting selectedEntries");
        this.$emit("update:selectedEntries", val);
      },
    },
  },
  mounted() {
    this.searchTerm = this.defaultSearchTerm;
  },
  methods: {
    prettyBytes(num, precision = 3, addSpace = true) {
      const UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
      if (Math.abs(num) < 1) return num + (addSpace ? " " : "") + UNITS[0];
      const exponent = Math.min(Math.floor(Math.log10(num < 0 ? -num : num) / 3), UNITS.length - 1);
      const n = Number(((num < 0 ? -num : num) / 1000 ** exponent).toPrecision(precision));
      return (num < 0 ? "-" : "") + n + (addSpace ? " " : "") + UNITS[exponent];
    },
    timestampToLocaleDate(timestamp) {
      let date = new Date(Number(timestamp) * 1000);
      return date.toLocaleString("en-GB");
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
    unselectEntry(event, entry) {
      console.log("calling unselectEntry with");
      console.log(event);
      console.log(entry);
      const index = this.selectedEntries.indexOf(entry);
      if (index > -1) {
        this.selectedEntries.splice(index, 1);
      }
    },
  },
};
</script>

<style scoped>
.tree-column {
  /*position:absolute;*/
  height: 70vh;
  overflow-y: auto;
  padding-right: 30px;
  scrollbar-width: thin;
}

.selected-entries-column {
  height: 70vh;
  overflow-y: auto;
  padding-right: 30px;
  scrollbar-width: thin;
}

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
  /*  border: solid 1px teal;
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
