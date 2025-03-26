<template>
  <div :id="synthesis - information" class="data-block">
    <div class="datablock-header collapsible">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        :class="{ rotated: !isCollapsed }"
        @click="toggleCollapse"
      />
      <label class="block-title">Synthesis Information</label>
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
      contentMaxHeight: "none",
      padding_height: 18,
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
.data-block {
  padding-bottom: 18px;
}

.datablock-header {
  display: flex;
  align-items: center;
  font-size: large;
  height: 35px;
  margin: auto;
}

.collapsible {
  /* background-color: #eee; */
  color: white;
  /* color: #444; */
  /*cursor: pointer;*/
  /*padding: 6px;*/
  width: 100%;
  /* border: 1px solid #ccc; */
  text-align: left;
  outline: none;
  /* border-radius: 3px; */
}

.block-title {
  display: flex;
  align-items: center;
  margin-left: 1em;
  font-size: large;
  font-weight: 500;
  margin: auto 0;
}

.collapse-arrow {
  font-size: large;
  margin-left: 10px;
  margin-right: 10px;
  color: #004175;
  transition: all 0.4s;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
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
