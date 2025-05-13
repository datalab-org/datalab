<template>
  <div id="synthesis-information" data-testid="synthesis-block" class="mb-2">
    <div class="d-flex align-items-center mb-2">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow me-2"
        data-testid="collapse-arrow"
        :class="{ 'rotate-90': isExpanded }"
        @click="toggleExpandBlock"
      />
      <label class="form-label mb-0">Synthesis Information</label>
    </div>

    <div
      ref="contentContainer"
      class="content-container overflow-hidden"
      :style="{ 'max-height': contentMaxHeight }"
    >
      <div class="card component-card">
        <div class="card-body pb-0 mb-0 ps-4">
          <CompactConstituentTable
            id="synthesis-table"
            v-model="constituents"
            data-testid="synthesis-table"
            :types-to-query="['samples', 'starting_materials']"
          />
        </div>
      </div>
      <div class="mt-1">
        <span id="synthesis-procedure-label" class="subheading ms-2">Procedure</span>
        <TinyMceInline
          v-model="SynthesisDescription"
          aria-labelledby="synthesis-procedure-label"
        ></TinyMceInline>
      </div>
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
.collapse-arrow {
  font-size: large;
  color: #004175;
  transition: transform 0.4s;
  cursor: pointer;
}

.collapse-arrow:hover {
  color: #7ca7ca;
}

.rotate-90 {
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
  transition: max-height 0.4s ease-in-out;
}
</style>
