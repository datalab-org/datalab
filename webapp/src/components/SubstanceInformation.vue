<template>
  <div id="substance-information" class="data-block" data-testid="substance-block">
    <div class="datablock-header collapsible" :class="{ expanded: isExpanded }">
      <font-awesome-icon
        :icon="['fas', 'chevron-right']"
        fixed-width
        class="collapse-arrow"
        data-testid="collapse-arrow"
        @click="toggleExpandBlock"
      />
      <label class="block-title">Substance Information</label>
    </div>
    <div
      ref="contentContainer"
      class="content-container"
      :style="{ 'max-height': contentMaxHeight }"
    >
      <div id="substance-information">
        <div class="form-row">
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-chemform">Chemical formula</label>
            <ChemFormulaInput id="substance-chemform" v-model="chemform" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-smiles">SMILES</label>
            <input id="substance-smiles" v-model="smiles" class="form-control" type="text" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-inchi">InChI</label>
            <input id="substance-inchi" v-model="inchi" class="form-control" type="text" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-inchi">InChI Key</label>
            <input id="substance-inchi" v-model="inchi_key" class="form-control" type="text" />
          </div>
          <div class="form-group col-sm-4 col-6 pr-2">
            <label for="substance-mass">Molar mass / molecular weight</label>
            <input id="substance-mass" v-model="molar_mass" class="form-control" type="text" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-row col-sm-4 col-6 pr-2">
            <label for="substance-ghs">GHS codes</label>
            <GHSHazardInformationid v-model="GHS_codes" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { createComputedSetterForItemField } from "@/field_utils.js";
import { GHSHazardInformation } from "@/components/GHSHazardInformation.vue";
import ChemFormulaInput from "@/components/ChemFormulaInput";

export default {
  components: {
    ChemFormulaInput,
    GHSHazardInformation,
  },
  props: {
    item_id: { type: String, required: true },
  },
  data() {
    return {
      // isExpanded is used to toggle the visibility of the content-container starts as false then will expand when clicked or if it is filled
      isExpanded: false,
      contentMaxHeight: "0px", // "none", Start collapsed so 0px, if expanded set to none in mounted
      padding_height: 18,
    };
  },
  computed: {
    chemform: createComputedSetterForItemField("chemform"),
    smiles: createComputedSetterForItemField("smiles"),
    inchi: createComputedSetterForItemField("inchi"),
    inchi_key: createComputedSetterForItemField("inchi_key"),
    GHS_codes: createComputedSetterForItemField("GHS_codes"),
    molar_mass: createComputedSetterForItemField("molar_mass"),
  },
  watch: {
    // Added initialization check to prevent firing on mount - this seemed to trigger an unsaved check when loading the sample for the second time
    constituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
  },
  mounted() {
    var content = this.$refs.contentContainer;

    // Auto-collapsed when initialised empty
    this.isExpanded = true;

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
