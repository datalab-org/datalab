<template>
  <div id="synthesis-information">
    <div class="header-container">
      <div class="label-container">
        <label class="mr-2 pb-2">Synthesis Information</label>
        <font-awesome-icon
          :icon="['fas', 'chevron-right']"
          class="collapse-icon"
          :class="{ rotated: !isCollapsed }"
          @click="toggleCollapse"
        />
      </div>
    </div>
    <div :class="['content-container', { collapsed: isCollapsed }]">
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="synthesis-table"
            v-model="constituents"
            :types-to-query="['samples', 'starting_materials']"
          />
        </div>
      </div>
      <span id="synthesis-procedure-label" class="subheading ml-2">Procedure</span>
      <TinyMceInline
        v-model="SynthesisDescription"
        aria-labelledby="synthesis-procedure-label"
      ></TinyMceInline>
    </div>
  </div>
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
import { createComputedSetterForItemField } from "@/field_utils.js";
import CompactConstituentTable from "@/components/CompactConstituentTable.vue";

export default {
  components: {
    TinyMceInline,
    CompactConstituentTable,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      selectedNewConstituent: null,
      selectedChangedConstituent: null,
      selectShown: [],
      // isCollapsed is used to toggle the visibility of the content-container starts as true then will expand when clicked or if it is filled
      isCollapsed: true,
    };
  },
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
  },
  watch: {
    // since constituents is an object, the computed setter never fires and
    // saved status is never updated. So, use a watcher:
    constituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
    SynthesisDescription: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
    },
  },
  mounted() {
    this.selectShown = new Array(this.constituents.length).fill(false);
    // Auto-collapsed when initialised empty
    this.isCollapsed =
      (!this.constituents || this.constituents.length === 0) &&
      (!this.SynthesisDescription || this.SynthesisDescription.trim() === "");
  },
  methods: {
    toggleCollapse() {
      // Switches isCollapsed to the opposite of what it currently is when clicked
      this.isCollapsed = !this.isCollapsed;
      // Explicitly prevent this toggle from marking the item as unsaved
      // by not calling this.$store.commit("setItemSaved", ...)
    },
    addConstituent(selectedItem) {
      this.constituents.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
      this.isCollapsed = false;
    },
    turnOnRowSelect(index) {
      this.selectShown[index] = true;
      this.selectedChangedConstituent = this.constituents[index].item;
      this.$nextTick(function () {
        // unfortunately this seems to be the "official" way to focus on the select element:
        this.$refs[`select${index}`].$refs.selectComponent.$refs.search.focus();
      });
    },
    swapConstituent(selectedItem, index) {
      this.constituents[index].item = selectedItem;
      this.selectShown[index] = false;
    },
    removeConstituent(index) {
      this.constituents.splice(index, 1);
      this.selectShown.splice(index, 1);
    },
  },
};
</script>

<style scoped>
.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
}

.header-container {
  display: flex;
  align-items: center;
}

.label-container {
  display: flex;
  align-items: center;
  /* gap: 8px; */
}

.collapse-icon {
  margin-left: 8px;
  font-size: large;
  display: flex;
  align-items: center;
  vertical-align: middle;
  transition: transform 0.4s ease-in-out;
  cursor: pointer;
}

.rotated {
  transform: rotate(90deg);
}

.content-container {
  max-height: 500px; /* Set a large enough height */
  overflow: hidden;
  transition: max-height 0.4s ease-in-out;
}

.content-container.collapsed {
  max-height: 0;
}
</style>
