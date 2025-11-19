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
      <span id="synthesis-reactants-label" class="subheading mt-2 pb-2 ml-2">
        <label for="synthesis-reactants-table">Reactants, reagents, inputs</label>
      </span>
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="synthesis-reactants-table"
            v-model="constituents"
            :types-to-query="['samples', 'starting_materials']"
          />
        </div>
      </div>
      <span id="synthesis-products-label" class="subheading mt-2 pb-2 ml-2"
        ><label for="synthesis-products-table">Products</label></span
      >

      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="synthesis-products-table"
            v-model="products"
            :types-to-query="['samples', 'starting_materials']"
          />
        </div>
        <div v-if="calculatedYield !== null" class="ml-2 mt-2">
          <span class="text-muted"
            >Calculated yield: <strong>{{ calculatedYield.toFixed(2) }}%</strong></span
          >
        </div>
      </div>
      <span id="synthesis-procedure-label" class="subheading ml-2"><label>Procedure</label></span>
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
    products: createComputedSetterForItemField("synthesis_products"),
    SynthesisDescription: createComputedSetterForItemField("synthesis_description"),
    calculatedYield() {
      const item = this.$store.state.all_item_data[this.item_id];
      if (!item || !item.synthesis_products || !item.synthesis_constituents) {
        return null;
      }

      const selfProduct = item.synthesis_products.find((p) => p.item?.item_id === this.item_id);

      if (!selfProduct || !selfProduct.quantity) {
        return null;
      }

      const totalInput = item.synthesis_constituents.reduce((sum, c) => sum + (c.quantity || 0), 0);

      if (totalInput === 0) {
        return null;
      }

      return (selfProduct.quantity / totalInput) * 100;
    },
  },
  watch: {
    // Added initialization check to prevent firing on mount - this seemed to trigger an unsaved check when loading the sample for the second time
    constituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
    products: {
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

    var content = this.$refs.contentContainer;

    // Auto-collapsed when initialised empty
    this.isExpanded =
      (this.constituents && this.constituents.length > 0) ||
      (this.products && this.products.length > 0) ||
      (this.SynthesisDescription && this.SynthesisDescription.trim() !== "");

    // If expanded set height to none, otherwise set to 0px
    if (this.isExpanded) {
      this.contentMaxHeight = "none";
      content.style.overflow = "visible";
    } else {
      this.contentMaxHeight = "0px";
    }

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
        content.style.overflow = "visible";
      } else {
        content.style.overflow = "hidden";
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
    addProduct(selectedItem) {
      this.products.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewProduct = null;
      this.selectShown.push(false);
      this.isExpanded = true;
    },
    turnOnRowProductSelect(index) {
      this.selectProductShown[index] = true;
      this.selectedChangedProduct = this.products[index].item;
      this.$nextTick(function () {
        // unfortunately this seems to be the "official" way to focus on the select element:
        this.$refs[`select${index}`].$refs.selectComponent.$refs.search.focus();
      });
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
    swapProduct(selectedItem, index) {
      this.products[index].item = selectedItem;
      this.selectShown[index] = false;
    },
    removeProduct(index) {
      this.products.splice(index, 1);
      this.selectShown.splice(index, 1);
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
}

.content-container {
  overflow: hidden;
  max-height: none;
  transition: max-height 0.4s ease-in-out;
}
</style>
