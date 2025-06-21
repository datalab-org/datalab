<template>
  <div id="synthesis-information" class="data-block" data-testid="synthesis-block">
    <div class="datablock-header collapsible" :class="{ expanded: isExpanded }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        data-testid="collapse-arrow"
        @click="toggleExpandBlock"
      />
      <label class="block-title">Synthesis Information</label>
    </div>
    <div
      ref="contentContainer"
      class="content-container"
      :style="{ 'max-height': contentMaxHeight }"
    >
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
      // isExpanded is used to toggle the visibility of the content-container starts as false then will expand when clicked or if it is filled
      isExpanded: false,
      contentMaxHeight: "0px", // "none", Start collapsed so 0px, if expanded set to none in mounted
      padding_height: 18,
    };
  },
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
  },
  watch: {
    // Added initialization check to prevent firing on mount - this seemed to trigger an unsaved check when loading the sample for the second time
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
    this.selectShown = new Array((this.constituents || []).length).fill(false);
    // Auto-collapsed when initialised empty
    this.isExpanded =
      (this.constituents && this.constituents.length > 0) ||
      (this.SynthesisDescription && this.SynthesisDescription.trim() !== "");
    // If expanded set height to none, otherwise set to 0px
    if (this.isExpanded) {
      this.contentMaxHeight = "none";
    } else {
      this.contentMaxHeight = "0px";
    }
    var content = this.$refs.contentContainer;
    content.addEventListener("transitionend", () => {
      if (this.isExpanded) {
        this.contentMaxHeight = "none";
      }
    });
  },
  methods: {
    toggleExpandBlock() {
      var content = this.$refs.contentContainer;
      console.log(this.contentMaxHeight);
      if (!this.isExpanded) {
        this.contentMaxHeight = content.scrollHeight + 2 * this.padding_height + "px";
        this.isExpanded = true;
      } else {
        requestAnimationFrame(() => {
          //must be an arrow function so that 'this' is still accessible!
          this.contentMaxHeight = content.scrollHeight + "px";
          requestAnimationFrame(() => {
            this.contentMaxHeight = "0px";
            this.isExpanded = false;
          });
        });
      }
    },
    addConstituent(selectedItem) {
      this.constituents.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
      this.isExpanded = true;
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

/* expanded is on the parent (the header) */
.expanded .collapse-arrow {
  -webkit-transform: rotate(90deg);
  -moz-transform: rotate(90deg);
  transform: rotate(90deg);
}

.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
}

.content-container {
  overflow: hidden;
  max-height: none;
  transition: max-height 0.4s ease-in-out;
}
</style>
