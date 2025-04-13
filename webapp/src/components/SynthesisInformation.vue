<template>
  <div id="synthesis-information">
    <label for="synthesis-information" class="mr-2">Synthesis information</label>
    <div class="card">
      <span id="synthesis-reactants-label" class="subheading mt-2 pb-2 ml-2">
        <label for="synthesis-reactants-table">Reactants, reagents, inputs</label>
      </span>
      <div class="component-card">
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
      <div class="component-card">
        <div class="card-body pt-2 pb-0 mb-0 pl-5">
          <CompactConstituentTable
            id="synthesis-products-table"
            v-model="products"
            :types-to-query="['samples', 'starting_materials']"
          />
        </div>
      </div>
      <span id="synthesis-procedure-label" class="subheading mt-2 pb-2 ml-2"
        ><label>Procedure</label></span
      >
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
  computed: {
    constituents: createComputedSetterForItemField("synthesis_constituents"),
    products: createComputedSetterForItemField("synthesis_products"),
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
    products: {
      handler() {
        this.$store.commit("setItemSaved", { item_id: this.item_id, isSaved: false });
      },
      deep: true,
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
}
</style>
