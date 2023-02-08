<template>
  <div id="cell-preparation-information">
    <label class="mr-2 pb-2">Cell Construction</label>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="pos-electrode-table"
        >Positive electrode</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable id="pos-electrode-table" v-model="PosElectrodeConstituents" />
        </div>
      </div>
    </div>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="electrolyte-table"
        >Electrolyte</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable id="electrolyte-table" v-model="ElectrolyteConstituents" />
        </div>
      </div>
    </div>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="neg-electrode-table"
        >Negative electrode</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable id="neg-electrode-table" v-model="NegElectrodeConstituents" />
        </div>
      </div>
    </div>

    <div class="form-group ml-5 mt-3">
      <label id="synthesis-procedure-label" class="subheading">Procedure</label>
      <TinyMceInline
        aria-labelledby="synthesis-procedure-label"
        v-model="CellPreparationDescription"
      />
    </div>
  </div>
</template>

<script>
import TinyMceInline from "@/components/TinyMceInline";
// import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { createComputedSetterForItemField } from "@/field_utils.js";

// import ItemSelect from "@/components/ItemSelect.vue";
// import FormattedItemName from "@/components/FormattedItemName.vue";

import CompactConstituentTable from "@/components/CompactConstituentTable";

export default {
  data() {
    return {
      selectedNewConstituent: null,
      selectedChangedConstituent: null,
      selectShown: [],
    };
  },
  props: {
    item_id: String,
  },
  computed: {
    PosElectrodeConstituents: createComputedSetterForItemField("positive_electrode"),
    ElectrolyteConstituents: createComputedSetterForItemField("electrolyte"),
    NegElectrodeConstituents: createComputedSetterForItemField("negative_electrode"),
    CellPreparationDescription: createComputedSetterForItemField("cell_preparation_description"),
  },
  methods: {
    addConstituent(selectedItem) {
      this.PosElectrodeConstituents.push({
        item: selectedItem,
        quantity: null,
        unit: "g",
      });
      this.selectedNewConstituent = null;
      this.selectShown.push(false);
    },
    turnOnRowSelect(index) {
      this.selectShown[index] = true;
      this.selectedChangedConstituent = this.PosElectrodeConstituents[index].item;
      this.$nextTick(function () {
        // unfortunately this seems to be the "official" way to focus on the select element:
        this.$refs[`select${index}`].$refs.selectComponent.$refs.search.focus();
      });
    },
    swapConstituent(selectedItem, index) {
      this.PosElectrodeConstituents[index].item = selectedItem;
      this.selectShown[index] = false;
    },
    removeConstituent(index) {
      this.PosElectrodeConstituents.splice(index, 1);
      this.selectShown.splice(index, 1);
    },
  },
  watch: {
    // since PosElectrodeConstituents is an object, the computed setter never fires and
    // saved status is never updated. So, use a watcher:
    PosElectrodeConstituents: {
      handler() {
        this.$store.commit("setSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
  },
  mounted() {
    this.selectShown = new Array(this.PosElectrodeConstituents.length).fill(false);
  },
  components: {
    TinyMceInline,
    // ChemicalFormula,
    // ItemSelect,
    // FormattedItemName,
    CompactConstituentTable,
  },
};
</script>

<style scoped>
.component-card {
  width: 700px;
}

.first-column {
  position: relative;
}

.swap-constituent-icon {
  cursor: pointer;
  position: absolute;
  font-size: regular;
  color: #bbb;
  float: right;
  transform: translateY(30%);
  transition: transform 0.4s ease;
  width: 1.5rem;
  left: -1.5rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.select-in-row {
  width: 100%;
}

.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
}

table {
  margin-bottom: 0rem;
}

.borderless td,
.borderless th {
  border: none;
}

.empty-search {
  opacity: 0.5;
  font-style: italic;
}
</style>
