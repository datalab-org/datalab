<template>
  <div id="cell-preparation-information">
    <label class="mr-2 pb-2">Cell Construction</label>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="pos-electrode-table"
        >Positive electrode</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="pos-electrode-table"
            v-model="PosElectrodeConstituents"
            :types-to-query="['starting_materials', 'samples']"
          />
        </div>
      </div>
    </div>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="electrolyte-table"
        >Electrolyte</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="electrolyte-table"
            v-model="ElectrolyteConstituents"
            :types-to-query="['starting_materials', 'samples']"
          />
        </div>
      </div>
    </div>

    <div class="form-group ml-5">
      <label class="subheading cell-component-label mt-4 pb-1" for="neg-electrode-table"
        >Negative electrode</label
      >
      <div class="card component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="neg-electrode-table"
            v-model="NegElectrodeConstituents"
            :types-to-query="['starting_materials', 'samples']"
          />
        </div>
      </div>
    </div>

    <div class="form-group ml-5 mt-3">
      <label id="synthesis-procedure-label" class="subheading">Procedure</label>
      <TiptapInline
        v-model="CellPreparationDescription"
        aria-labelledby="synthesis-procedure-label"
      />
    </div>
  </div>
</template>

<script>
import TiptapInline from "@/components/TiptapInline";
// import ChemicalFormula from "@/components/ChemicalFormula.vue";
import { createComputedSetterForItemField } from "@/field_utils.js";

// import ItemSelect from "@/components/ItemSelect.vue";
// import FormattedItemName from "@/components/FormattedItemName.vue";

import CompactConstituentTable from "@/components/CompactConstituentTable";

export default {
  components: {
    TiptapInline,
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
    };
  },
  computed: {
    PosElectrodeConstituents: createComputedSetterForItemField("positive_electrode"),
    ElectrolyteConstituents: createComputedSetterForItemField("electrolyte"),
    NegElectrodeConstituents: createComputedSetterForItemField("negative_electrode"),
    CellPreparationDescription: createComputedSetterForItemField("cell_preparation_description"),
  },
  watch: {
    // since PosElectrodeConstituents is an object, the computed setter never fires and
    // saved status is never updated. So, use a watcher:
    PosElectrodeConstituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
    ElectrolyteConstituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
    NegElectrodeConstituents: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
    },
  },
};
</script>

<style scoped>
.component-card {
  width: 700px;
}

.subheading {
  color: darkslategrey;
  font-size: small;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 0px;
}
</style>
